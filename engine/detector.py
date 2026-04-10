"""
ملف الكشف - Object Detector (YOLO26)
======================================
يُدير الاستدلال (inference) باستخدام نموذج YOLO26 ONNX.

YOLO26 هو نموذج end-to-end بدون NMS:
- المخرجات: (1, 300, 6) = [x1, y1, x2, y2, confidence, class_id]
- لا يحتاج NMS — النموذج يُرجع نتائج نهائية مباشرة
- الإحداثيات في مساحة النموذج (640×640) — تحتاج إعادة تحجيم

المسؤوليات:
- تحميل نموذج ONNX مرة واحدة
- تشغيل الاستدلال على الإطارات المُعالجة
- تصفية الكشوفات بعتبة الثقة
- تحويل الإحداثيات من مساحة النموذج إلى الإطار الأصلي
- إرجاع الكشوفات بتنسيق supervision

المرتبط به:
- يُستورد من: ai_thread.py
- يستقبل من: preprocessor.py (إطارات مُعالجة مسبقاً + معلومات التحجيم)
- يُرسل إلى: tracker.py (كشوفات مُنقاة)
"""

import logging
import os
from typing import Optional, Tuple

import numpy as np
import onnxruntime as ort
import supervision as sv

from core.config import MODEL_PATH, CONFIDENCE_THRESHOLD, MODEL_INPUT_SIZE

logger = logging.getLogger(__name__)


class ObjectDetector:
    """
    كاشف الكائنات باستخدام YOLO26 ONNX
    ======================================
    يُغلف ONNX Runtime ويُوفر واجهة بسيطة للكشف.

    YOLO26 يختلف عن الإصدارات القديمة:
    - End-to-end: المخرجات نهائية بدون NMS
    - الشكل: (1, max_detections, 6)
    - كل كشف: [x1, y1, x2, y2, confidence, class_id]
    """

    def __init__(
        self,
        model_path: str = MODEL_PATH,
        confidence_threshold: float = CONFIDENCE_THRESHOLD
    ):
        """
        تهيئة الكاشف

        المُعاملات (Args):
            model_path: مسار ملف نموذج ONNX
            confidence_threshold: الحد الأدنى للثقة (0.0 - 1.0)
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold

        # التحقق من وجود ملف النموذج قبل التحميل
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"ملف النموذج غير موجود: {self.model_path}")

        # كائن جلسة ONNX
        self.session: Optional[ort.InferenceSession] = None
        self.input_name: Optional[str] = None

        # معلومات المخرجات (تُكتشف تلقائياً)
        self.output_format: str = "unknown"  # "yolo26" أو "yolov8" أو "yolov5"
        self.max_detections: int = 300
        self.num_classes: int = 80

        # تحميل النموذج
        self._load_model()

    def _load_model(self) -> None:
        """
        تحميل نموذج ONNX
        ==================
        يُنشئ جلسة ONNX Runtime مع دعم CUDA و CPU.
        يكتشف تنسيق المخرجات تلقائياً.
        """
        try:
            logger.info(f"جاري تحميل نموذج ONNX من: {self.model_path}")

            # التحقق من وجود الملف
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")

            # تحديد مزودي التنفيذ - CUDA أولاً ثم CPU
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']

            # إنشاء الجلسة
            self.session = ort.InferenceSession(
                self.model_path,
                providers=providers
            )

            # الحصول على اسم مدخل النموذج
            self.input_name = self.session.get_inputs()[0].name

            # اكتشاف تنسيق المخرجات
            self._detect_output_format()

            # التحقق من المزود المستخدم فعلياً
            actual_provider = self.session.get_providers()[0]
            logger.info(
                f"تم تحميل النموذج بنجاح — "
                f"المزود: {actual_provider}, "
                f"التنسيق: {self.output_format}, "
                f"أقصى كشوفات: {self.max_detections}"
            )

        except Exception as e:
            logger.error(f"فشل تحميل النموذج: {e}")
            raise

    def _detect_output_format(self) -> None:
        """
        اكتشاف تنسيق مخرجات النموذج تلقائياً
        =========================================
        يُنشئ إدخال وهمي ويفحص شكل المخرجات.

        التنسيقات المدعومة:
        - YOLO26: (1, 300, 6)  → [x1, y1, x2, y2, conf, class_id]
        - YOLOv8: (1, 84, 8400) → transposed, no obj_conf
        - YOLOv5: (1, 25200, 85) → [cx, cy, w, h, obj_conf, 80_classes]
        """
        # إنشاء إدخال وهمي للاختبار
        dummy_input = np.zeros((1, 3, *MODEL_INPUT_SIZE), dtype=np.float32)
        outputs = self.session.run(None, {self.input_name: dummy_input})
        output_shape = outputs[0].shape

        logger.info(f"شكل مخرجات النموذج: {output_shape}")

        if len(output_shape) == 3:
            batch, dim1, dim2 = output_shape

            if dim2 == 6:
                # YOLO26: (1, 300, 6) — end-to-end, NMS-free
                self.output_format = "yolo26"
                self.max_detections = dim1
                logger.info(f"تم اكتشاف تنسيق YOLO26 — {self.max_detections} كشف أقصى")

            elif dim1 < dim2 and dim1 <= 84 + 32:
                # YOLOv8: (1, 84, 8400) — transposed
                self.output_format = "yolov8"
                self.num_classes = dim1 - 4
                logger.info(f"تم اكتشاف تنسيق YOLOv8 — {self.num_classes} فئة")

            elif dim2 <= 84 + 32 + 1:
                # YOLOv5: (1, 25200, 85) — [cx,cy,w,h,obj_conf,classes]
                self.output_format = "yolov5"
                self.num_classes = dim2 - 5
                logger.info(f"تم اكتشاف تنسيق YOLOv5 — {self.num_classes} فئة")

            else:
                logger.warning(f"تنسيق غير معروف: {output_shape}, سيُعامل كـ YOLO26")
                self.output_format = "yolo26"
                self.max_detections = dim1

        else:
            logger.warning(f"شكل مخرجات غير متوقع: {output_shape}")
            self.output_format = "yolo26"

    def detect(
        self,
        preprocessed_frame: np.ndarray,
        scale_info: Optional[dict] = None
    ) -> sv.Detections:
        """
        كشف الكائنات في إطار مُعالج مسبقاً

        المُعاملات (Args):
            preprocessed_frame: إطار بشكل (1, 3, H, W) من preprocessor
            scale_info: معلومات التحجيم من preprocessor لتحويل الإحداثيات
                        {"scale": float, "pad_x": int, "pad_y": int,
                         "orig_w": int, "orig_h": int}

        المرجع (Returns):
            كائن supervision.Detections بإحداثيات الإطار الأصلي
        """
        if self.session is None:
            logger.error("النموذج غير محمل")
            return sv.Detections.empty()

        # تشغيل الاستدلال
        outputs = self.session.run(None, {self.input_name: preprocessed_frame})
        raw_output = outputs[0]

        # تحليل المخرجات حسب التنسيق
        if self.output_format == "yolo26":
            detections = self._parse_yolo26(raw_output)
        elif self.output_format == "yolov8":
            detections = self._parse_yolov8(raw_output)
        elif self.output_format == "yolov5":
            detections = self._parse_yolov5(raw_output)
        else:
            detections = self._parse_yolo26(raw_output)

        # إعادة تحجيم الإحداثيات للحجم الأصلي
        if scale_info is not None and len(detections) > 0:
            detections = self._rescale_detections(detections, scale_info)

        return detections

    def _parse_yolo26(self, raw_output: np.ndarray) -> sv.Detections:
        """
        تحليل مخرجات YOLO26

        الشكل: (1, max_detections, 6)
        كل صف: [cx, cy, w, h, confidence, class_id]

        لا يحتاج NMS — النتائج نهائية من النموذج.
        """
        output = raw_output[0]  # (300, 6)

        # تصفية بعتبة الثقة
        confidences = output[:, 4]
        mask = confidences > self.confidence_threshold
        filtered = output[mask]

        if len(filtered) == 0:
            return sv.Detections.empty()

        # استخراج المكونات - YOLO26 يُخرج (x1, y1, x2, y2) مباشرة
        x1 = filtered[:, 0]
        y1 = filtered[:, 1]
        x2 = filtered[:, 2]
        y2 = filtered[:, 3]
        confs = filtered[:, 4]
        class_ids = filtered[:, 5].astype(int)

        boxes = np.stack([x1, y1, x2, y2], axis=1)

        return sv.Detections(
            xyxy=boxes,
            confidence=confs,
            class_id=class_ids
        )

    def _parse_yolov8(self, raw_output: np.ndarray) -> sv.Detections:
        """
        تحليل مخرجات YOLOv8 (احتياطي)

        الشكل: (1, 4+num_classes, num_boxes)
        يحتاج transpose + NMS
        """
        import cv2

        output = raw_output[0].T  # (num_boxes, 4+num_classes)

        # استخراج الصناديق والفئات
        boxes_cxcywh = output[:, :4]
        class_probs = output[:, 4:]

        # أفضل فئة لكل صندوق
        class_ids = np.argmax(class_probs, axis=1)
        confidences = class_probs[np.arange(len(class_ids)), class_ids]

        # تصفية بعتبة الثقة
        mask = confidences > self.confidence_threshold
        if not np.any(mask):
            return sv.Detections.empty()

        boxes_filtered = boxes_cxcywh[mask]
        confs_filtered = confidences[mask]
        ids_filtered = class_ids[mask]

        # تحويل cx,cy,w,h → x1,y1,x2,y2
        x1 = boxes_filtered[:, 0] - boxes_filtered[:, 2] / 2
        y1 = boxes_filtered[:, 1] - boxes_filtered[:, 3] / 2
        x2 = boxes_filtered[:, 0] + boxes_filtered[:, 2] / 2
        y2 = boxes_filtered[:, 1] + boxes_filtered[:, 3] / 2
        xyxy = np.stack([x1, y1, x2, y2], axis=1)

        # تحويل cx,cy,w,h → x,y,w,h لـ NMS
        boxes_xywh = boxes_filtered.copy()
        boxes_xywh[:, 0] = boxes_filtered[:, 0] - boxes_filtered[:, 2] / 2  # x = cx - w/2
        boxes_xywh[:, 1] = boxes_filtered[:, 1] - boxes_filtered[:, 3] / 2  # y = cy - h/2

        # تطبيق NMS
        nms_result = cv2.dnn.NMSBoxes(
            boxes_xywh.tolist(),
            confs_filtered.tolist(),
            self.confidence_threshold,  # score_threshold
            0.45  # nms_threshold (IoU)
        )

        if len(nms_result) == 0:
            return sv.Detections.empty()

        indices = nms_result.flatten()

        return sv.Detections(
            xyxy=xyxy[indices],
            confidence=confs_filtered[indices],
            class_id=ids_filtered[indices]
        )

    def _parse_yolov5(self, raw_output: np.ndarray) -> sv.Detections:
        """
        تحليل مخرجات YOLOv5 (احتياطي)

        الشكل: (1, num_boxes, 5+num_classes)
        كل صف: [cx, cy, w, h, obj_conf, class1_prob, class2_prob, ...]
        يحتاج NMS
        """
        import cv2

        output = raw_output[0]  # (num_boxes, 85)

        # ثقة الكائن
        obj_conf = output[:, 4]
        mask = obj_conf > self.confidence_threshold
        if not np.any(mask):
            return sv.Detections.empty()

        filtered = output[mask]

        # أفضل فئة
        class_probs = filtered[:, 5:]
        class_ids = np.argmax(class_probs, axis=1)
        class_confs = class_probs[np.arange(len(class_ids)), class_ids]
        confidences = filtered[:, 4] * class_confs

        # تصفية ثانية
        conf_mask = confidences > self.confidence_threshold
        if not np.any(conf_mask):
            return sv.Detections.empty()

        boxes_cxcywh = filtered[conf_mask, :4]
        confs = confidences[conf_mask]
        ids = class_ids[conf_mask]

        # تحويل cx,cy,w,h → x1,y1,x2,y2
        x1 = boxes_cxcywh[:, 0] - boxes_cxcywh[:, 2] / 2
        y1 = boxes_cxcywh[:, 1] - boxes_cxcywh[:, 3] / 2
        x2 = boxes_cxcywh[:, 0] + boxes_cxcywh[:, 2] / 2
        y2 = boxes_cxcywh[:, 1] + boxes_cxcywh[:, 3] / 2
        xyxy = np.stack([x1, y1, x2, y2], axis=1)

        # تحويل cx,cy,w,h → x,y,w,h لـ NMS
        boxes_xywh = boxes_cxcywh.copy()
        boxes_xywh[:, 0] = boxes_cxcywh[:, 0] - boxes_cxcywh[:, 2] / 2  # x = cx - w/2
        boxes_xywh[:, 1] = boxes_cxcywh[:, 1] - boxes_cxcywh[:, 3] / 2  # y = cy - h/2

        # تطبيق NMS (ترتيب المعاملات الصحيح)
        nms_result = cv2.dnn.NMSBoxes(
            boxes_xywh.tolist(),
            confs.tolist(),
            self.confidence_threshold,  # score_threshold أولاً
            0.45  # nms_threshold (IoU) ثانياً
        )

        if len(nms_result) == 0:
            return sv.Detections.empty()

        indices = nms_result.flatten()

        return sv.Detections(
            xyxy=xyxy[indices],
            confidence=confs[indices],
            class_id=ids[indices]
        )

    def _rescale_detections(
        self,
        detections: sv.Detections,
        scale_info: dict
    ) -> sv.Detections:
        """
        تحويل إحداثيات الكشف من مساحة النموذج إلى الإطار الأصلي

        المُعاملات (Args):
            detections: الكشوفات بإحداثيات النموذج
            scale_info: {"scale": float, "pad_x": int, "pad_y": int,
                         "orig_w": int, "orig_h": int}

        المرجع (Returns):
            كشوفات بإحداثيات الإطار الأصلي
        """
        scale = scale_info["scale"]
        pad_x = scale_info["pad_x"]
        pad_y = scale_info["pad_y"]
        orig_w = scale_info["orig_w"]
        orig_h = scale_info["orig_h"]

        # إزالة الحشو ثم إعادة التحجيم
        xyxy = detections.xyxy.copy()
        xyxy[:, [0, 2]] = (xyxy[:, [0, 2]] - pad_x) / scale
        xyxy[:, [1, 3]] = (xyxy[:, [1, 3]] - pad_y) / scale

        # قص الإحداثيات لحدود الإطار
        xyxy[:, [0, 2]] = np.clip(xyxy[:, [0, 2]], 0, orig_w)
        xyxy[:, [1, 3]] = np.clip(xyxy[:, [1, 3]], 0, orig_h)

        detections.xyxy = xyxy
        return detections

"""
ملف خيط الذكاء الاصطناعي - AI Engine Thread
=============================================
الخيط الرئيسي لمعالجة الذكاء الاصطناعي.
يعمل بشكل منفصل عن واجهة المستخدم لمنع التجميد.

المسؤوليات:
- سحب الإطارات من الطابور
- تشغيل المعالجة المسبقة والكشف والتتبع
- تحديث خط العد والعدادات
- رسم الصناديق والخط على الإطار
- إرسال الإطارات والإحصائيات لواجهة المستخدم عبر Signals

المرتبط به:
- يُستورد من: main_window.py
- يستقبل من: video/ingestor.py (عبر raw_frame_queue)
- يُرسل إلى: ui/main_window.py (عبر Signals)
- يستخدم: engine/preprocessor.py, engine/detector.py, engine/tracker.py
"""

import queue
import logging
import threading
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
import supervision as sv

from PySide6.QtCore import QThread, Signal, Slot

from core.config import (
    VEHICLE_CLASSES, VEHICLE_CLASS_NAMES_AR,
    LINE_WIDTH
)
from engine.preprocessor import FramePreprocessor
from engine.detector import ObjectDetector
from engine.tracker import VehicleTracker, LineZoneManager

logger = logging.getLogger(__name__)


class AIEngineThread(QThread):
    """
    خيط معالجة الذكاء الاصطناعي
    =============================
    ينفصل تماماً عن خيط واجهة المستخدم.
    يتواصل فقط عبر Signals/Slots الآمنة.
    """

    # ==========================================================================
    # الإشارات - Signals
    # ==========================================================================

    # إطار مُعالج وجاهز للعرض (numpy array بصيغة BGR)
    frame_ready = Signal(object)

    # إحصائيات محدثة (قاموس بالأعداد)
    stats_ready = Signal(object)

    # رسالة خطأ
    error_occurred = Signal(str)

    def __init__(
        self,
        raw_frame_queue: queue.Queue,
        vehicle_classes: Dict[int, str] = VEHICLE_CLASSES
    ):
        """
        تهيئة خيط الذكاء الاصطناعي

        المُعاملات (Args):
            raw_frame_queue: الطابور المشترك مع VideoIngestor
            vehicle_classes: قاموس فئات المركبات
        """
        super().__init__()

        # حفظ المعاملات
        self.raw_frame_queue = raw_frame_queue
        self.vehicle_classes = vehicle_classes

        # ======================================================================
        # تهيئة المكونات
        # ======================================================================

        # مُعالج الإطارات المسبق
        self.preprocessor = FramePreprocessor()

        # كاشف الكائنات
        self.detector = ObjectDetector()

        # متتبع المركبات
        self.tracker = VehicleTracker()

        # مدير خط العد
        self.line_zone_manager = LineZoneManager()

        # ======================================================================
        # أدوات الرسم من supervision
        # ======================================================================

        # رسم الصناديق
        self.box_annotator = sv.BoxAnnotator(thickness=1)

        self.label_annotator = sv.LabelAnnotator(
            text_position=sv.Position.TOP_LEFT,
            text_scale=0.4,
            text_thickness=1,
            border_radius=3
        )

        self.line_annotator = sv.LineZoneAnnotator(thickness=2)

        # ======================================================================
        # علم التحكم — محمي بقفل للأمان
        # ======================================================================
        self._is_running = False
        self._lock = threading.Lock()

    def run(self) -> None:
        """
        حلقة المعالجة الرئيسية
        ========================
        تُشغل تلقائياً عند استدعاء start().
        تستمر في العمل حتى استدعاء stop_processing().
        """
        with self._lock:
            self._is_running = True
        logger.info("تم بدء خيط الذكاء الاصطناعي")

        try:
            while True:
                # فحص علم التوقف بأمان
                with self._lock:
                    if not self._is_running:
                        break

                # سحب إطار من الطابور
                try:
                    frame = self.raw_frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if frame is None:
                    continue

                # معالجة الإطار
                try:
                    annotated_frame, stats = self._process_frame(frame)
                    self.frame_ready.emit(annotated_frame)
                    self.stats_ready.emit(stats)
                except Exception as e:
                    logger.error(f"خطأ في معالجة الإطار: {e}")
                    self.error_occurred.emit(f"خطأ في معالجة الإطار: {e}")
                    continue

        except Exception as e:
            self.error_occurred.emit(f"خطأ في خيط الذكاء الاصطناعي: {e}")

        finally:
            with self._lock:
                self._is_running = False
            logger.info("تم إيقاف خيط الذكاء الاصطناعي")

    def _process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        معالجة إطار واحد بالكامل

        المُعاملات (Args):
            frame: إطار خام من الفيديو (BGR)

        المرجع (Returns):
            Tuple من (الإطار المُرسوم, الإحصائيات)
        """
        # الخطوة 1: معالجة مسبقة (مع letterbox)
        input_tensor, scale_info = self.preprocessor.preprocess(frame)

        # الخطوة 2: كشف الكائنات (مع إعادة تحجيم الإحداثيات)
        detections = self.detector.detect(input_tensor, scale_info)

        # الخطوة 3: تتبع المركبات
        tracked_detections = self.tracker.update(detections)

        # الخطوة 4: تصفية المركبات فقط
        vehicle_detections = self.tracker.filter_vehicles(tracked_detections)

        # الخطوة 5: تحديث خط العد
        if self.line_zone_manager.line_zone is not None:
            self.line_zone_manager.update(vehicle_detections)

        # الخطوة 6: رسم على الإطار
        annotated_frame = self._annotate_frame(
            frame, tracked_detections, vehicle_detections
        )

        # الخطوة 7: تجميع الإحصائيات
        stats = self._compile_stats(vehicle_detections)

        return annotated_frame, stats

    def _annotate_frame(
        self,
        frame: np.ndarray,
        all_detections: sv.Detections,
        vehicle_detections: sv.Detections
    ) -> np.ndarray:
        """
        رسم الصناديق والخط على الإطار

        المُعاملات (Args):
            frame: الإطار الأصلي
            all_detections: جميع الكشوفات
            vehicle_detections: كشوفات المركبات فقط

        المرجع (Returns):
            إطار مُرسوم عليه الصناديق والخط
        """
        annotated = frame.copy()

        # رسم خط العد إذا موجود
        if self.line_zone_manager.line_zone is not None:
            annotated = self.line_annotator.annotate(
                frame=annotated,
                line_counter=self.line_zone_manager.line_zone
            )

        # رسم صناديق المركبات
        if len(vehicle_detections) > 0:
            labels = self.tracker.get_labels(vehicle_detections)

            annotated = self.box_annotator.annotate(
                scene=annotated,
                detections=vehicle_detections
            )

            annotated = self.label_annotator.annotate(
                scene=annotated,
                detections=vehicle_detections,
                labels=labels
            )

        return annotated

    def _compile_stats(self, detections: sv.Detections = None) -> Dict:
        """
        تجميع الإحصائيات الحالية

        يعرض:
        - العدد التراكمي من خط العد (in/out/total)
        - عدد المركبات المرئية حالياً حسب النوع

        المُعاملات (Args):
            detections: الكشوفات الحالية

        المرجع (Returns):
            قاموس يحتوي على جميع الأعداد
        """
        stats = {}

        # أعداد خط العد (تراكمية)
        line_counts = self.line_zone_manager.get_counts()
        stats['in_count'] = line_counts['in_count']
        stats['out_count'] = line_counts['out_count']
        stats['total'] = line_counts['in_count'] + line_counts['out_count']

        # تهيئة أعداد الفئات
        for class_id, class_name in self.vehicle_classes.items():
            stats[class_name] = 0

        # أعداد المركبات المرئية حالياً حسب الفئة
        if detections is not None and len(detections) > 0:
            unique_classes, counts = np.unique(
                detections.class_id, return_counts=True
            )
            for class_id, count in zip(unique_classes, counts):
                class_name = self.vehicle_classes.get(int(class_id), None)
                if class_name:
                    stats[class_name] = int(count)

        return stats

    @Slot(object)
    def set_line_coordinates(
        self,
        coords: Optional[Tuple[Tuple[int, int], Tuple[int, int]]]
    ) -> None:
        """
        Slot لاستقبال إحداثيات الخط من واجهة المستخدم

        المُعاملات (Args):
            coords: نقطتي الخط أو None للمسح
        """
        if coords is None:
            self.line_zone_manager.clear_line()
        else:
            point_a, point_b = coords
            self.line_zone_manager.set_line(point_a, point_b)

    def reset_counts(self) -> None:
        """
        إعادة تعيين العدادات
        ======================
        يُعيد إنشاء LineZone بنفس الإحداثيات لتصفير العدادات.
        """
        self.line_zone_manager.reset_counts()

    def stop_processing(self) -> None:
        """
        إشارة للتوقف عن المعالجة (thread-safe)
        ==========================================
        """
        with self._lock:
            self._is_running = False

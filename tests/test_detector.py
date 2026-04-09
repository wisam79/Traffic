"""
اختبارات الكاشف - Detector Tests
====================================
يختبر ObjectDetector مع:
- تحميل النموذج
- اكتشاف تنسيق YOLO26 تلقائياً
- تحليل مخرجات YOLO26 (1, 300, 6)
- تصفية الثقة
- إعادة تحجيم الإحداثيات
- تحليل YOLOv8/v5 (احتياطي)
- حالات الحافة
"""

import os
import numpy as np
import pytest
import supervision as sv

from engine.detector import ObjectDetector
from core.config import MODEL_PATH, CONFIDENCE_THRESHOLD


# ==============================================================================
# اختبارات تحميل النموذج
# ==============================================================================

class TestModelLoading:
    """اختبارات تحميل النموذج"""

    @pytest.mark.integration
    def test_model_loads_successfully(self):
        """التحقق من تحميل النموذج بدون خطأ"""
        detector = ObjectDetector()
        assert detector.session is not None

    @pytest.mark.integration
    def test_model_detects_yolo26_format(self):
        """التحقق من اكتشاف تنسيق YOLO26"""
        detector = ObjectDetector()
        assert detector.output_format == "yolo26"

    @pytest.mark.integration
    def test_model_max_detections_300(self):
        """التحقق من أقصى كشوفات = 300"""
        detector = ObjectDetector()
        assert detector.max_detections == 300

    @pytest.mark.integration
    def test_model_input_name_exists(self):
        """التحقق من وجود اسم المدخل"""
        detector = ObjectDetector()
        assert detector.input_name is not None
        assert isinstance(detector.input_name, str)

    def test_missing_model_raises(self):
        """خطأ عند ملف نموذج غير موجود"""
        with pytest.raises(FileNotFoundError):
            ObjectDetector(model_path="nonexistent_model.onnx")


# ==============================================================================
# اختبارات تحليل YOLO26
# ==============================================================================

class TestYOLO26Parsing:
    """اختبارات تحليل مخرجات YOLO26"""

    def test_parse_yolo26_basic(self):
        """تحليل أساسي لمخرجات YOLO26"""
        detector = ObjectDetector.__new__(ObjectDetector)
        detector.confidence_threshold = 0.5

        raw = np.zeros((1, 300, 6), dtype=np.float32)
        raw[0, 0] = [320, 240, 100, 80, 0.9, 2]  # سيارة
        raw[0, 1] = [100, 100, 50, 40, 0.8, 7]    # شاحنة

        result = detector._parse_yolo26(raw)

        assert len(result) == 2
        assert result.confidence[0] == pytest.approx(0.9)
        assert result.confidence[1] == pytest.approx(0.8)
        assert result.class_id[0] == 2
        assert result.class_id[1] == 7

    def test_parse_yolo26_confidence_filter(self):
        """تصفية الثقة — فقط أعلى من العتبة"""
        detector = ObjectDetector.__new__(ObjectDetector)
        detector.confidence_threshold = 0.5

        raw = np.zeros((1, 300, 6), dtype=np.float32)
        raw[0, 0] = [320, 240, 100, 80, 0.9, 2]   # فوق العتبة ✅
        raw[0, 1] = [100, 100, 50, 40, 0.3, 7]     # تحت العتبة ❌
        raw[0, 2] = [200, 200, 60, 50, 0.51, 3]    # فوق العتبة بالكاد ✅

        result = detector._parse_yolo26(raw)
        assert len(result) == 2

    def test_parse_yolo26_empty_output(self):
        """مخرجات فارغة (كل الثقة = 0)"""
        detector = ObjectDetector.__new__(ObjectDetector)
        detector.confidence_threshold = 0.5

        raw = np.zeros((1, 300, 6), dtype=np.float32)
        result = detector._parse_yolo26(raw)

        assert len(result) == 0

    def test_parse_yolo26_coordinates(self):
        """التحقق من أن الإحداثيات تمرّر كما هي (x1, y1, x2, y2)"""
        detector = ObjectDetector.__new__(ObjectDetector)
        detector.confidence_threshold = 0.1

        raw = np.zeros((1, 300, 6), dtype=np.float32)
        # x1=150, y1=110, x2=250, y2=190, conf=0.9, class_id=2
        raw[0, 0] = [150, 110, 250, 190, 0.9, 2]

        result = detector._parse_yolo26(raw)

        assert result.xyxy[0, 0] == pytest.approx(150.0)  # x1
        assert result.xyxy[0, 1] == pytest.approx(110.0)  # y1
        assert result.xyxy[0, 2] == pytest.approx(250.0)  # x2
        assert result.xyxy[0, 3] == pytest.approx(190.0)  # y2


# ==============================================================================
# اختبارات إعادة تحجيم الإحداثيات
# ==============================================================================

class TestCoordinateRescaling:
    """اختبارات إعادة تحجيم الإحداثيات"""

    def test_rescale_identity(self, scale_info_identity):
        """بدون تحجيم (scale=1, padding=0)"""
        detector = ObjectDetector.__new__(ObjectDetector)

        detections = sv.Detections(
            xyxy=np.array([[100, 100, 200, 200]], dtype=np.float32),
            confidence=np.array([0.9]),
            class_id=np.array([2])
        )

        result = detector._rescale_detections(detections, scale_info_identity)

        assert result.xyxy[0, 0] == pytest.approx(100.0)
        assert result.xyxy[0, 1] == pytest.approx(100.0)
        assert result.xyxy[0, 2] == pytest.approx(200.0)
        assert result.xyxy[0, 3] == pytest.approx(200.0)

    def test_rescale_1080p(self, scale_info_1080p):
        """تحجيم من 640×640 إلى 1920×1080"""
        detector = ObjectDetector.__new__(ObjectDetector)

        # نقطة في منتصف النموذج (320, 320)
        detections = sv.Detections(
            xyxy=np.array([[300, 300, 340, 340]], dtype=np.float32),
            confidence=np.array([0.9]),
            class_id=np.array([2])
        )

        result = detector._rescale_detections(detections, scale_info_1080p)

        # الإحداثيات يجب أن تكون أكبر في الإطار الأصلي
        assert result.xyxy[0, 0] > 300  # x1 أكبر
        assert result.xyxy[0, 2] > 340  # x2 أكبر

    def test_rescale_clipping(self, scale_info_identity):
        """قص الإحداثيات عند حدود الإطار"""
        detector = ObjectDetector.__new__(ObjectDetector)

        # إحداثيات خارج الحدود
        detections = sv.Detections(
            xyxy=np.array([[-50, -30, 700, 700]], dtype=np.float32),
            confidence=np.array([0.9]),
            class_id=np.array([2])
        )

        result = detector._rescale_detections(detections, scale_info_identity)

        assert result.xyxy[0, 0] >= 0     # x1 لا يكون سالب
        assert result.xyxy[0, 1] >= 0     # y1 لا يكون سالب
        assert result.xyxy[0, 2] <= 640   # x2 لا يتجاوز العرض
        assert result.xyxy[0, 3] <= 640   # y2 لا يتجاوز الارتفاع


# ==============================================================================
# اختبارات تكامل الكاشف
# ==============================================================================

class TestDetectorIntegration:
    """اختبارات تكامل — تحتاج النموذج"""

    @pytest.mark.integration
    def test_detect_returns_detections(self, sample_frame_720p):
        """detect() تُرجع sv.Detections"""
        from engine.preprocessor import FramePreprocessor

        detector = ObjectDetector()
        preprocessor = FramePreprocessor()

        tensor, scale_info = preprocessor.preprocess(sample_frame_720p)
        result = detector.detect(tensor, scale_info)

        assert isinstance(result, sv.Detections)

    @pytest.mark.integration
    def test_detect_empty_frame(self, black_frame):
        """إطار أسود → كشوفات فارغة أو قليلة"""
        from engine.preprocessor import FramePreprocessor

        detector = ObjectDetector()
        preprocessor = FramePreprocessor()

        tensor, scale_info = preprocessor.preprocess(black_frame)
        result = detector.detect(tensor, scale_info)

        assert isinstance(result, sv.Detections)
        # إطار أسود لا يجب أن يحتوي على مركبات
        assert len(result) == 0

    @pytest.mark.integration
    def test_detect_confidence_filtering(self):
        """التحقق من أن جميع الثقات أعلى من العتبة"""
        detector = ObjectDetector(confidence_threshold=0.5)
        from engine.preprocessor import FramePreprocessor
        preprocessor = FramePreprocessor()

        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        tensor, scale_info = preprocessor.preprocess(frame)
        result = detector.detect(tensor, scale_info)

        if len(result) > 0:
            assert all(c > 0.5 for c in result.confidence)

"""
اختبارات التكامل — Pipeline الكامل
=====================================
يختبر خط الأنابيب الكامل:
preprocessor → detector → tracker → line_zone

هذه الاختبارات تحتاج نموذج YOLO26 الفعلي.
"""

import queue
import numpy as np
import pytest
import supervision as sv

from engine.preprocessor import FramePreprocessor
from engine.detector import ObjectDetector
from engine.tracker import VehicleTracker, LineZoneManager


@pytest.mark.integration
class TestFullPipeline:
    """اختبارات خط الأنابيب الكامل"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """تهيئة مكونات Pipeline"""
        self.preprocessor = FramePreprocessor()
        self.detector = ObjectDetector()
        self.tracker = VehicleTracker()
        self.line_manager = LineZoneManager()

    def test_pipeline_720p(self, sample_frame_720p):
        """Pipeline كامل مع إطار 720p"""
        # معالجة مسبقة
        tensor, scale_info = self.preprocessor.preprocess(sample_frame_720p)
        assert tensor.shape == (1, 3, 640, 640)

        # كشف
        detections = self.detector.detect(tensor, scale_info)
        assert isinstance(detections, sv.Detections)

        # تتبع
        tracked = self.tracker.update(detections)
        assert isinstance(tracked, sv.Detections)

        # تصفية مركبات
        vehicles = self.tracker.filter_vehicles(tracked)
        assert isinstance(vehicles, sv.Detections)

    def test_pipeline_1080p(self, sample_frame_1080p):
        """Pipeline كامل مع إطار 1080p"""
        tensor, scale_info = self.preprocessor.preprocess(sample_frame_1080p)
        detections = self.detector.detect(tensor, scale_info)
        tracked = self.tracker.update(detections)
        vehicles = self.tracker.filter_vehicles(tracked)
        assert isinstance(vehicles, sv.Detections)

    def test_pipeline_with_line_zone(self, sample_frame_720p):
        """Pipeline مع خط عد"""
        # تعيين خط
        self.line_manager.set_line("main", (0, 360), (1280, 360))

        # معالجة
        tensor, scale_info = self.preprocessor.preprocess(sample_frame_720p)
        detections = self.detector.detect(tensor, scale_info)
        tracked = self.tracker.update(detections)
        vehicles = self.tracker.filter_vehicles(tracked)

        # تحديث الخط
        self.line_manager.update(vehicles)

        # التحقق من العدادات
        counts = self.line_manager.get_counts()
        assert "in_count" in counts
        assert "out_count" in counts

    def test_pipeline_black_frame_no_detections(self, black_frame):
        """إطار أسود → لا كشوفات"""
        tensor, scale_info = self.preprocessor.preprocess(black_frame)
        detections = self.detector.detect(tensor, scale_info)
        assert len(detections) == 0

    def test_pipeline_multiple_frames(self, sample_frame_720p):
        """معالجة عدة إطارات متتالية"""
        for i in range(5):
            tensor, scale_info = self.preprocessor.preprocess(sample_frame_720p)
            detections = self.detector.detect(tensor, scale_info)
            tracked = self.tracker.update(detections)
            vehicles = self.tracker.filter_vehicles(tracked)

        # لم يحدث خطأ
        assert True

    def test_pipeline_scale_info_consistency(self, sample_frame_1080p):
        """تناسق scale_info بين preprocessor و detector"""
        tensor, scale_info = self.preprocessor.preprocess(sample_frame_1080p)

        # scale_info يجب أن يحتوي أبعاد أصلية صحيحة
        assert scale_info["orig_w"] == 1920
        assert scale_info["orig_h"] == 1080

        detections = self.detector.detect(tensor, scale_info)

        # الإحداثيات لن تتجاوز الأبعاد الأصلية
        if len(detections) > 0:
            assert detections.xyxy[:, 0].min() >= 0
            assert detections.xyxy[:, 1].min() >= 0
            assert detections.xyxy[:, 2].max() <= 1920
            assert detections.xyxy[:, 3].max() <= 1080


@pytest.mark.integration
class TestResetFlow:
    """اختبار تدفق إعادة التعيين"""

    def test_reset_counts_flow(self, sample_frame_720p):
        """اختبار تدفق إعادة العد الكامل"""
        preprocessor = FramePreprocessor()
        detector = ObjectDetector()
        tracker = VehicleTracker()
        manager = LineZoneManager()

        # تعيين خط
        manager.set_line("main", (0, 360), (1280, 360))

        # معالجة إطار
        tensor, scale_info = preprocessor.preprocess(sample_frame_720p)
        detections = detector.detect(tensor, scale_info)
        tracked = tracker.update(detections)
        vehicles = tracker.filter_vehicles(tracked)
        manager.update(vehicles)

        # إعادة التعيين
        manager.reset_counts()
        counts = manager.get_counts()
        assert counts["in_count"] == 0
        assert counts["out_count"] == 0

        # الخط لا يزال موجود
        assert manager.has_line

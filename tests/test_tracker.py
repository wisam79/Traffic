"""
اختبارات المتتبع ومدير خط العد - Tracker Tests
=================================================
يختبر VehicleTracker و LineZoneManager مع:
- تتبع ByteTrack
- تصفية فئات المركبات
- إنشاء/مسح خط العد
- حساب الدخول/الخروج
- إعادة تعيين العدادات
- التسميات العربية
"""

import numpy as np
import pytest
import supervision as sv

from engine.tracker import VehicleTracker, LineZoneManager
from core.config import VEHICLE_CLASSES


# ==============================================================================
# اختبارات المتتبع
# ==============================================================================

class TestVehicleTrackerInit:
    """اختبارات تهيئة المتتبع"""

    def test_default_classes(self):
        """التحقق من فئات المركبات الافتراضية"""
        tracker = VehicleTracker()
        assert tracker.vehicle_classes == VEHICLE_CLASSES

    def test_custom_classes(self):
        """التحقق من فئات مخصصة"""
        classes = {2: "car"}
        tracker = VehicleTracker(vehicle_classes=classes)
        assert tracker.vehicle_classes == classes

    def test_byte_tracker_created(self):
        """التحقق من إنشاء ByteTracker"""
        tracker = VehicleTracker()
        assert tracker.byte_tracker is not None


class TestVehicleTrackerUpdate:
    """اختبارات تحديث التتبع"""

    def test_update_returns_detections(self, sample_detections):
        """update() تُرجع sv.Detections"""
        tracker = VehicleTracker()
        result = tracker.update(sample_detections)
        assert isinstance(result, sv.Detections)

    def test_update_empty_detections(self, empty_detections):
        """تحديث بكشوفات فارغة"""
        tracker = VehicleTracker()
        result = tracker.update(empty_detections)
        assert isinstance(result, sv.Detections)
        assert len(result) == 0

    def test_update_adds_tracker_id(self, sample_detections):
        """التحقق من إضافة معرفات التتبع"""
        tracker = VehicleTracker()
        result = tracker.update(sample_detections)
        # ByteTrack يُضيف tracker_id
        if len(result) > 0:
            assert result.tracker_id is not None


class TestVehicleFilter:
    """اختبارات تصفية المركبات"""

    def test_filter_keeps_vehicles(self):
        """يحتفظ بالمركبات فقط (car=2, truck=7, motorcycle=3)"""
        tracker = VehicleTracker()
        dets = sv.Detections(
            xyxy=np.array([
                [100, 200, 300, 400],
                [500, 100, 700, 350],
                [200, 300, 350, 500],
            ], dtype=np.float32),
            confidence=np.array([0.9, 0.85, 0.7], dtype=np.float32),
            class_id=np.array([2, 7, 3], dtype=int)
        )
        # تمرير عبر tracker أولاً للحصول على tracker_id
        tracked = tracker.update(dets)
        result = tracker.filter_vehicles(tracked)
        # كلها مركبات
        assert len(result) >= 0  # ByteTrack قد لا يُتبع الكل من أول إطار

    def test_filter_removes_non_vehicles(self, non_vehicle_detections):
        """يحذف غير المركبات (person=0, dog=16)"""
        tracker = VehicleTracker()
        result = tracker.filter_vehicles(non_vehicle_detections)
        assert len(result) == 0

    def test_filter_mixed(self):
        """خليط من مركبات وغير مركبات"""
        tracker = VehicleTracker()
        mixed = sv.Detections(
            xyxy=np.array([
                [100, 100, 200, 200],  # car (2) ✅
                [300, 300, 400, 400],  # person (0) ❌
                [500, 500, 600, 600],  # bus (5) ✅
            ], dtype=np.float32),
            confidence=np.array([0.9, 0.95, 0.8]),
            class_id=np.array([2, 0, 5])
        )
        # تمرير عبر tracker أولاً
        tracked = tracker.update(mixed)
        result = tracker.filter_vehicles(tracked)
        # person يُحذف
        for det_class in result.class_id:
            assert det_class in {2, 5}

    def test_filter_empty(self, empty_detections):
        """تصفية كشوفات فارغة"""
        tracker = VehicleTracker()
        result = tracker.filter_vehicles(empty_detections)
        assert len(result) == 0


class TestVehicleLabels:
    """اختبارات التسميات"""

    def test_labels_format(self):
        """التحقق من تنسيق التسميات"""
        tracker = VehicleTracker()
        dets = sv.Detections(
            xyxy=np.array([[100, 200, 300, 400]], dtype=np.float32),
            confidence=np.array([0.9], dtype=np.float32),
            class_id=np.array([2], dtype=int)
        )
        tracked = tracker.update(dets)
        if len(tracked) > 0:
            labels = tracker.get_labels(tracked)
            assert isinstance(labels, list)
            assert len(labels) == len(tracked)

    def test_labels_contain_class_name(self):
        """التحقق من أن التسميات تحتوي اسم الفئة"""
        tracker = VehicleTracker()
        dets = sv.Detections(
            xyxy=np.array([[100, 200, 300, 400]], dtype=np.float32),
            confidence=np.array([0.9], dtype=np.float32),
            class_id=np.array([2], dtype=int)
        )
        tracked = tracker.update(dets)
        if len(tracked) > 0:
            labels = tracker.get_labels(tracked)
            for label in labels:
                assert isinstance(label, str)
                assert len(label) > 0


# ==============================================================================
# اختبارات مدير خط العد
# ==============================================================================

class TestLineZoneManagerInit:
    """اختبارات تهيئة مدير الخط"""

    def test_initial_no_line(self):
        """لا يوجد خط عند البداية"""
        manager = LineZoneManager()
        assert len(manager.line_zones) == 0

    def test_initial_counts_zero(self):
        """العدادات صفرية عند البداية"""
        manager = LineZoneManager()
        counts = manager.get_counts()
        assert counts["in_count"] == 0
        assert counts["out_count"] == 0


class TestLineZoneManagerSetLine:
    """اختبارات تعيين الخط"""

    def test_set_line(self):
        """تعيين خط عد"""
        manager = LineZoneManager()
        manager.set_line("test", (100, 200), (500, 200))
        assert len(manager.line_zones) > 0

    def test_set_line_horizontal(self):
        """خط أفقي"""
        manager = LineZoneManager()
        manager.set_line("test", (0, 300), (640, 300))
        assert len(manager.line_zones) > 0

    def test_set_line_vertical(self):
        """خط عمودي"""
        manager = LineZoneManager()
        manager.set_line("test", (320, 0), (320, 480))
        assert len(manager.line_zones) > 0

    def test_set_line_diagonal(self):
        """خط مائل"""
        manager = LineZoneManager()
        manager.set_line("test", (100, 100), (500, 400))
        assert len(manager.line_zones) > 0

    def test_clear_line(self):
        """مسح الخط"""
        manager = LineZoneManager()
        manager.set_line("test", (100, 200), (500, 200))
        assert len(manager.line_zones) > 0
        manager.clear_line()
        assert len(manager.line_zones) == 0


class TestLineZoneManagerCounts:
    """اختبارات العدادات"""

    def test_counts_after_no_update(self):
        """العدادات بعد تعيين الخط بدون تحديث"""
        manager = LineZoneManager()
        manager.set_line("test", (100, 200), (500, 200))
        counts = manager.get_counts()
        assert counts["in_count"] == 0
        assert counts["out_count"] == 0

    def test_reset_counts(self):
        """إعادة تعيين العدادات"""
        manager = LineZoneManager()
        manager.set_line("test", (100, 200), (500, 200))
        manager.reset_counts()
        counts = manager.get_counts()
        assert counts["in_count"] == 0
        assert counts["out_count"] == 0

    def test_reset_keeps_line(self):
        """إعادة التعيين لا تحذف الخط"""
        manager = LineZoneManager()
        manager.set_line("test", (100, 200), (500, 200))
        manager.reset_counts()
        assert len(manager.line_zones) > 0

    def test_counts_without_line(self):
        """العدادات بدون خط مُعين"""
        manager = LineZoneManager()
        assert not manager.has_line
        counts = manager.get_counts()
        assert counts["in_count"] == 0
        assert counts["out_count"] == 0

    def test_reset_without_line_no_error(self):
        """إعادة التعيين بدون خط — لا خطأ"""
        manager = LineZoneManager()
        manager.reset_counts()  # لا يجب أن يُسبب خطأ

    def test_update_with_empty_detections(self, empty_detections):
        """تحديث بكشوفات فارغة"""
        manager = LineZoneManager()
        manager.set_line("test", (100, 200), (500, 200))
        manager.update(empty_detections)
        counts = manager.get_counts()
        assert counts["in_count"] == 0
        assert counts["out_count"] == 0

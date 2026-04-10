"""
ملف التتبع والخط العددي - Tracker & Line Zone
===============================================
يُدير تتبع الكائنات عبر الإطارات وحساب crossings لخط العد.

المسؤوليات:
- تتبع المركبات باستخدام ByteTrack
- تصفية الكشوفات للاحتفاظ بالمركبات فقط
- إدارة خط العد (LineZone) وحساب الدخول/الخروج

المرتبط به:
- يُستورد من: ai_thread.py
- يستقبل من: detector.py (كشوفات خام)
- يرتبط بـ: main_window.py (عبر إحداثيات الخط)
"""

import logging
from typing import Dict, Tuple

import numpy as np
import supervision as sv

from core.config import VEHICLE_CLASSES, TRACKER_FRAME_RATE

logger = logging.getLogger(__name__)


class VehicleTracker:
    """
    متتبع المركبات
    ================
    يُغلف ByteTrack ويُدير تتبع المركبات عبر الإطارات.
    يُصفي الكشوفات للاحتفاظ بالمركبات فقط.
    """

    def __init__(self, vehicle_classes: Dict[int, str] = VEHICLE_CLASSES, frame_rate: int = TRACKER_FRAME_RATE):
        """
        تهيئة المتتبع

        المُعاملات (Args):
            vehicle_classes: قاموس أرقام الفئات → أسماء المركبات
            frame_rate: معدل الإطارات للتتبع
        """
        self.vehicle_classes = vehicle_classes
        self.vehicle_class_names = set(vehicle_classes.values())

        # إنشاء ByteTracker
        # ByteTrack يتتبع الكائنات حتى عند فقدان الكشف مؤقتاً
        self.byte_tracker = sv.ByteTrack(frame_rate=frame_rate)

    def update(self, detections: sv.Detections) -> sv.Detections:
        """
        تحديث التتبع بكشوفات جديدة

        المُعاملات (Args):
            detections: كشوفات من detector.py

        المرجع (Returns):
            كشوفات مُحدثة مع معرفات التتبع
        """
        # تحديث المتتبع بالكشوفات الجديدة
        if len(detections) > 0:
            tracked = self.byte_tracker.update_with_detections(detections)
        else:
            tracked = sv.Detections.empty()

        return tracked

    def filter_vehicles(self, detections: sv.Detections) -> sv.Detections:
        """
        تصفية الكشوفات للاحتفاظ بالمركبات فقط

        المُعاملات (Args):
            detections: جميع الكشوفات

        المرجع (Returns):
            كشوفات المركبات فقط
        """
        if len(detections) == 0:
            return detections

        # إنشاء قناع (mask) للمركبات
        # رقم الفئة يجب أن يكون في vehicle_classes
        vehicle_class_ids = set(self.vehicle_classes.keys())
        mask = np.array([cid in vehicle_class_ids for cid in detections.class_id])

        # تطبيق القناع
        vehicle_detections = detections[mask]

        # تصفية للكشوفات المُتبعة فقط (tracker_id != -1)
        if len(vehicle_detections) > 0:
            tracked_mask = vehicle_detections.tracker_id != -1
            return vehicle_detections[tracked_mask]

        return vehicle_detections

    def get_labels(self, detections: sv.Detections) -> list:
        """
        إنشاء تسميات نصية للكشوفات

        تُستخدم للرسم على الإطار.

        المُعاملات (Args):
            detections: كشوفات المُتبعة

        المرجع (Returns):
            قائمة النصوص (مثال: "ID:12 car")
        """
        labels = []

        for class_id, tracker_id in zip(detections.class_id, detections.tracker_id):
            class_name = self.vehicle_classes.get(class_id, "unknown")
            label = f"ID:{tracker_id} {class_name}"
            labels.append(label)

        return labels


class LineZoneManager:
    """
    مدير خط العد
    ==============
    يُنشئ ويُدير LineZone من supervision.
    يحسب عدد المركبات الداخلة والخارجة.
    """

    def __init__(self):
        """
        تهيئة مدير الخط
        ---------------
        يبدأ بدون خط - يجب استدعاء set_line() لتحديده.
        """
        self.line_zones: Dict[str, sv.LineZone] = {}

    def set_line(self, line_id: str, point_a: Tuple[int, int], point_b: Tuple[int, int]) -> None:
        existing = self.line_zones.get(line_id)
        if existing is not None:
            start = existing.vector.start
            end = existing.vector.end
            if (start.x, start.y) == point_a and (end.x, end.y) == point_b:
                return
        self.line_zones[line_id] = sv.LineZone(
            start=sv.Point(x=point_a[0], y=point_a[1]),
            end=sv.Point(x=point_b[0], y=point_b[1]),
            triggering_anchors=(sv.Position.BOTTOM_CENTER,),
            minimum_crossing_threshold=3
        )
        logger.info(f"تم تعيين خط العد [{line_id}]: {point_a} -> {point_b}")

    def remove_line(self, line_id: str) -> None:
        if line_id in self.line_zones:
            del self.line_zones[line_id]
            logger.info(f"تم إزالة خط العد [{line_id}]")

    def clear_line(self) -> None:
        self.line_zones.clear()
        logger.info("تم مسح جميع خطوط العد")

    def update(self, vehicle_detections: sv.Detections) -> None:
        for line_zone in self.line_zones.values():
            line_zone.trigger(vehicle_detections)

    def reset_counts(self) -> None:
        new_zones = {}
        for line_id, line_zone in self.line_zones.items():
            start = line_zone.vector.start
            end = line_zone.vector.end
            new_zones[line_id] = sv.LineZone(
                start=start, end=end,
                triggering_anchors=(sv.Position.BOTTOM_CENTER,),
                minimum_crossing_threshold=3
            )
        self.line_zones = new_zones
        logger.info("تم إعادة تعيين عدادات خطوط العد")

    def get_counts(self, vehicle_classes: Dict[int, str] = None) -> Dict[str, int]:
        if not self.line_zones:
            result = {"in_count": 0, "out_count": 0}
            if vehicle_classes:
                for class_name in vehicle_classes.values():
                    result[class_name] = 0
            return result

        in_count = sum(lz.in_count for lz in self.line_zones.values())
        out_count = sum(lz.out_count for lz in self.line_zones.values())
        result = {"in_count": in_count, "out_count": out_count}

        if vehicle_classes:
            for class_id, class_name in vehicle_classes.items():
                total = 0
                for lz in self.line_zones.values():
                    total += lz.in_count_per_class.get(class_id, 0)
                    total += lz.out_count_per_class.get(class_id, 0)
                result[class_name] = total

        return result

    @property
    def has_line(self) -> bool:
        return len(self.line_zones) > 0

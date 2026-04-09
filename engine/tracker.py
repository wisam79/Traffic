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
from typing import Dict, Optional, Tuple

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
        self.line_zone: Optional[sv.LineZone] = None

    def set_line(self, point_a: Tuple[int, int], point_b: Tuple[int, int]) -> None:
        """
        تعيين خط العد الجديد

        المُعاملات (Args):
            point_a: نقطة البداية (x, y)
            point_b: نقطة النهاية (x, y)

        المرتبط به:
        - يُستدعى من: ai_thread.py
        - إحداثيات تأتي من: main_window.py (نقرات المستخدم)
        """
        self.line_zone = sv.LineZone(
            start=sv.Point(x=point_a[0], y=point_a[1]),
            end=sv.Point(x=point_b[0], y=point_b[1]),
            triggering_anchors=(sv.Position.BOTTOM_CENTER,),
            minimum_crossing_threshold=3
        )
        logger.info(f"تم تعيين خط العد: {point_a} -> {point_b}")

    def clear_line(self) -> None:
        """
        مسح خط العد
        ------------
        يُزيل الخط الحالي.
        """
        self.line_zone = None
        logger.info("تم مسح خط العد")

    def update(self, vehicle_detections: sv.Detections) -> None:
        """
        تحديث خط العد بكشوفات المركبات

        هذه الدالة هي التي تُفعّل العد!
        يجب استدعاؤها مع كشوفات المركبات فقط (ليست جميع الكشوفات).

        المُعاملات (Args):
            vehicle_detections: كشوفات المركبات المُتبعة
        """
        if self.line_zone is None:
            return

        # تفعيل الخط - supervision تتحقق من crossing
        self.line_zone.trigger(vehicle_detections)

    def reset_counts(self) -> None:
        """
        إعادة تعيين العدادات
        ======================
        يُعيد إنشاء LineZone بنفس الإحداثيات لتصفير العدادات.
        """
        if self.line_zone is not None:
            start = self.line_zone.vector.start
            end = self.line_zone.vector.end
            self.line_zone = sv.LineZone(
                start=start, end=end,
                triggering_anchors=(sv.Position.BOTTOM_CENTER,),
                minimum_crossing_threshold=3
            )
            logger.info("تم إعادة تعيين عدادات خط العد")

    def get_counts(self) -> Dict[str, int]:
        """
        الحصول على أعداد العد الحالية

        المرجع (Returns):
            قاموس بـ in_count و out_count
        """
        if self.line_zone is None:
            return {"in_count": 0, "out_count": 0}

        return {
            "in_count": self.line_zone.in_count,
            "out_count": self.line_zone.out_count
        }

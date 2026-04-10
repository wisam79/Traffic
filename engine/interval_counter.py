"""
عداد الفترات الزمنية - Interval Counter
==========================================
يُدير التقسيم الزمني للعدادات، يُحفظ سجل كل فترة ويُعيد تعيين العدادات تلقائياً.

المسؤوليات:
- تتبع الفترة الزمنية الحالية
- حفظ سجل الفترات المنتهية مع الإحصائيات
- إعادة تعيين العدادات عند انتهاء كل فترة
- دعم فترات مخصصة أو تراكمية (كامل المدة)

المرتبط به:
- يُستورد من: ai_thread.py
- يرتبط بـ: ui/interval_panel.py (عبر signals)
"""

import time
import threading
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class IntervalRecord:
    """
    سجل فترة زمنية
    ================
    يحتوي على بيانات فترة عد كاملة.
    """
    index: int
    start_time: float
    end_time: float
    duration_seconds: float
    stats: Dict[str, int]


class IntervalCounter:
    """
    عداد الفترات الزمنية
    =====================
    يُقسم وقت العد إلى فترات محددة ويُحفظ سجل كل فترة.
    عند انتهاء كل فترة يُعيد تعيين العدادات تلقائياً.
    """

    INTERVAL_NONE = 0
    INTERVAL_1_MIN = 60
    INTERVAL_5_MIN = 300
    INTERVAL_10_MIN = 600
    INTERVAL_15_MIN = 900
    INTERVAL_30_MIN = 1800
    INTERVAL_60_MIN = 3600

    PRESETS = [
        (INTERVAL_NONE, "كامل المدة"),
        (INTERVAL_1_MIN, "1 دقيقة"),
        (INTERVAL_5_MIN, "5 دقائق"),
        (INTERVAL_10_MIN, "10 دقائق"),
        (INTERVAL_15_MIN, "15 دقيقة"),
        (INTERVAL_30_MIN, "30 دقيقة"),
        (INTERVAL_60_MIN, "60 دقيقة"),
    ]

    def __init__(self):
        self._lock = threading.Lock()
        self._interval_seconds: int = self.INTERVAL_NONE
        self._start_time: float = 0.0
        self._interval_start_time: float = 0.0
        self._history: List[IntervalRecord] = []
        self._interval_index: int = 0
        self._is_active: bool = False
        self._last_snapshot: Dict[str, int] = {}

    def set_interval(self, seconds: int) -> None:
        with self._lock:
            self._interval_seconds = max(0, seconds)
            logger.info(f"تم تعيين فترة العد: {seconds} ثانية")

    def get_interval(self) -> int:
        with self._lock:
            return self._interval_seconds

    def start(self) -> None:
        with self._lock:
            self._start_time = time.time()
            self._interval_start_time = self._start_time
            self._interval_index = 0
            self._history.clear()
            self._is_active = True
            self._last_snapshot = {}
        logger.info("تم بدء عداد الفترات الزمنية")

    def stop(self) -> None:
        with self._lock:
            self._is_active = False
        logger.info("تم إيقاف عداد الفترات الزمنية")

    def reset(self) -> None:
        with self._lock:
            self._history.clear()
            self._interval_index = 0
            self._interval_start_time = time.time()
            self._last_snapshot = {}
        logger.info("تم إعادة تعيين عداد الفترات الزمنية")

    def check_interval(self, current_stats: Dict[str, int]) -> Optional[IntervalRecord]:
        """
        فحص ما إذا انتهت الفترة الحالية

        المُعاملات (Args):
            current_stats: الإحصائيات الحالية من LineZoneManager

        المرجع (Returns):
            IntervalRecord إذا انتهت فترة، أو None
        """
        with self._lock:
            if not self._is_active or self._interval_seconds == self.INTERVAL_NONE:
                return None

            elapsed = time.time() - self._interval_start_time
            if elapsed < self._interval_seconds:
                return None

            record = IntervalRecord(
                index=self._interval_index,
                start_time=self._interval_start_time,
                end_time=time.time(),
                duration_seconds=elapsed,
                stats=self._compute_interval_stats(current_stats)
            )

            self._history.append(record)
            self._interval_index += 1
            self._interval_start_time = time.time()
            self._last_snapshot = {}

        logger.info(
            f"انتهت الفترة #{record.index + 1} — "
            f"الإجمالي: {record.stats.get('total', 0)}, "
            f"المدة: {record.duration_seconds:.0f}ث"
        )
        return record

    def _compute_interval_stats(self, current_stats: Dict[str, int]) -> Dict[str, int]:
        """
        حساب إحصائيات الفترة الحالية (الحالي - اللقطة السابقة)
        """
        result = {}
        for key, value in current_stats.items():
            prev = self._last_snapshot.get(key, 0)
            result[key] = max(0, value - prev)
        return result

    def get_elapsed(self) -> float:
        """
        الوقت المنقضي في الفترة الحالية (ثواني)
        """
        with self._lock:
            if not self._is_active:
                return 0.0
            return time.time() - self._interval_start_time

    def get_total_elapsed(self) -> float:
        """
        الوقت الكلي المنقضي منذ البدء (ثواني)
        """
        with self._lock:
            if not self._is_active:
                return 0.0
            return time.time() - self._start_time

    def get_progress(self) -> float:
        """
        نسبة التقدم في الفترة الحالية (0.0 - 1.0)
        للفترة الكاملة تعيد 0.0 دائماً
        """
        with self._lock:
            if not self._is_active or self._interval_seconds == self.INTERVAL_NONE:
                return 0.0
            elapsed = time.time() - self._interval_start_time
            return min(1.0, elapsed / self._interval_seconds)

    def get_history(self) -> List[IntervalRecord]:
        with self._lock:
            return list(self._history)

    def get_current_interval_number(self) -> int:
        with self._lock:
            return self._interval_index + 1

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._is_active

    @staticmethod
    def format_seconds(seconds: float) -> str:
        """
        تنسيق الثواني بصيغة MM:SS أو HH:MM:SS
        """
        total = int(seconds)
        hours = total // 3600
        minutes = (total % 3600) // 60
        secs = total % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

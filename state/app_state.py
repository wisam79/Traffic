"""
ملف إدارة الحالة - Application State Management
=================================================
يُدير الحالة المشتركة بين خيط واجهة المستخدم وخيط معالجة الذكاء الاصطناعي.
يضمن الوصول الآمن للبيانات باستخدام الأقفال (threading.Lock).

المسؤوليات:
- تخزين إحداثيات خط العد بشكل آمن
- إدارة حالة البث (نشط/متوقف)
- تخزين مصدر الفيديو
- حفظ الأحدثيات والإحصائيات

المرتبط به:
- يُستورد من: main_window.py, ai_thread.py
- مرتبط بـ: جميع المكونات التي تحتاج مشاركة البيانات
"""

import threading
from typing import Optional, Tuple, Dict, Any


class AppState:
    """
    حاوية حالة التطبيق الآمنة للخيوط
    ====================================
    تُوفر واجهة آمنة للوصول إلى البيانات المشتركة بين الخيوط المختلفة.
    كل عملية قراءة/كتابة تتم تحت قفل لمنع التضارب.
    """

    def __init__(self):
        """
        تهيئة مدير الحالة
        ------------------
        يُنشئ القفل والمتغيرات الداخلية.
        جميع المتغيرات خاصة (بادئة _) ولا يُ الوصول لها إلا عبر الدوال.
        """
        # القفل الرئيسي - يضمن الوصول الآمن من خيط واحد فقط في كل مرة
        self._lock = threading.Lock()

        # إحداثيات خطوط العد: {line_id: ((x1, y1), (x2, y2))} أو فارغ
        self._line_coordinates: Dict[Any, Tuple[Tuple[int, int], Tuple[int, int]]] = {}

        # مصدر الفيديو: مسار ملف، رابط RTSP، أو رقم كاميرا
        self._video_source: str = ""

        # حالة البث: هل الفيديو يعمل حالياً؟
        self._is_streaming: bool = False

        # الإحصائيات الحالية: عدد المركبات etc.
        self._stats: Dict[str, int] = {}

        # أبعاد الإطار الحالي
        self._frame_width: int = 0
        self._frame_height: int = 0

    # ==========================================================================
    # دوال إحداثيات الخط - Line Coordinates Methods
    # ==========================================================================

    def get_line_coordinates(self) -> Dict[Any, Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        الحصول على إحداثيات جميع خطوط العد

        المرجع (Returns):
            قاموس من معرف الخط إلى نقطتي البداية والنهاية
        """
        with self._lock:
            return self._line_coordinates.copy() if self._line_coordinates else {}

    def get_line_coordinate(self, line_id: Any) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        الحصول على إحداثيات خط عد محدد

        المُعاملات (Args):
            line_id: معرف الخط

        المرجع (Returns):
            Tuple من نقطتين أو None إذا لم يُحدد الخط
        """
        with self._lock:
            return self._line_coordinates.get(line_id)

    def set_line_coordinates(
        self, line_id: Any, coords: Optional[Tuple[Tuple[int, int], Tuple[int, int]]]
    ) -> None:
        """
        تعيين إحداثيات خط عد

        المُعاملات (Args):
            line_id: معرف الخط
            coords: نقطتي البداية والنهاية، أو None لمسح الخط
        """
        with self._lock:
            if coords is None:
                self._line_coordinates.pop(line_id, None)
            else:
                self._line_coordinates[line_id] = coords

    def remove_line_coordinates(self, line_id: Any) -> None:
        """
        إزالة إحداثيات خط عد محدد
        """
        self.set_line_coordinates(line_id, None)

    def clear_line_coordinates(self) -> None:
        """
        مسح جميع إحداثيات الخطوط
        """
        with self._lock:
            self._line_coordinates.clear()

    # ==========================================================================
    # دوال مصدر الفيديو - Video Source Methods
    # ==========================================================================

    def get_video_source(self) -> str:
        """
        الحصول على مصدر الفيديو الحالي

        المرجع (Returns):
            نص يحتوي على المسار أو الرابط
        """
        with self._lock:
            return self._video_source

    def set_video_source(self, source: str) -> None:
        """
        تعيين مصدر الفيديو الجديد

        المُعاملات (Args):
            source: مسار ملف، رابط RTSP، أو رقم كاميرا
        """
        with self._lock:
            self._video_source = source

    # ==========================================================================
    # دوال حالة البث - Streaming State Methods
    # ==========================================================================

    def is_streaming(self) -> bool:
        """
        التحقق من حالة البث

        المرجع (Returns):
            True إذا كان البث نشطاً، False إذا كان متوقفاً
        """
        with self._lock:
            return self._is_streaming

    def set_streaming(self, active: bool) -> None:
        """
        تغيير حالة البث

        المُعاملات (Args):
            active: True لبدء البث، False للإيقاف
        """
        with self._lock:
            self._is_streaming = active

    # ==========================================================================
    # دوال الإحصائيات - Statistics Methods
    # ==========================================================================

    def get_stats(self) -> Dict[str, int]:
        """
        الحصول على الإحصائيات الحالية

        المرجع (Returns):
            نسخة من القاموس (ليست المرجع الأصلي) لمنع التعديل الخارجي
        """
        with self._lock:
            return self._stats.copy()

    def set_stats(self, stats: Dict[str, int]) -> None:
        """
        تحديث الإحصائيات

        المُعاملات (Args):
            stats: قاموس جديد بالإحصائيات
        """
        with self._lock:
            self._stats = stats.copy()

    # ==========================================================================
    # دوال أبعاد الإطار - Frame Dimensions Methods
    # ==========================================================================

    def get_frame_dimensions(self) -> Tuple[int, int]:
        """
        الحصول على أبعاد الإطار الحالي

        المرجع (Returns):
            Tuple من (العرض، الارتفاع)
        """
        with self._lock:
            return (self._frame_width, self._frame_height)

    def set_frame_dimensions(self, width: int, height: int) -> None:
        """
        تعيين أبعاد الإطار

        المُعاملات (Args):
            width: عرض الإطار بالبكسل
            height: ارتفاع الإطار بالبكسل

        Raises:
            ValueError: إذا كانت الأبعاد غير صالحة
        """
        if not isinstance(width, int) or not isinstance(height, int):
            raise ValueError("الأبعاد يجب أن تكون أعداداً صحيحة")
        if width <= 0 or height <= 0:
            raise ValueError("الأبعاد يجب أن تكون أعداداً موجبة")

        with self._lock:
            self._frame_width = width
            self._frame_height = height


# ==============================================================================
# المثيل العام - Global Instance
# ==============================================================================
# هذا هو الكائن الوحيد الذي سيُستخدم في كامل التطبيق
# لا تُنشئ مثيل جديد - استخدم هذا المثيل مباشرة

app_state = AppState()

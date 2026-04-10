"""
ملف مشغل الفيديو - Video Player
=================================
يُدير عرض الفيديو على QGraphicsView مع دعم التكبير/التصغير والتحريك.

المسؤوليات:
- عرض الإطارات بكفاءة
- دعم التكبير بعجلة الماوس
- التحريك بالسحب
- تتبع FPS
- منع تسرب الذاكرة

المرتبط به:
- يُستورد من: video_panel.py
- يستقبل من: ai_thread.py (عبر Signal frame_ready)
"""

import time
import cv2
import numpy as np
from collections import deque
from typing import Dict, Optional

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QImage, QPixmap, QPainter, QWheelEvent
)


class ZoomableGraphicsView(QGraphicsView):
    """
    عرض رسوميات قابل للتكبير
    ==========================
    يُضيف دعم عجلة الماوس للتكبير/التصغير.
    يُحافظ على التناسب عند تغيير الحجم.
    """

    def __init__(self, parent=None):
        """
        تهيئة العرض
        ------------
        يُفعّل تتبع الماوس ويعطل السلوك الافتراضي.
        """
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._user_zoomed = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        معالجة عجلة الماوس للتكبير/التصغير

        المُعاملات (Args):
            event: حدث عجلة الماوس

        المرتبط به:
        - يُستدعى تلقائياً عند استخدام عجلة الماوس
        """
        # عوامل التكبير
        zoom_in_factor = 1.25
        zoom_out_factor = 0.8

        # التكبير أو التصغير حسب اتجاه العجلة
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

        self._user_zoomed = True

        event.accept()

    def resizeEvent(self, event) -> None:
        """
        معالجة تغيير الحجم

        يُحافظ على ملاءمة المشهد عند تغيير حجم النافذة.
        """
        super().resizeEvent(event)

        if not self._user_zoomed and self.scene() and self.scene().items():
            for item in self.scene().items():
                if hasattr(item, 'pixmap'):
                    self.fitInView(item, Qt.KeepAspectRatio)
                    break


class VideoDisplayManager:
    """
    مدير عرض الفيديو
    ==================
    يُدير تحديث الإطارات على QGraphicsScene.
    يتتبع FPS ويمنع تسرب الذاكرة.

    المرتبط به:
    - يُنشأ من: video_panel.py
    - يُستدعى من: main_window.py (عبر slot _on_frame_ready)
    - يستقبل البيانات من: ai_thread.py (Signal)
    """

    def __init__(self, graphics_view: ZoomableGraphicsView):
        """
        تهيئة مدير العرض

        المُعاملات (Args):
            graphics_view: عنصر ZoomableGraphicsView من الواجهة
        """
        # حفظ المرجع
        self.graphics_view = graphics_view

        # إنشاء المشهد
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)

        # إعدادات العرض
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.graphics_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.graphics_view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.graphics_view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        # عنصر الصورة - سيُحدث مع كل إطار
        self.pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._current_frame_data = None

        # ======================================================================
        # تتبع FPS
        # ======================================================================
        self.frame_times = deque(maxlen=120)
        self.current_fps = 0
        self.total_frames = 0

    def update_frame(self, frame: np.ndarray) -> None:
        """
        تحديث الإطار المعروض

        تُزيل الإطار القديم وتُضيف الجديد.
        تمنع تسرب الذاكرة بحذف العنصر القديم.

        المُعاملات (Args):
            frame: إطار مُعالج بصيغة BGR من ai_thread.py

        المرتبط به:
        - يُستدعى من: main_window.py._on_frame_ready()
        """
        if frame is None:
            return

        if not isinstance(frame, np.ndarray) or frame.size == 0:
            return

        if frame.ndim != 3 or frame.shape[2] != 3:
            return

        # ======================================================================
        # تحديث FPS
        # ======================================================================
        now = time.time()
        self.frame_times.append(now)
        self.total_frames += 1

        # حساب FPS الفعلي: عدد الإطارات في آخر ثانية
        if len(self.frame_times) >= 2:
            elapsed = self.frame_times[-1] - self.frame_times[0]
            if elapsed > 0:
                self.current_fps = int(len(self.frame_times) / elapsed)
            else:
                self.current_fps = 0
        else:
            self.current_fps = 0

        # ======================================================================
        # تحويل الإطار إلى QImage
        # ======================================================================

        # الخطوة 1: تحويل من BGR إلى RGB
        # OpenCV يستخدم BGR، لكن Qt يتوقع RGB
        # .copy() keeps data alive while QImage references it
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self._current_frame_data = rgb_frame

        # الخطوة 2: الحصول على الأبعاد
        height, width, channel = rgb_frame.shape
        bytes_per_line = 3 * width  # 3 بايت لكل بكسل (RGB)

        # الخطوة 3: إنشاء QImage
        # البيانات مباشرة من numpy array - لا نسخ!
        q_image = QImage(
            rgb_frame.data, width, height, bytes_per_line,
            QImage.Format_RGB888
        )

        # ======================================================================
        # تحديث المشهد
        # ======================================================================

        # إنشاء QPixmap من QImage
        pixmap = QPixmap.fromImage(q_image)

        # تحديث الصورة المعروضة (إعادة استخدام العنصر الموجود)
        if self.pixmap_item is not None:
            self.pixmap_item.setPixmap(pixmap)
        else:
            self.pixmap_item = self.scene.addPixmap(pixmap)

        # ملاءة العرض (فقط عند أول إطار أو بعد إعادة تعيين العرض)
        if not self.graphics_view._user_zoomed:
            self.graphics_view.fitInView(
                self.pixmap_item,
                Qt.AspectRatioMode.KeepAspectRatio
            )

    def zoom_in(self) -> None:
        """
        تكبير العرض
        ------------
        تُضاعف العرض بنسبة 120%
        """
        self.graphics_view.scale(1.2, 1.2)
        self.graphics_view._user_zoomed = True

    def zoom_out(self) -> None:
        """
        تصغير العرض
        -------------
        تُقلص العرض بنسبة 80%
        """
        self.graphics_view.scale(0.8, 0.8)
        self.graphics_view._user_zoomed = True

    def reset_view(self) -> None:
        """
        إعادة تعيين العرض
        -------------------
        تُزيل التكبير وتُلائم الإطار بالكامل.
        """
        self.graphics_view.resetTransform()
        self.graphics_view._user_zoomed = False
        if self.pixmap_item:
            self.graphics_view.fitInView(
                self.pixmap_item,
                Qt.AspectRatioMode.KeepAspectRatio
            )

    def get_zoom_level(self) -> int:
        """
        الحصول على مستوى التكبير الحالي

        المرجع (Returns):
            نسبة التكبير كنسبة مئوية (100 = بدون تكبير)
        """
        return int(self.graphics_view.transform().m11() * 100)

    def get_stats(self) -> Dict:
        """
        الحصول على إحصائيات الأداء

        المرجع (Returns):
            قاموس بـ fps و total_frames
        """
        return {
            'fps': self.current_fps,
            'total_frames': self.total_frames
        }

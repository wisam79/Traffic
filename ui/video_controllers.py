"""
ملف التحكم في الفيديو - Video Controllers
===========================================
يُدير جميع عناصر التحكم في تشغيل الفيديو:
- التشغيل/الإيقاف المؤقت/الخطوة
- سرعة التشغيل
- السطوع والتباين والتشبع
- التقاط الصور والتسجيل
- شريط التقدم والتنقل

المسؤوليات:
- توفير واجهة للتحكم في تشغيل الفيديو
- تعديل خصائص الصورة
- إدارة التسجيل والتقاط الصور

المرتبط به:
- يُستورد من: video_panel.py, control_panel.py
- يتحكم في: video_ingestor.py, ai_thread.py
"""

import cv2
import numpy as np
import time
import os
from datetime import datetime
from typing import Optional, Callable, Dict

import logging

logger = logging.getLogger(__name__)





# ==============================================================================
# مدير تعديل الصورة
# ==============================================================================

class ImageAdjuster:
    """
    مُعدّل خصائص الصورة
    =====================
    يُوفر تحكم في السطوع والتباين والتشبع.

    المرتبط به:
    - يُنشأ من: video_controllers.py
    - يُطبق على: كل إطار قبل العرض
    - يتحكم فيه: video_panel.py (عبر sliders)
    """

    def __init__(self):
        """تهيئة مُعدّل الصورة."""
        # القيم الافتراضية
        self.brightness = 0    # -100 إلى +100
        self.contrast = 1.0    # 0.0 إلى 3.0
        self.saturation = 1.0  # 0.0 إلى 3.0

        # هل التعديل نشط؟
        self.is_active = False

    def adjust(self, frame: np.ndarray) -> np.ndarray:
        if not self.is_active:
            return frame

        if self.brightness == 0 and self.contrast == 1.0 and self.saturation == 1.0:
            self.is_active = False
            return frame

        adjusted = frame

        if self.brightness != 0 or self.contrast != 1.0:
            adjusted = cv2.convertScaleAbs(adjusted, alpha=self.contrast, beta=self.brightness)

        if self.saturation != 1.0:
            hsv = cv2.cvtColor(adjusted, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            s = cv2.convertScaleAbs(s, alpha=self.saturation, beta=0)
            adjusted = cv2.cvtColor(cv2.merge([h, s, v]), cv2.COLOR_HSV2BGR)

        return adjusted

    def reset(self) -> None:
        """
        إعادة تعيين جميع القيم
        ========================
        """
        self.brightness = 0
        self.contrast = 1.0
        self.saturation = 1.0
        self.is_active = False
        logger.info("تم إعادة تعيين تعديل الصورة")

    def set_brightness(self, value: int) -> None:
        """
        تعيين السطوع

        المُعاملات (Args):
            value: -100 إلى +100
        """
        self.brightness = max(-100, min(value, 100))
        self.is_active = True

    def set_contrast(self, value: float) -> None:
        """
        تعيين التباين

        المُعاملات (Args):
            value: 0.0 إلى 3.0
        """
        self.contrast = max(0.0, min(value, 3.0))
        self.is_active = True

    def set_saturation(self, value: float) -> None:
        """
        تعيين التشبع

        المُعاملات (Args):
            value: 0.0 إلى 3.0
        """
        self.saturation = max(0.0, min(value, 3.0))
        self.is_active = True


# ==============================================================================
# مدير التسجيل والتقاط الصور
# ==============================================================================

class MediaRecorder:
    """
    مُسجل الفيديو والصور
    ======================
    يُدير التقاط الصور (Screenshots) وتسجيل الفيديو.

    المرتبط به:
    - يُنشأ من: video_controllers.py
    - يحفظ في: مجلد recordings/
    - يتحكم فيه: video_panel.py
    """

    def __init__(self, output_dir: str = "recordings"):
        """
        تهيئة المُسجل

        المُعاملات (Args):
            output_dir: مجلد الحفظ
        """
        self.output_dir = output_dir
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"فشل إنشاء المجلد {output_dir}: {e}")

        # حالة التسجيل
        self.is_recording = False
        self.video_writer = None
        self.recording_start_time = None
        self.current_filepath = None

        # إحصائيات
        self.total_screenshots = 0
        self.total_recordings = 0

    def __del__(self):
        if self.is_recording:
            self.stop_recording()

    def take_screenshot(self, frame: np.ndarray) -> str:
        """
        التقاط صورة من الإطار الحالي

        المُعاملات (Args):
            frame: الإطار الحالي (BGR)

        المرجع (Returns):
            مسار الملف المحفوظ
        """
        # إنشاء اسم ملف فريد
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)

        # حفظ الصورة
        success = cv2.imwrite(filepath, frame)
        if not success:
            logger.error(f"فشل حفظ الصورة: {filepath}")
            raise IOError(f"Failed to save screenshot to {filepath}")
        self.total_screenshots += 1

        logger.info(f"تم التقاط صورة: {filepath}")
        return filepath

    def start_recording(self, frame: np.ndarray, fps: float = 30.0) -> bool:
        """
        بدء تسجيل الفيديو

        المُعاملات (Args):
            frame: الإطار الأول (لتحديد الأبعاد)
            fps: عدد الإطارات في الثانية

        المرجع (Returns):
            True إذا نجح البدء
        """
        if self.is_recording:
            logger.warning("التسجيل قيد التشغيل بالفعل")
            return False

        if frame is None or frame.size == 0:
            logger.error("إطار غير صالح للتسجيل")
            return False

        # إنشاء اسم ملف فريد
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.avi"
        filepath = os.path.join(self.output_dir, filename)

        try:
            # الحصول على الأبعاد
            height, width = frame.shape[:2]

            # إنشاء VideoWriter — محاولة XVID أولاً
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter(
                filepath, fourcc, fps, (width, height)
            )

            if not self.video_writer.isOpened():
                # تحرير الكاتب الفاشل قبل المحاولة الثانية
                self.video_writer.release()

                # محاولة mp4v كبديل
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(
                    filepath, fourcc, fps, (width, height)
                )

                if not self.video_writer.isOpened():
                    self.video_writer.release()
                    self.video_writer = None
                    logger.error("فشل بدء التسجيل بجميع الكوديكات")
                    return False

            # كتابة الإطار الأول
            self.video_writer.write(frame)

            self.current_filepath = filepath
            self.is_recording = True
            self.recording_start_time = time.time()
            self.total_recordings += 1

            logger.info(f"تم بدء التسجيل: {filepath}")
            return True

        except Exception as e:
            logger.error(f"خطأ في بدء التسجيل: {e}")
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            return False

    def write_frame(self, frame: np.ndarray) -> None:
        """
        كتابة إطار في الفيديو المسجل

        المُعاملات (Args):
            frame: الإطار للكتابة
        """
        if self.is_recording and self.video_writer:
            self.video_writer.write(frame)

    def stop_recording(self) -> Optional[str]:
        """
        إيقاف التسجيل

        المرجع (Returns):
            مسار الملف المسجل أو None
        """
        if not self.is_recording:
            return None

        filepath = self.current_filepath
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        self.current_filepath = None
        self.is_recording = False
        self.recording_start_time = None

        logger.info(f"تم إيقاف التسجيل")
        return filepath

    def get_recording_duration(self) -> float:
        """
        الحصول على مدة التسجيل الحالية

        المرجع (Returns):
            المدة بالثواني
        """
        if self.is_recording and self.recording_start_time:
            return time.time() - self.recording_start_time
        return 0.0

    def get_recording_status_text(self) -> str:
        """
        الحصول على نص حالة التسجيل

        المرجع (Returns):
            نص يصف حالة التسجيل
        """
        if self.is_recording:
            duration = self.get_recording_duration()
            mins = int(duration // 60)
            secs = int(duration % 60)
            return f"🔴 تسجيل {mins:02d}:{secs:02d}"
        return ""


# ==============================================================================
# مدير التحكم الشامل
# ==============================================================================

class VideoController:
    """
    متحكم الفيديو الشامل
    ======================
    يربط جميع المتحكمات الفرعية:
    - ImageAdjuster
    - MediaRecorder

    المرتبط به:
    - يُنشأ من: video_panel.py
    - يحتوي على جميع متحكمات الفيديو
    - يُطبق التعديلات على كل إطار
    """

    def __init__(self):
        """تهيئة متحكم الفيديو الشامل."""
        # المتحكمات الفرعية
        self.adjuster = ImageAdjuster()
        self.recorder = MediaRecorder()

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        معالجة إطار قبل العرض

        الخطوات:
        1. تعديل الصورة (سطوع، تباين، تشبع)
        2. كتابة الإطار إذا كان التسجيل نشط

        المُعاملات (Args):
            frame: الإطار الأصلي

        المرجع (Returns):
            إطار مُعالج
        """
        try:
            # تطبيق تعديل الصورة
            adjusted = self.adjuster.adjust(frame)

            # كتابة الإطار إذا كان التسجيل نشط
            if self.recorder.is_recording:
                self.recorder.write_frame(adjusted)

            return adjusted

        except Exception as e:
            logger.error(f"خطأ في معالجة الإطار: {e}")
            return frame

    def reset_all(self) -> None:
        """
        إعادة تعيين جميع المتحكمات
        =============================
        """
        self.adjuster.reset()
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        logger.info("تم إعادة تعيين جميع متحكمات الفيديو")

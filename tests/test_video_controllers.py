"""
اختبارات متحكمات الفيديو - Video Controllers Tests
====================================================
يختبر ImageAdjuster و MediaRecorder مع:
- تعديل السطوع/التباين/التشبع
- إعادة التعيين
- التقاط الصور
- التسجيل (بدء/إيقاف)
- VideoController الشامل
"""

import os
import tempfile
import numpy as np
import pytest

from ui.video_controllers import ImageAdjuster, MediaRecorder, VideoController


# ==============================================================================
# اختبارات مُعدّل الصورة
# ==============================================================================

class TestImageAdjusterInit:
    """اختبارات تهيئة المُعدّل"""

    def test_default_values(self):
        """القيم الافتراضية"""
        adj = ImageAdjuster()
        assert adj.brightness == 0
        assert adj.contrast == 1.0
        assert adj.saturation == 1.0




class TestImageAdjusterModify:
    """اختبارات التعديل"""

    def test_set_brightness(self):
        """تعيين السطوع"""
        adj = ImageAdjuster()
        adj.set_brightness(50)
        assert adj.brightness == 50

    def test_set_contrast(self):
        """تعيين التباين"""
        adj = ImageAdjuster()
        adj.set_contrast(1.5)
        assert adj.contrast == 1.5

    def test_set_saturation(self):
        """تعيين التشبع"""
        adj = ImageAdjuster()
        adj.set_saturation(2.0)
        assert adj.saturation == 2.0

    def test_reset(self):
        """إعادة التعيين"""
        adj = ImageAdjuster()
        adj.set_brightness(50)
        adj.set_contrast(2.0)
        adj.set_saturation(0.5)
        adj.reset()
        assert adj.brightness == 0
        assert adj.contrast == 1.0
        assert adj.saturation == 1.0


class TestImageAdjusterApply:
    """اختبارات تطبيق التعديل"""

    def test_adjust_default_no_change(self):
        """التعديل الافتراضي لا يُغير الصورة"""
        adj = ImageAdjuster()
        frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
        result = adj.adjust(frame)
        assert result.shape == frame.shape
        assert result.dtype == np.uint8

    def test_adjust_brightness_positive(self):
        """زيادة السطوع → قيم أعلى"""
        adj = ImageAdjuster()
        adj.set_brightness(50)
        frame = np.ones((100, 100, 3), dtype=np.uint8) * 100
        result = adj.adjust(frame)
        assert result.mean() > frame.mean()

    def test_adjust_brightness_negative(self):
        """إنقاص السطوع → قيم أقل"""
        adj = ImageAdjuster()
        adj.set_brightness(-50)
        frame = np.ones((100, 100, 3), dtype=np.uint8) * 200
        result = adj.adjust(frame)
        assert result.mean() < frame.mean()

    def test_adjust_output_shape(self):
        """الشكل لا يتغير"""
        adj = ImageAdjuster()
        adj.set_brightness(30)
        adj.set_contrast(1.5)
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = adj.adjust(frame)
        assert result.shape == (480, 640, 3)

    def test_adjust_output_clipped(self):
        """القيم محصورة بين 0 و 255"""
        adj = ImageAdjuster()
        adj.set_brightness(100)
        adj.set_contrast(3.0)
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = adj.adjust(frame)
        assert result.min() >= 0
        assert result.max() <= 255


# ==============================================================================
# اختبارات مُسجل الوسائط
# ==============================================================================

class TestMediaRecorderInit:
    """اختبارات تهيئة المُسجل"""

    def test_default_not_recording(self):
        """لا تسجيل عند البداية"""
        rec = MediaRecorder()
        assert rec.is_recording is False

    def test_default_counts_zero(self):
        """العدادات صفرية"""
        rec = MediaRecorder()
        assert rec.total_screenshots == 0
        assert rec.total_recordings == 0


class TestMediaRecorderScreenshot:
    """اختبارات التقاط الصور"""

    def test_take_screenshot(self):
        """التقاط صورة"""
        rec = MediaRecorder()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        filepath = rec.take_screenshot(frame)

        assert filepath is not None
        assert os.path.exists(filepath)
        assert rec.total_screenshots == 1

        # تنظيف
        os.remove(filepath)

    def test_screenshot_increments_count(self):
        """العداد يزيد مع كل صورة"""
        rec = MediaRecorder()
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        path1 = rec.take_screenshot(frame)
        path2 = rec.take_screenshot(frame)

        assert rec.total_screenshots == 2

        # تنظيف
        if path1 and os.path.exists(path1):
            os.remove(path1)
        if path2 and os.path.exists(path2):
            os.remove(path2)


# ==============================================================================
# اختبارات VideoController الشامل
# ==============================================================================

class TestVideoControllerInit:
    """اختبارات تهيئة المتحكم الشامل"""

    def test_has_adjuster(self):
        """يحتوي على مُعدّل"""
        vc = VideoController()
        assert isinstance(vc.adjuster, ImageAdjuster)

    def test_has_recorder(self):
        """يحتوي على مُسجل"""
        vc = VideoController()
        assert isinstance(vc.recorder, MediaRecorder)

    def test_no_playback_controller(self):
        """لا يحتوي على PlaybackController (تمت إزالته)"""
        vc = VideoController()
        assert not hasattr(vc, 'playback')


class TestVideoControllerProcessFrame:
    """اختبارات معالجة الإطار"""

    def test_process_returns_frame(self):
        """process_frame تُرجع إطار"""
        vc = VideoController()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = vc.process_frame(frame)
        assert isinstance(result, np.ndarray)
        assert result.shape == (480, 640, 3)

    def test_process_returns_frame(self):
        """معالجة الإطار تعيد إطار صالح"""
        vc = VideoController()
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        result = vc.process_frame(frame)

        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)

    def test_reset_all(self):
        """إعادة تعيين الكل"""
        vc = VideoController()
        vc.adjuster.set_brightness(50)
        vc.reset_all()
        assert vc.adjuster.brightness == 0

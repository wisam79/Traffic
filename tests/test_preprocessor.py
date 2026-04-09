"""
اختبارات المعالج المسبق - Preprocessor Tests
==============================================
يختبر FramePreprocessor مع:
- أحجام إطارات مختلفة (مربع، أفقي، عمودي)
- صحة Letterbox (النسبة + الحشو + اللون)
- صحة معلومات التحجيم (scale_info)
- صحة الشكل والتنسيق النهائي
- حالات الحافة (إطار فارغ، أبعاد صفرية)
"""

import numpy as np
import pytest

from engine.preprocessor import FramePreprocessor


class TestFramePreprocessorInit:
    """اختبارات تهيئة المعالج"""

    def test_default_target_size(self):
        """التحقق من الحجم الافتراضي 640×640"""
        fp = FramePreprocessor()
        assert fp.target_size == (640, 640)

    def test_custom_target_size(self):
        """التحقق من حجم مخصص"""
        fp = FramePreprocessor(target_size=(320, 320))
        assert fp.target_size == (320, 320)

    def test_invalid_target_size_raises(self):
        """خطأ عند حجم سالب أو صفري"""
        with pytest.raises(ValueError):
            FramePreprocessor(target_size=(0, 640))
        with pytest.raises(ValueError):
            FramePreprocessor(target_size=(640, -1))


class TestPreprocessOutputShape:
    """اختبارات شكل المخرجات"""

    def test_output_shape_square(self, sample_frame_640):
        """مخرجات إطار مربع: (1, 3, 640, 640)"""
        fp = FramePreprocessor()
        tensor, _ = fp.preprocess(sample_frame_640)
        assert tensor.shape == (1, 3, 640, 640)

    def test_output_shape_1080p(self, sample_frame_1080p):
        """مخرجات إطار 1080p: (1, 3, 640, 640)"""
        fp = FramePreprocessor()
        tensor, _ = fp.preprocess(sample_frame_1080p)
        assert tensor.shape == (1, 3, 640, 640)

    def test_output_shape_720p(self, sample_frame_720p):
        """مخرجات إطار 720p: (1, 3, 640, 640)"""
        fp = FramePreprocessor()
        tensor, _ = fp.preprocess(sample_frame_720p)
        assert tensor.shape == (1, 3, 640, 640)

    def test_output_shape_vertical(self, sample_frame_vertical):
        """مخرجات إطار عمودي: (1, 3, 640, 640)"""
        fp = FramePreprocessor()
        tensor, _ = fp.preprocess(sample_frame_vertical)
        assert tensor.shape == (1, 3, 640, 640)

    def test_output_dtype_float32(self, sample_frame_720p):
        """التحقق من نوع البيانات float32"""
        fp = FramePreprocessor()
        tensor, _ = fp.preprocess(sample_frame_720p)
        assert tensor.dtype == np.float32

    def test_output_range_normalized(self, sample_frame_720p):
        """التحقق من أن القيم بين 0 و1"""
        fp = FramePreprocessor()
        tensor, _ = fp.preprocess(sample_frame_720p)
        assert tensor.min() >= 0.0
        assert tensor.max() <= 1.0


class TestLetterboxScaleInfo:
    """اختبارات معلومات التحجيم"""

    def test_scale_info_keys(self, sample_frame_720p):
        """التحقق من وجود جميع المفاتيح"""
        fp = FramePreprocessor()
        _, info = fp.preprocess(sample_frame_720p)
        assert "scale" in info
        assert "pad_x" in info
        assert "pad_y" in info
        assert "orig_w" in info
        assert "orig_h" in info

    def test_scale_info_orig_dims_720p(self, sample_frame_720p):
        """التحقق من الأبعاد الأصلية لـ 720p"""
        fp = FramePreprocessor()
        _, info = fp.preprocess(sample_frame_720p)
        assert info["orig_w"] == 1280
        assert info["orig_h"] == 720

    def test_scale_info_orig_dims_1080p(self, sample_frame_1080p):
        """التحقق من الأبعاد الأصلية لـ 1080p"""
        fp = FramePreprocessor()
        _, info = fp.preprocess(sample_frame_1080p)
        assert info["orig_w"] == 1920
        assert info["orig_h"] == 1080

    def test_scale_info_square_no_padding(self, sample_frame_640):
        """إطار مربع 640×640 → لا حشو"""
        fp = FramePreprocessor()
        _, info = fp.preprocess(sample_frame_640)
        assert info["scale"] == pytest.approx(1.0)
        assert info["pad_x"] == 0
        assert info["pad_y"] == 0

    def test_scale_info_widescreen_pad_y(self, sample_frame_1080p):
        """إطار عريض → حشو عمودي"""
        fp = FramePreprocessor()
        _, info = fp.preprocess(sample_frame_1080p)
        # نسبة عريضة → scale بالعرض، حشو على المحور Y
        assert info["pad_y"] > 0
        assert info["pad_x"] == 0

    def test_scale_info_vertical_pad_x(self, sample_frame_vertical):
        """إطار عمودي → حشو أفقي"""
        fp = FramePreprocessor()
        _, info = fp.preprocess(sample_frame_vertical)
        # نسبة عمودية → scale بالارتفاع، حشو على المحور X
        assert info["pad_x"] > 0
        assert info["pad_y"] == 0

    def test_scale_stored_as_last(self, sample_frame_720p):
        """التحقق من تخزين معلومات التحجيم الأخيرة"""
        fp = FramePreprocessor()
        _, info = fp.preprocess(sample_frame_720p)
        assert fp.last_scale_info == info


class TestLetterboxPadding:
    """اختبارات حشو Letterbox"""

    def test_padding_color_is_gray(self, black_frame):
        """الحشو باللون الرمادي (114)"""
        fp = FramePreprocessor()
        tensor, info = fp.preprocess(black_frame)
        # الإطار أسود (0) + الحشو رمادي (114/255)
        gray_value = 114.0 / 255.0

        # فحص منطقة الحشو (فوق الصورة)
        if info["pad_y"] > 0:
            pad_region = tensor[0, 0, :info["pad_y"], :]
            assert np.allclose(pad_region, gray_value, atol=0.01)


class TestPreprocessEdgeCases:
    """اختبارات حالات الحافة"""

    def test_none_frame_raises(self):
        """خطأ عند إطار None"""
        fp = FramePreprocessor()
        with pytest.raises(ValueError, match="None"):
            fp.preprocess(None)

    def test_wrong_channels_raises(self):
        """خطأ عند إطار بقنوات خاطئة"""
        fp = FramePreprocessor()
        bad_frame = np.zeros((100, 100, 4), dtype=np.uint8)  # RGBA
        with pytest.raises(ValueError, match="3-channel"):
            fp.preprocess(bad_frame)

    def test_grayscale_raises(self):
        """خطأ عند إطار رمادي (بدون قنوات)"""
        fp = FramePreprocessor()
        gray = np.zeros((100, 100), dtype=np.uint8)
        with pytest.raises(ValueError):
            fp.preprocess(gray)

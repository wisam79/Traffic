"""
اختبارات أدوات الرسم - Drawing Modes Tests
=============================================
يختبر AdvancedLineDrawer مع:
- أوضاع الرسم (SINGLE_LINE, MULTI_LINE)
- التحقق من صحة الإحداثيات
- رسم وإكمال الخطوط
- مسح الخطوط
- التراجع/الإعادة
- حالات الحافة
"""

import pytest
from unittest.mock import MagicMock

from ui.drawing_modes import AdvancedLineDrawer, DrawingMode, LineData


# ==============================================================================
# اختبارات DrawingMode
# ==============================================================================

class TestDrawingMode:
    """اختبارات أوضاع الرسم"""

    def test_single_line_exists(self):
        """التحقق من وجود وضع SINGLE_LINE"""
        assert DrawingMode.SINGLE_LINE is not None

    def test_multi_line_exists(self):
        """التحقق من وجود وضع MULTI_LINE"""
        assert DrawingMode.MULTI_LINE is not None

    def test_no_zone_mode(self):
        """التحقق من عدم وجود وضع ZONE"""
        assert not hasattr(DrawingMode, "ZONE")

    def test_only_two_modes(self):
        """فقط وضعان"""
        values = list(DrawingMode)
        assert len(values) == 2


# ==============================================================================
# اختبارات LineData
# ==============================================================================

class TestLineData:
    """اختبارات بيانات الخط"""

    def test_create_line(self):
        """إنشاء خط"""
        line = LineData([(100, 200), (300, 400)], line_id=1)
        assert line.line_id == 1
        assert len(line.points) == 2
        assert line.is_active is True

    def test_start_point(self):
        """نقطة البداية"""
        line = LineData([(100, 200), (300, 400)], line_id=1)
        assert line.get_start_point() == (100, 200)

    def test_end_point(self):
        """نقطة النهاية"""
        line = LineData([(100, 200), (300, 400)], line_id=1)
        assert line.get_end_point() == (300, 400)

    def test_mid_point(self):
        """نقطة المنتصف"""
        line = LineData([(100, 200), (300, 400)], line_id=1)
        mid = line.get_mid_point()
        assert mid == (200, 300)

    def test_empty_line_start(self):
        """نقطة البداية لخط فارغ"""
        line = LineData([], line_id=1)
        assert line.get_start_point() == (0, 0)

    def test_empty_line_end(self):
        """نقطة النهاية لخط فارغ"""
        line = LineData([], line_id=1)
        assert line.get_end_point() == (0, 0)


# ==============================================================================
# اختبارات AdvancedLineDrawer
# ==============================================================================

class TestAdvancedLineDrawerInit:
    """اختبارات تهيئة الرسام"""

    def test_default_mode(self):
        """الوضع الافتراضي SINGLE_LINE"""
        drawer = AdvancedLineDrawer()
        assert drawer.drawing_mode == DrawingMode.SINGLE_LINE

    def test_not_drawing_initially(self):
        """لا رسم عند البداية"""
        drawer = AdvancedLineDrawer()
        assert drawer.is_drawing is False

    def test_empty_lines_initially(self):
        """لا خطوط عند البداية"""
        drawer = AdvancedLineDrawer()
        assert len(drawer.lines) == 0

    def test_frame_bounds_zero(self):
        """حدود الإطار صفرية عند البداية"""
        drawer = AdvancedLineDrawer()
        assert drawer.frame_width == 0
        assert drawer.frame_height == 0


class TestSetFrameBounds:
    """اختبارات تعيين حدود الإطار"""

    def test_set_bounds(self):
        """تعيين حدود"""
        drawer = AdvancedLineDrawer()
        drawer.set_frame_bounds(1920, 1080)
        assert drawer.frame_width == 1920
        assert drawer.frame_height == 1080


class TestCoordinateValidation:
    """اختبارات التحقق من صحة الإحداثيات"""

    def test_click_inside_frame(self):
        """نقرة داخل الإطار"""
        drawer = AdvancedLineDrawer()
        mock_scene = MagicMock()
        drawer.scene = mock_scene
        drawer.set_frame_bounds(640, 480)

        result = drawer.handle_click(320, 240)
        assert result != "outside_frame"

    def test_click_outside_frame_right(self):
        """نقرة خارج الإطار (يمين)"""
        drawer = AdvancedLineDrawer()
        mock_scene = MagicMock()
        drawer.scene = mock_scene
        drawer.set_frame_bounds(640, 480)

        result = drawer.handle_click(700, 240)
        assert result == "outside_frame"

    def test_click_outside_frame_bottom(self):
        """نقرة خارج الإطار (أسفل)"""
        drawer = AdvancedLineDrawer()
        mock_scene = MagicMock()
        drawer.scene = mock_scene
        drawer.set_frame_bounds(640, 480)

        result = drawer.handle_click(320, 500)
        assert result == "outside_frame"

    def test_click_negative_coords(self):
        """نقرة بإحداثيات سالبة"""
        drawer = AdvancedLineDrawer()
        mock_scene = MagicMock()
        drawer.scene = mock_scene
        drawer.set_frame_bounds(640, 480)

        result = drawer.handle_click(-10, 240)
        assert result == "outside_frame"

    def test_click_on_boundary(self):
        """نقرة على حدود الإطار — مقبولة"""
        drawer = AdvancedLineDrawer()
        mock_scene = MagicMock()
        drawer.scene = mock_scene
        drawer.set_frame_bounds(640, 480)

        result = drawer.handle_click(640, 480)
        assert result != "outside_frame"

    def test_no_bounds_allows_all(self):
        """بدون حدود مُعينة — كل النقرات مقبولة"""
        drawer = AdvancedLineDrawer()
        mock_scene = MagicMock()
        drawer.scene = mock_scene
        # لم نُعين حدود

        result = drawer.handle_click(9999, 9999)
        assert result != "outside_frame"


class TestSingleLineDrawing:
    """اختبارات رسم خط واحد"""

    def test_first_click_sets_point_a(self):
        """النقرة الأولى تُعين النقطة A"""
        drawer = AdvancedLineDrawer()
        mock_scene = MagicMock()
        drawer.scene = mock_scene

        result = drawer.handle_click(100, 200)
        assert result == "point_a_set"
        assert drawer.is_drawing is True

    def test_second_click_completes_line(self):
        """النقرة الثانية تُكمل الخط"""
        drawer = AdvancedLineDrawer()
        mock_scene = MagicMock()
        drawer.scene = mock_scene

        drawer.handle_click(100, 200)
        result = drawer.handle_click(400, 300)
        assert result == "line_complete"

    def test_line_stored_after_complete(self):
        """الخط يُحفظ بعد الإكمال"""
        drawer = AdvancedLineDrawer()
        mock_scene = MagicMock()
        drawer.scene = mock_scene

        drawer.handle_click(100, 200)
        drawer.handle_click(400, 300)

        assert len(drawer.lines) == 1
        assert drawer.lines[0].points[0] == (100, 200)
        assert drawer.lines[0].points[1] == (400, 300)


class TestSetDrawingMode:
    """اختبارات تبديل وضع الرسم"""

    def test_set_single_line(self):
        drawer = AdvancedLineDrawer()
        drawer.set_drawing_mode(DrawingMode.SINGLE_LINE)
        assert drawer.drawing_mode == DrawingMode.SINGLE_LINE

    def test_set_multi_line(self):
        drawer = AdvancedLineDrawer()
        drawer.set_drawing_mode(DrawingMode.MULTI_LINE)
        assert drawer.drawing_mode == DrawingMode.MULTI_LINE


class TestNoScene:
    """اختبارات بدون مشهد"""

    def test_click_without_scene(self):
        """نقرة بدون مشهد → خطأ"""
        drawer = AdvancedLineDrawer()
        result = drawer.handle_click(100, 200)
        assert result == "error_no_scene"

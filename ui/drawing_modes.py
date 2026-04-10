"""
ملف أدوات رسم الخطوط - Line Drawing Tools
==========================================
يُدير رسم وتحرير خطوط العد ومناطق العد.

المسؤوليات:
- دعم أوضاع رسم متعددة (خط واحد، خطوط متعددة، منطقة)
- معاينة مباشرة أثناء الرسم
- تحديد وتحرير/حذف الخطوط
- التراجع/إعادة
- نقاط الربط الذكية

المرتبط به:
- يُستورد من: video_panel.py
- يتفاعل مع: المستخدم (ماوس)
- يُرسل البيانات إلى: ai_thread.py
"""

import logging
import copy
from typing import List, Tuple, Optional, Callable
from enum import Enum

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsTextItem
from PySide6.QtCore import QPointF, QLineF, Qt
from PySide6.QtGui import QPen, QColor, QFont, QBrush, QPolygonF

logger = logging.getLogger(__name__)


# ==============================================================================
# أوضاع الرسم
# ==============================================================================

class DrawingMode(Enum):
    """
    أوضاع رسم الخطوط
    ==================
    """
    SINGLE_LINE = "خط واحد"
    MULTI_LINE = "خطوط متعددة"


# ==============================================================================
# بيانات الخط
# ==============================================================================

class LineData:
    """
    بيانات خط العد
    ================
    يُخزن إحداثيات الخط وخصائصه.
    """

    def __init__(self, points: List[Tuple[int, int]], line_id: int):
        """
        تهيئة بيانات الخط

        المُعاملات (Args):
            points: قائمة النقاط [(x1,y1), (x2,y2), ...]
            line_id: معرف فريد للخط
        """
        self.points = points
        self.line_id = line_id
        self.is_active = True

        # عناصر الرسوميات (للحذف لاحقاً)
        self.graphics_items = []

    def __deepcopy__(self, memo):
        """نسخ عميق لتجنب مشاكل QGraphicsItem"""
        import copy
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == 'graphics_items':
                setattr(result, k, [])
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result

    def get_start_point(self) -> Tuple[int, int]:
        """الحصول على نقطة البداية."""
        return self.points[0] if self.points else (0, 0)

    def get_end_point(self) -> Tuple[int, int]:
        """الحصول على نقطة النهاية."""
        return self.points[-1] if self.points else (0, 0)

    def get_mid_point(self) -> Tuple[int, int]:
        """الحصول على نقطة المنتصف."""
        if not self.points:
            return (0, 0)
        mid_x = sum(p[0] for p in self.points) // len(self.points)
        mid_y = sum(p[1] for p in self.points) // len(self.points)
        return (mid_x, mid_y)


# ==============================================================================
# مدير رسم الخطوط المتقدم
# ==============================================================================

class AdvancedLineDrawer:
    """
    مدير رسم الخطوط المتقدم
    ========================
    يُوفر رسم متقدم مع معاينة مباشرة وأوضاع متعددة.

    المرتبط به:
    - يُنشأ من: video_panel.py
    - يستقبل نقرات من: MouseFilter
    - يُرسل خطوط مكتملة إلى: ai_thread.py
    """

    def __init__(self, on_lines_changed_callback: Optional[Callable] = None):
        """
        تهيئة المدير

        المُعاملات (Args):
            on_lines_changed_callback: callback عند تغيير الخطوط
        """
        # الحالة
        self.drawing_mode = DrawingMode.SINGLE_LINE
        self.is_drawing = False
        self.current_points: List[Tuple[int, int]] = []

        # حدود الإطار (تُحدث عند تعيين المشهد)
        self.frame_width: int = 0
        self.frame_height: int = 0

        # قائمة جميع الخطوط
        self.lines: List[LineData] = []
        self.next_line_id = 1

        # التراجع/إعادة
        self.undo_stack: List[List[LineData]] = []
        self.redo_stack: List[List[LineData]] = []

        # المشهد
        self.scene = None

        # عناصر المعاينة المباشرة
        self.preview_items = []

        # العناصر المحددة
        self.selected_line_id: Optional[int] = None
        self.selection_items = []

        # Callbacks
        self.on_lines_changed_callback = on_lines_changed_callback

    def set_scene(self, scene) -> None:
        """
        تعيين المشهد

        المُعاملات (Args):
            scene: QGraphicsScene
        """
        self.scene = scene

    def set_frame_bounds(self, width: int, height: int) -> None:
        """
        تعيين حدود الإطار للتحقق من صحة الإحداثيات

        المُعاملات (Args):
            width: عرض إطار الفيديو بالبكسل
            height: ارتفاع إطار الفيديو بالبكسل
        """
        self.frame_width = width
        self.frame_height = height
        logger.info(f"حدود الإطار: {width}x{height}")

    def set_drawing_mode(self, mode: DrawingMode) -> None:
        """
        تعيين وضع الرسم

        المُعاملات (Args):
            mode: الوضع الجديد
        """
        self.drawing_mode = mode
        logger.info(f"وضع الرسم: {mode.value}")

    def handle_click(self, x: int, y: int) -> Optional[str]:
        """
        معالجة نقرة الماوس

        المُعاملات (Args):
            x, y: إحداثيات النقرة

        المرجع (Returns):
            نص يصف النتيجة
        """
        if self.scene is None:
            return "error_no_scene"

        # التحقق من صحة الإحداثيات (داخل حدود الإطار)
        if self.frame_width > 0 and self.frame_height > 0:
            if x < 0 or y < 0 or x > self.frame_width or y > self.frame_height:
                logger.warning(f"نقرة خارج حدود الإطار: ({x}, {y})")
                return "outside_frame"

        # وضع خط واحد
        if self.drawing_mode == DrawingMode.SINGLE_LINE:
            return self._handle_single_line_click(x, y)

        # وضع خطوط متعددة
        elif self.drawing_mode == DrawingMode.MULTI_LINE:
            return self._handle_multi_line_click(x, y)

        return "unknown_mode"

    def handle_move(self, x: int, y: int) -> None:
        """
        معالجة حركة الماوس (للمعاينة المباشرة)

        المُعاملات (Args):
            x, y: إحداثيات المؤشر
        """
        if not self.is_drawing or not self.current_points:
            return

        # تحديث المعاينة المباشرة
        self._update_preview(x, y)

    def _handle_single_line_click(self, x: int, y: int) -> str:
        """
        معالجة النقر في وضع خط واحد

        المُعاملات (Args):
            x, y: إحداثيات النقرة

        المرجع (Returns):
            نص الحالة
        """
        if not self.is_drawing:
            # ==================================================================
            # النقطة الأولى
            # ==================================================================
            self.is_drawing = True
            self.current_points = [(x, y)]

            # رسم نقطة البداية
            self._draw_point_marker(x, y, is_start=True)

            return "point_a_set"

        else:
            # ==================================================================
            # النقطة الثانية - اكتمال الخط
            # ==================================================================
            self.current_points.append((x, y))

            # حفظ الخط
            self._save_current_line()

            # إنهاء الرسم
            self._finish_drawing()

            return "line_complete"

    def _handle_multi_line_click(self, x: int, y: int) -> str:
        """
        معالجة النقر في وضع خطوط متعددة
        (نفس خط واحد لكن لا يمسح الخطوط السابقة)
        """
        if not self.is_drawing:
            self.is_drawing = True
            self.current_points = [(x, y)]
            self._draw_point_marker(x, y, is_start=True)
            return "point_a_set"
        else:
            self.current_points.append((x, y))
            self._save_current_line()
            self._finish_drawing()

            return "line_complete"


    def _draw_point_marker(self, x: int, y: int, is_start: bool = True) -> None:
        """
        رسم نقطة مرئية

        المُعاملات (Args):
            x, y: الإحداثيات
            is_start: هل هي نقطة بداية؟
        """
        if not self.scene:
            return

        color = QColor(0, 255, 255, 255) if is_start else QColor(255, 165, 0, 255)

        # دائرة خارجية
        outer = self.scene.addEllipse(
            x - 8, y - 8, 16, 16,
            QPen(color, 3),
            QColor(color.red(), color.green(), color.blue(), 100)
        )
        outer.setZValue(100)
        self.preview_items.append(outer)

        # نقطة داخلية
        inner = self.scene.addEllipse(
            x - 3, y - 3, 6, 6,
            QPen(QColor(255, 255, 255), 2),
            QColor(255, 255, 255, 255)
        )
        inner.setZValue(101)
        self.preview_items.append(inner)

    def _update_preview(self, x: int, y: int) -> None:
        """
        تحديث المعاينة المباشرة للخط

        المُعاملات (Args):
            x, y: موقع المؤشر الحالي
        """
        if not self.scene or not self.current_points:
            return

        # حذف عناصر المعاينة القديمة
        for item in self.preview_items:
            is_permanent = getattr(item, 'is_permanent', False)
            if not is_permanent:
                self.scene.removeItem(item)
        self.preview_items.clear()

        # إعادة رسم النقاط
        for i, point in enumerate(self.current_points):
            self._draw_point_marker(point[0], point[1], is_start=(i == 0))

        # رسم خط مؤقت من آخر نقطة إلى المؤشر
        if len(self.current_points) > 0:
            last_point = self.current_points[-1]
            line = self.scene.addLine(
                QLineF(last_point[0], last_point[1], x, y)
            )
            line.setPen(QPen(QColor(255, 255, 0, 180), 2))
            line.setZValue(99)
            self.preview_items.append(line)

    def _save_current_line(self) -> None:
        """حفظ الخط الحالي في القائمة."""
        if len(self.current_points) < 2:
            return

        # إنشاء LineData
        line_data = LineData(
            points=self.current_points.copy(),
            line_id=self.next_line_id
        )
        self.next_line_id += 1

        # حفظ في قائمة التراجع
        self.undo_stack.append(copy.deepcopy(self.lines))
        self.redo_stack.clear()

        # رسم الخط النهائي
        self._draw_final_line(line_data)

        # إضافة للقائمة
        self.lines.append(line_data)

        # إرسال callback
        if self.on_lines_changed_callback:
            self.on_lines_changed_callback(self.lines)

        logger.info(f"تم حفظ الخط #{line_data.line_id} بـ {len(line_data.points)} نقاط")

    def _draw_final_line(self, line_data: LineData) -> None:
        """
        رسم الخط النهائي

        المُعاملات (Args):
            line_data: بيانات الخط
        """
        if not self.scene:
            return

        # رسم الخط/المضلع
        if len(line_data.points) == 2:
            # خط عادي
            p1, p2 = line_data.points
            line_item = self.scene.addLine(
                QLineF(p1[0], p1[1], p2[0], p2[1])
            )
            line_pen = QPen(QColor(0, 255, 255, 220), 4)
            line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            line_item.setPen(line_pen)
            line_item.setZValue(50)
            line_item._line_id = line_data.line_id
            line_data.graphics_items.append(line_item)

            # إضافة سهم الاتجاه
            mid_x = (p1[0] + p2[0]) // 2
            mid_y = (p1[1] + p2[1]) // 2
            arrow = self.scene.addText("▶", QFont("Arial", 12, QFont.Weight.Bold))
            arrow.setDefaultTextColor(QColor(0, 255, 255))
            arrow.setPos(mid_x - 8, mid_y - 8)
            arrow.setZValue(51)
            arrow._line_id = line_data.line_id
            line_data.graphics_items.append(arrow)
        else:
            # مضلع
            polygon = QPolygonF([QPointF(p[0], p[1]) for p in line_data.points])
            polygon_item = QGraphicsPolygonItem(polygon)
            polygon_item.setPen(QPen(QColor(255, 165, 0, 220), 3))
            polygon_item.setBrush(QColor(255, 165, 0, 40))
            polygon_item.setZValue(50)
            polygon_item._line_id = line_data.line_id
            self.scene.addItem(polygon_item)
            line_data.graphics_items.append(polygon_item)

        # رسم النقاط
        for i, point in enumerate(line_data.points):
            is_start = (i == 0)
            color = QColor(0, 255, 0, 200) if is_start else QColor(255, 165, 0, 200)
            marker = self.scene.addEllipse(
                point[0] - 6, point[1] - 6, 12, 12,
                QPen(color, 2),
                QColor(color.red(), color.green(), color.blue(), 120)
            )
            marker.setZValue(52)
            marker._line_id = line_data.line_id
            line_data.graphics_items.append(marker)

    def _finish_drawing(self) -> None:
        """إنهاء عملية الرسم الحالية."""
        self.is_drawing = False
        self.current_points.clear()

        # حذف عناصر المعاينة
        for item in self.preview_items:
            if self.scene:
                self.scene.removeItem(item)
        self.preview_items.clear()

    def undo(self) -> None:
        """التراجع عن آخر عملية."""
        if not self.undo_stack:
            return

        # حفظ الحالة الحالية في redo
        self.redo_stack.append(copy.deepcopy(self.lines))

        # استرجاع الحالة السابقة
        self.lines = self.undo_stack.pop()

        # إعادة رسم كل شيء
        self._redraw_all_lines()

        logger.info("تم التراجع")

    def redo(self) -> None:
        """إعادة العملية."""
        if not self.redo_stack:
            return

        # حفظ الحالة الحالية في undo
        self.undo_stack.append(copy.deepcopy(self.lines))

        # استرجاع الحالة التالية
        self.lines = self.redo_stack.pop()

        # إعادة رسم
        self._redraw_all_lines()

        logger.info("تم الإعادة")

    def delete_selected_line(self) -> None:
        """حذف الخط المحدد."""
        if self.selected_line_id is None:
            return

        # حفظ في التراجع
        self.undo_stack.append(copy.deepcopy(self.lines))
        self.redo_stack.clear()

        # حذف من القائمة
        self.lines = [l for l in self.lines if l.line_id != self.selected_line_id]

        # إعادة رسم
        self._redraw_all_lines()
        deleted_id = self.selected_line_id
        self.selected_line_id = None

        if self.on_lines_changed_callback:
            self.on_lines_changed_callback(self.lines)

        logger.info(f"تم حذف الخط #{deleted_id}")

    def clear_all(self) -> None:
        """مسح جميع الخطوط."""
        if not self.lines:
            return

        # حفظ في التراجع
        self.undo_stack.append(copy.deepcopy(self.lines))
        self.redo_stack.clear()

        # حذف جميع العناصر من المشهد
        for line_data in self.lines:
            for item in line_data.graphics_items:
                if self.scene:
                    self.scene.removeItem(item)
            line_data.graphics_items.clear()

        self.lines.clear()
        self.selected_line_id = None

        # إنهاء الرسم الحالي
        self._finish_drawing()

        if self.on_lines_changed_callback:
            self.on_lines_changed_callback(self.lines)

        logger.info("تم مسح جميع الخطوط")

    def _clear_scene_items(self):
        if self.scene is None:
            return
        items_to_remove = []
        for item in self.scene.items():
            if hasattr(item, '_line_id'):
                items_to_remove.append(item)
        for item in items_to_remove:
            self.scene.removeItem(item)
        for line in self.lines:
            line.graphics_items = []

    def _redraw_all_lines(self) -> None:
        """إعادة رسم جميع الخطوط."""
        if not self.scene:
            return

        self._clear_scene_items()

        for line_data in self.lines:
            self._draw_final_line(line_data)

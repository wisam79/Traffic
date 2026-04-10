"""
ملف لوحة الفيديو - Video Panel
===============================
يُنشئ لوحة عرض الفيديو مع شريط العنوان وشريط الحالة.

المسؤوليات:
- إنشاء ZoomableGraphicsView
- إنشاء VideoDisplayManager
- إنشاء InteractiveLineDrawer
- إعداد تصفية الماوس
- إدارة شريط العنوان والحالة

المرتبط به:
- يُستورد من: main_window.py
- يحتوي على: video_player.py, drawing_modes.py, video_controllers.py
"""

import logging
import cv2
import numpy as np
from typing import Tuple, Callable, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QEvent, QObject, QTimer

from ui.video_player import ZoomableGraphicsView, VideoDisplayManager
from ui.video_controllers import VideoController
from ui.drawing_modes import AdvancedLineDrawer, DrawingMode, LineData
from ui.line_manager import LineManagerWidget
from ui.video_info_display import VideoInfoDisplay
from ui.styles import (
    VIDEO_HEADER_STYLE, VIDEO_DISPLAY_STYLE, STATUS_BAR_STYLE,
    STATUS_LIVE_STYLE, STATUS_STOPPED_STYLE,
    STATUS_LINE_SET_STYLE, STATUS_LINE_UNSET_STYLE,
    INSTRUCTION_DEFAULT_STYLE, INSTRUCTION_ACTIVE_STYLE,
    INSTRUCTION_SUCCESS_STYLE, INSTRUCTION_ERROR_STYLE,
    COORDS_STYLE
)
from ui.themes import (
    ButtonStyles, Spacing, Typography, ThemeColors, MiscStyles, StatusBarStyles
)

logger = logging.getLogger(__name__)


class MouseFilter(QObject):
    """
    تصفية أحداث الماوس
    ====================
    يُحول إحداثيات widget إلى إحداثيات scene.
    """

    def __init__(self, parent, click_callback: Callable, move_callback: Callable):
        super().__init__(parent)
        self.click_callback = click_callback
        self.move_callback = move_callback
        self.drawing_enabled = True

    def eventFilter(self, obj, event) -> bool:
        parent = self.parent()
        if not isinstance(parent, ZoomableGraphicsView):
            return False

        if event.type() == QEvent.Type.MouseButtonPress:
            if self.drawing_enabled:
                scene_pos = parent.mapToScene(event.pos())
                x, y = int(scene_pos.x()), int(scene_pos.y())
                self.click_callback(x, y)
                return True
            return False

        elif event.type() == QEvent.Type.MouseMove:
            scene_pos = parent.mapToScene(event.pos())
            x, y = int(scene_pos.x()), int(scene_pos.y())
            self.move_callback(x, y)

        return False


class VideoPanel(QWidget):
    """
    لوحة الفيديو الرئيسية
    ======================
    تحتوي على شريط العنوان ومنطقة عرض الفيديو وشريط الحالة فقط.
    عناصر التحكم في الصورة والتسجيل نُقلت إلى VideoToolbar.
    """

    def __init__(self):
        super().__init__()

        self.video_display = None
        self.video_manager = None
        self.video_controller = VideoController()
        self.advanced_line_drawer = AdvancedLineDrawer()
        self.line_manager_widget = LineManagerWidget()
        self.line_manager_widget.hide()
        self.video_info_display = VideoInfoDisplay()
        self.video_info_display.hide()

        self.btn_zoom_in = None
        self.btn_zoom_out = None
        self.btn_reset_view = None
        self.lbl_fps = None
        self.lbl_status_indicator = None
        self.btn_manage_lines = None

        self.lbl_instruction = None
        self.lbl_coords = None
        self.lbl_line_status = None

        self._mouse_filter = None
        self._line_callback = None
        self._sent_line_coords: dict = {}
        self._toast_timer = QTimer()
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._hide_toast)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        header_bar = self._create_video_header()
        layout.addWidget(header_bar)

        self.video_display = ZoomableGraphicsView()
        self.video_display.setObjectName("VideoDisplay")
        self.video_display.setStyleSheet(VIDEO_DISPLAY_STYLE)
        self.video_display.setMouseTracking(True)
        layout.addWidget(self.video_display, stretch=1)

        layout.addWidget(self.video_info_display)
        layout.addWidget(self.line_manager_widget)

        status_bar = self._create_status_bar()
        layout.addWidget(status_bar)

        self.video_manager = VideoDisplayManager(self.video_display)
        self.advanced_line_drawer.set_scene(self.video_manager.scene)
        self.advanced_line_drawer.on_lines_changed_callback = self._on_lines_changed

        self.line_manager_widget.lst_lines.currentRowChanged.connect(
            self._on_line_selected
        )
        self.line_manager_widget.cmb_mode.currentIndexChanged.connect(
            self._on_drawing_mode_changed
        )
        self.line_manager_widget.btn_undo.clicked.connect(
            lambda: self.advanced_line_drawer.undo()
        )
        self.line_manager_widget.btn_redo.clicked.connect(
            lambda: self.advanced_line_drawer.redo()
        )
        self.line_manager_widget.btn_delete.clicked.connect(
            lambda: self.advanced_line_drawer.delete_selected_line()
        )
        self.line_manager_widget.btn_clear_all.clicked.connect(
            lambda: self.advanced_line_drawer.clear_all()
        )

        self._setup_mouse_handling()

    def show_video_info(self, show: bool) -> None:
        if show:
            self.video_info_display.show()
        else:
            self.video_info_display.hide()

    def _create_video_header(self) -> QWidget:
        header = QWidget()
        header.setStyleSheet(VIDEO_HEADER_STYLE)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(Spacing.MD, Spacing.XS, Spacing.MD, Spacing.XS)

        title = QLabel("📹 بث مباشر")
        layout.addWidget(title)

        layout.addStretch()

        self.lbl_status_indicator = QLabel("⚫ متوقف")
        self.lbl_status_indicator.setStyleSheet(STATUS_STOPPED_STYLE)
        layout.addWidget(self.lbl_status_indicator)

        sep1 = QLabel("|")
        sep1.setStyleSheet(MiscStyles.header_separator())
        layout.addWidget(sep1)

        self.lbl_fps = QLabel("FPS: --")
        self.lbl_fps.setStyleSheet(MiscStyles.fps_label())
        layout.addWidget(self.lbl_fps)

        sep2 = QLabel("|")
        sep2.setStyleSheet(MiscStyles.header_separator())
        layout.addWidget(sep2)

        self.btn_zoom_in = QPushButton("➕")
        self.btn_zoom_in.setFixedSize(32, 26)
        self.btn_zoom_in.setToolTip("تكبير")
        self.btn_zoom_in.clicked.connect(lambda: self.video_manager.zoom_in())
        layout.addWidget(self.btn_zoom_in)

        self.btn_zoom_out = QPushButton("➖")
        self.btn_zoom_out.setFixedSize(32, 26)
        self.btn_zoom_out.setToolTip("تصغير")
        self.btn_zoom_out.clicked.connect(lambda: self.video_manager.zoom_out())
        layout.addWidget(self.btn_zoom_out)

        self.btn_reset_view = QPushButton("⟲")
        self.btn_reset_view.setFixedSize(32, 26)
        self.btn_reset_view.setToolTip("إعادة تعيين العرض")
        self.btn_reset_view.clicked.connect(lambda: self.video_manager.reset_view())
        layout.addWidget(self.btn_reset_view)

        sep3 = QLabel("|")
        sep3.setStyleSheet(MiscStyles.header_separator())
        layout.addWidget(sep3)

        self.btn_manage_lines = QPushButton("📏 الخطوط")
        self.btn_manage_lines.setFixedHeight(26)
        self.btn_manage_lines.setStyleSheet(MiscStyles.tool_button())
        self.btn_manage_lines.clicked.connect(self._toggle_line_manager)
        layout.addWidget(self.btn_manage_lines)

        return header

    def _create_status_bar(self) -> QWidget:
        status = QWidget()
        status.setStyleSheet(STATUS_BAR_STYLE)
        layout = QHBoxLayout(status)
        layout.setContentsMargins(Spacing.MD, Spacing.XS, Spacing.MD, Spacing.XS)

        self.lbl_instruction = QLabel("💡 انقر مرتين على الفيديو لرسم خط العد")
        self.lbl_instruction.setStyleSheet(INSTRUCTION_DEFAULT_STYLE)
        layout.addWidget(self.lbl_instruction)

        layout.addStretch()

        self.lbl_coords = QLabel("المؤشر: (0, 0)")
        self.lbl_coords.setStyleSheet(COORDS_STYLE)
        layout.addWidget(self.lbl_coords)

        self.lbl_line_status = QLabel("الخط: لم يُحدد")
        self.lbl_line_status.setStyleSheet(STATUS_LINE_UNSET_STYLE)
        layout.addWidget(self.lbl_line_status)

        return status

    def _setup_mouse_handling(self) -> None:
        self._mouse_filter = MouseFilter(
            self.video_display,
            click_callback=self._on_mouse_click,
            move_callback=self._on_mouse_move
        )
        self.video_display.viewport().installEventFilter(self._mouse_filter)

    def _on_mouse_move(self, x: int, y: int) -> None:
        self.lbl_coords.setText(f"المؤشر: ({x}, {y})")

    def _on_mouse_click(self, x: int, y: int) -> None:
        result = self.advanced_line_drawer.handle_click(x, y)

        if result == "point_a_set":
            self.lbl_instruction.setText("🎯 الآن انقر للنقطة B (نهاية الخط)")
            self.lbl_instruction.setStyleSheet(INSTRUCTION_ACTIVE_STYLE)
        elif result == "line_complete":
            self.lbl_instruction.setText("✅ تم إضافة الخط! انقر لرسم خط آخر")
            self.lbl_instruction.setStyleSheet(INSTRUCTION_SUCCESS_STYLE)
        elif result == "outside_frame":
            self.lbl_instruction.setText("⚠️ انقر داخل إطار الفيديو")
            self.lbl_instruction.setStyleSheet(INSTRUCTION_ERROR_STYLE)

    def _toggle_line_manager(self) -> None:
        if self.line_manager_widget.isVisible():
            self.line_manager_widget.hide()
            self.btn_manage_lines.setText("📏 الخطوط")
        else:
            self.line_manager_widget.show()
            self.btn_manage_lines.setText("📐 إخفاء")

    def _on_lines_changed(self, lines) -> None:
        self.line_manager_widget.update_line_list(lines)

        if self._line_callback and lines:
            current_coords = {}
            for line in lines:
                if len(line.points) >= 2:
                    current_coords[line.line_id] = (line.points[0], line.points[-1])

            for line_id, (point_a, point_b) in current_coords.items():
                if self._sent_line_coords.get(line_id) != (point_a, point_b):
                    self._line_callback(line_id, point_a, point_b)

            for line_id in list(self._sent_line_coords):
                if line_id not in current_coords:
                    self._line_callback(line_id, None, None)

            self._sent_line_coords = current_coords

    def _on_line_selected(self, row: int) -> None:
        line_id = self.line_manager_widget.get_selected_line_id()
        self.advanced_line_drawer.selected_line_id = line_id

    def _on_drawing_mode_changed(self) -> None:
        mode = self.line_manager_widget.get_selected_drawing_mode()
        if mode is not None:
            self.advanced_line_drawer.set_drawing_mode(mode)

    def set_line_callback(self, callback: Callable) -> None:
        self._line_callback = callback

    def on_brightness_change(self, value: int) -> None:
        self.video_controller.adjuster.set_brightness(value)

    def on_contrast_change(self, value: int) -> None:
        self.video_controller.adjuster.set_contrast(value / 100.0)

    def on_saturation_change(self, value: int) -> None:
        self.video_controller.adjuster.set_saturation(value / 100.0)

    def on_reset_adjust(self) -> None:
        self.video_controller.adjuster.reset()

    def on_screenshot(self) -> int:
        bgr_frame = self.video_manager.last_bgr_frame if self.video_manager else None
        if bgr_frame is not None:
            filepath = self.video_controller.recorder.take_screenshot(bgr_frame)
            count = self.video_controller.recorder.total_screenshots
            self._show_toast("📷 تم التقاط الصورة")
            logger.info(f"تم التقاط صورة: {filepath}")
            return count
        return 0

    def on_record(self) -> bool:
        if not self.video_controller.recorder.is_recording:
            bgr_frame = self.video_manager.last_bgr_frame if self.video_manager else None
            if bgr_frame is not None:
                success = self.video_controller.recorder.start_recording(bgr_frame)
                if success:
                    self._show_toast("⏺ بدء التسجيل")
                return success
        else:
            self.video_controller.recorder.stop_recording()
            self._show_toast("⏹ تم إيقاف التسجيل")
            return True
        return False

    def _show_toast(self, message: str, duration_ms: int = 2000) -> None:
        self.lbl_instruction.setText(message)
        self.lbl_instruction.setStyleSheet(
            f"color: {ThemeColors.SUCCESS}; font-size: {Typography.SIZE_SM}px; font-weight: bold;"
        )
        self._toast_timer.start(duration_ms)

    def _hide_toast(self) -> None:
        self.lbl_instruction.setText("💡 انقر مرتين على الفيديو لرسم خط العد")
        self.lbl_instruction.setStyleSheet(INSTRUCTION_DEFAULT_STYLE)



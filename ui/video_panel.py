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
- دمج متحكمات الفيديو الجديدة

المرتبط به:
- يُستورد من: main_window.py
- يحتوي على: video_player.py, line_drawer.py, video_controllers.py
"""

import logging
from typing import Tuple, Callable, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QGroupBox, QFrame
)
from PySide6.QtCore import Qt, QEvent, QObject

from ui.video_player import ZoomableGraphicsView, VideoDisplayManager
from ui.video_controllers import VideoController
from ui.drawing_modes import AdvancedLineDrawer, DrawingMode, LineData
from ui.line_manager import LineManagerWidget
from ui.video_info_display import VideoInfoDisplay
from ui.styles import (
    VIDEO_HEADER_STYLE, VIDEO_DISPLAY_STYLE, STATUS_BAR_STYLE,
    CONTROL_PANEL_STYLE, STATUS_LIVE_STYLE, STATUS_STOPPED_STYLE,
    STATUS_LINE_SET_STYLE, STATUS_LINE_UNSET_STYLE,
    INSTRUCTION_DEFAULT_STYLE, INSTRUCTION_ACTIVE_STYLE,
    INSTRUCTION_SUCCESS_STYLE, INSTRUCTION_ERROR_STYLE,
    COORDS_STYLE, RECORDING_ACTIVE_STYLE
)
from ui.themes import (
    ButtonStyles, Spacing, Typography, ThemeColors,
    InputStyles, MiscStyles
)

logger = logging.getLogger(__name__)


class MouseFilter(QObject):
    """
    تصفية أحداث الماوس
    ====================
    intercepts mouse events on the graphics view viewport.
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
    تحتوي على:
    - شريط العنوان مع أزرار التكبير
    - منطقة عرض الفيديو
    - شريط الحالة مع الإحداثيات
    """

    def __init__(self):
        super().__init__()

        self.video_display = None
        self.video_manager = None
        self.line_drawer = None

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

        self.btn_play_pause = None
        self.btn_stop = None
        self.btn_speed_up = None
        self.btn_slow_down = None
        self.lbl_speed = None
        self.lbl_recording = None

        self.slider_brightness = None
        self.slider_contrast = None
        self.slider_saturation = None
        self.lbl_brightness_val = None
        self.lbl_contrast_val = None
        self.lbl_saturation_val = None
        self.btn_reset_adjust = None

        self.btn_screenshot = None
        self.btn_record = None
        self.lbl_screenshot_count = None
        self.lbl_recording_count = None

        self.lbl_instruction = None
        self.lbl_coords = None
        self.lbl_line_status = None

        self.btn_manage_lines = None

        self._mouse_filter = None
        self._line_callback = None

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

        controls_panel = self._create_video_controls()
        layout.addWidget(controls_panel)

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
        sep1.setStyleSheet(f"color: {ThemeColors.BORDER_DARK}; font-size: {Typography.SIZE_BASE}px;")
        layout.addWidget(sep1)

        self.lbl_fps = QLabel("FPS: --")
        self.lbl_fps.setStyleSheet(f"color: {ThemeColors.SUCCESS}; font-size: {Typography.SIZE_SM}px; font-weight: bold; font-family: {Typography.FONT_FAMILY_MONO};")
        layout.addWidget(self.lbl_fps)

        sep2 = QLabel("|")
        sep2.setStyleSheet(f"color: {ThemeColors.BORDER_DARK}; font-size: {Typography.SIZE_BASE}px;")
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
        sep3.setStyleSheet(f"color: {ThemeColors.BORDER_DARK}; font-size: {Typography.SIZE_BASE}px;")
        layout.addWidget(sep3)

        self.btn_manage_lines = QPushButton("📏 الخطوط")
        self.btn_manage_lines.setFixedHeight(26)
        self.btn_manage_lines.setStyleSheet(MiscStyles.tool_button())
        self.btn_manage_lines.clicked.connect(self._toggle_line_manager)
        layout.addWidget(self.btn_manage_lines)

        return header

    def _create_video_controls(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(CONTROL_PANEL_STYLE)
        main_layout = QVBoxLayout(panel)
        main_layout.setSpacing(Spacing.XS)
        main_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)

        adjust_row = QHBoxLayout()
        adjust_row.setSpacing(Spacing.LG)

        self.slider_brightness, self.lbl_brightness_val = self._create_slider_row(
            adjust_row, "☀️", -100, 100, 0, self._on_brightness_change
        )
        self.slider_contrast, self.lbl_contrast_val = self._create_slider_row(
            adjust_row, "◐", 0, 300, 100, self._on_contrast_change
        )
        self.slider_saturation, self.lbl_saturation_val = self._create_slider_row(
            adjust_row, "🎨", 0, 300, 100, self._on_saturation_change
        )

        self.btn_reset_adjust = QPushButton("↺")
        self.btn_reset_adjust.setFixedSize(28, 28)
        self.btn_reset_adjust.setToolTip("إعادة تعيين الصورة")
        self.btn_reset_adjust.setStyleSheet(MiscStyles.tool_button())
        self.btn_reset_adjust.clicked.connect(self._on_reset_adjust)
        adjust_row.addWidget(self.btn_reset_adjust)

        main_layout.addLayout(adjust_row)

        media_row = QHBoxLayout()
        media_row.setSpacing(Spacing.SM)

        self.btn_screenshot = QPushButton("📷 تصوير")
        self.btn_screenshot.setFixedHeight(30)
        self.btn_screenshot.setStyleSheet(ButtonStyles.secondary_button())
        self.btn_screenshot.clicked.connect(self._on_screenshot)
        media_row.addWidget(self.btn_screenshot)

        self.btn_record = QPushButton("⏺ تسجيل")
        self.btn_record.setFixedHeight(30)
        self.btn_record.setStyleSheet(ButtonStyles.secondary_button())
        self.btn_record.clicked.connect(self._on_record)
        media_row.addWidget(self.btn_record)

        media_row.addStretch()

        self.lbl_screenshot_count = QLabel("صور: 0")
        self.lbl_screenshot_count.setStyleSheet(f"font-size: {Typography.SIZE_XS}px; color: {ThemeColors.TEXT_MUTED};")
        media_row.addWidget(self.lbl_screenshot_count)

        self.lbl_recording_count = QLabel("تسجيلات: 0")
        self.lbl_recording_count.setStyleSheet(f"font-size: {Typography.SIZE_XS}px; color: {ThemeColors.TEXT_MUTED};")
        media_row.addWidget(self.lbl_recording_count)

        self.lbl_recording = QLabel("")
        self.lbl_recording.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(self.lbl_recording)

        main_layout.addLayout(media_row)

        return panel

    def _create_slider_row(self, parent_layout, icon: str, min_val: int, max_val: int, default: int, callback) -> tuple:
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedWidth(20)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        parent_layout.addWidget(icon_lbl)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        slider.setStyleSheet(InputStyles.slider())
        slider.valueChanged.connect(callback)
        parent_layout.addWidget(slider)

        val_lbl = QLabel(str(default))
        val_lbl.setFixedWidth(32)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: {Typography.SIZE_XS}px; font-family: {Typography.FONT_FAMILY_MONO};")
        parent_layout.addWidget(val_lbl)

        return slider, val_lbl

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
            first_line = lines[0]
            if len(first_line.points) >= 2:
                self._line_callback(first_line.points[0], first_line.points[-1])

    def _on_line_selected(self, row: int) -> None:
        line_id = self.line_manager_widget.get_selected_line_id()
        self.advanced_line_drawer.selected_line_id = line_id

    def _on_drawing_mode_changed(self) -> None:
        mode = self.line_manager_widget.get_selected_drawing_mode()
        if mode is not None:
            self.advanced_line_drawer.set_drawing_mode(mode)

    def set_line_callback(self, callback: Callable) -> None:
        self._line_callback = callback

    def _on_brightness_change(self, value: int) -> None:
        self.video_controller.adjuster.set_brightness(value)
        self.lbl_brightness_val.setText(str(value))

    def _on_contrast_change(self, value: int) -> None:
        self.video_controller.adjuster.set_contrast(value / 100.0)
        self.lbl_contrast_val.setText(str(value))

    def _on_saturation_change(self, value: int) -> None:
        self.video_controller.adjuster.set_saturation(value / 100.0)
        self.lbl_saturation_val.setText(str(value))

    def _on_reset_adjust(self) -> None:
        self.video_controller.adjuster.reset()

        self.slider_brightness.blockSignals(True)
        self.slider_contrast.blockSignals(True)
        self.slider_saturation.blockSignals(True)

        self.slider_brightness.setValue(0)
        self.slider_contrast.setValue(100)
        self.slider_saturation.setValue(100)

        self.lbl_brightness_val.setText("0")
        self.lbl_contrast_val.setText("100")
        self.lbl_saturation_val.setText("100")

        self.slider_brightness.blockSignals(False)
        self.slider_contrast.blockSignals(False)
        self.slider_saturation.blockSignals(False)

    def _on_screenshot(self) -> None:
        bgr_frame = self._get_current_frame_as_bgr()
        if bgr_frame is not None:
            filepath = self.video_controller.recorder.take_screenshot(bgr_frame)

            count = self.video_controller.recorder.total_screenshots
            self.lbl_screenshot_count.setText(f"صور: {count}")

            logger.info(f"تم التقاط صورة: {filepath}")

    def _get_current_frame_as_bgr(self):
        if not self.video_manager.pixmap_item:
            return None

        import cv2
        import numpy as np

        pixmap = self.video_manager.pixmap_item.pixmap()
        q_image = pixmap.toImage()
        width = q_image.width()
        height = q_image.height()
        bytes_per_line = q_image.bytesPerLine()
        ptr = q_image.bits()
        ptr.setsize(bytes_per_line * height)
        arr = np.array(ptr).reshape(height, width, 4)
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)

    def _on_record(self) -> None:
        if not self.video_controller.recorder.is_recording:
            if self.video_manager.pixmap_item:
                bgr_frame = self._get_current_frame_as_bgr()

                if bgr_frame is not None:
                    success = self.video_controller.recorder.start_recording(bgr_frame)

                    if success:
                        self.btn_record.setText("⏹ إيقاف")
                        self.btn_record.setStyleSheet(ButtonStyles.danger_button())
                        self.lbl_recording.setText("🔴 تسجيل...")
                        self.lbl_recording.setStyleSheet(RECORDING_ACTIVE_STYLE)

                        count = self.video_controller.recorder.total_recordings
                        self.lbl_recording_count.setText(f"تسجيلات: {count}")
        else:
            self.video_controller.recorder.stop_recording()
            self.btn_record.setText("⏺ تسجيل")
            self.btn_record.setStyleSheet(ButtonStyles.secondary_button())
            self.lbl_recording.setText("")

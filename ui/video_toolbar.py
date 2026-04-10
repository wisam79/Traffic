"""
شريط أدوات الفيديو الجانبي - Video Toolbar
=============================================
عمود جانبي أيمن يحتوي على عناصر تحكم الصورة والتسجيل.
مُصمم مضغوط ليناسب بدون تمرير.

المرتبط به:
- يُستورد من: main_window.py
"""

import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QGroupBox
)
from PySide6.QtCore import Qt, Signal

from ui.styles import CONTROL_PANEL_STYLE, RECORDING_ACTIVE_STYLE
from ui.themes import (
    ButtonStyles, Spacing, Typography, ThemeColors,
    InputStyles, MiscStyles
)
from ui.interval_panel import IntervalPanel

logger = logging.getLogger(__name__)


class VideoToolbar(QWidget):
    """
    شريط أدوات الفيديو الجانبي الأيمن
    ====================================
    مُصمم مضغوط: منزلقات أفقية + أزرار مدمجة.
    """

    screenshot_requested = Signal()
    record_requested = Signal()
    reset_adjust_requested = Signal()
    brightness_changed = Signal(int)
    contrast_changed = Signal(int)
    saturation_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(160)

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
        self.lbl_recording = None

        self.interval_panel = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(Spacing.XS)
        layout.setContentsMargins(Spacing.XS, Spacing.XS, Spacing.XS, Spacing.XS)

        adjust_group = QGroupBox("الصورة")
        adjust_group.setStyleSheet(CONTROL_PANEL_STYLE)
        al = QVBoxLayout(adjust_group)
        al.setSpacing(2)
        al.setContentsMargins(6, 14, 6, 6)

        self.slider_brightness, self.lbl_brightness_val = self._create_slider(
            al, "☀️", -100, 100, 0
        )
        self.slider_brightness.valueChanged.connect(self.brightness_changed.emit)

        self.slider_contrast, self.lbl_contrast_val = self._create_slider(
            al, "◐", 0, 300, 100
        )
        self.slider_contrast.valueChanged.connect(self.contrast_changed.emit)

        self.slider_saturation, self.lbl_saturation_val = self._create_slider(
            al, "🎨", 0, 300, 100
        )
        self.slider_saturation.valueChanged.connect(self.saturation_changed.emit)

        self.btn_reset_adjust = QPushButton("↺ إعادة")
        self.btn_reset_adjust.setStyleSheet(MiscStyles.tool_button())
        self.btn_reset_adjust.setToolTip("إعادة تعيين الصورة")
        self.btn_reset_adjust.clicked.connect(self.reset_adjust_requested.emit)
        al.addWidget(self.btn_reset_adjust)

        layout.addWidget(adjust_group)

        media_group = QGroupBox("الوسائط")
        media_group.setStyleSheet(CONTROL_PANEL_STYLE)
        ml = QVBoxLayout(media_group)
        ml.setSpacing(2)
        ml.setContentsMargins(6, 14, 6, 6)

        self.btn_screenshot = QPushButton("📷 تصوير")
        self.btn_screenshot.setStyleSheet(ButtonStyles.secondary_button())
        self.btn_screenshot.setToolTip("التقاط صورة (Ctrl+S)")
        self.btn_screenshot.clicked.connect(self.screenshot_requested.emit)
        ml.addWidget(self.btn_screenshot)

        self.btn_record = QPushButton("⏺ تسجيل")
        self.btn_record.setStyleSheet(ButtonStyles.secondary_button())
        self.btn_record.setToolTip("بدء/إيقاف تسجيل")
        self.btn_record.clicked.connect(self.record_requested.emit)
        ml.addWidget(self.btn_record)

        counts_row = QHBoxLayout()
        self.lbl_screenshot_count = QLabel("0")
        self.lbl_screenshot_count.setToolTip("عدد الصور")
        self.lbl_screenshot_count.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: {Typography.SIZE_XS}px;")
        counts_row.addWidget(self.lbl_screenshot_count)
        counts_row.addStretch()
        self.lbl_recording_count = QLabel("0")
        self.lbl_recording_count.setToolTip("عدد التسجيلات")
        self.lbl_recording_count.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: {Typography.SIZE_XS}px;")
        counts_row.addWidget(self.lbl_recording_count)
        ml.addLayout(counts_row)

        self.lbl_recording = QLabel("")
        self.lbl_recording.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ml.addWidget(self.lbl_recording)

        layout.addWidget(media_group)

        self.interval_panel = IntervalPanel()
        layout.addWidget(self.interval_panel)

        layout.addStretch()

    def _create_slider(self, parent_layout, icon: str, min_val: int, max_val: int, default: int) -> tuple:
        row = QHBoxLayout()
        row.setSpacing(2)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedWidth(18)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(icon_lbl)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        slider.setStyleSheet(InputStyles.slider())
        row.addWidget(slider, stretch=1)

        val_lbl = QLabel(str(default))
        val_lbl.setFixedWidth(26)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: {Typography.SIZE_XS}px; font-family: {Typography.FONT_FAMILY_MONO};")
        row.addWidget(val_lbl)

        parent_layout.addLayout(row)
        return slider, val_lbl

    def set_recording_active(self, active: bool) -> None:
        if active:
            self.btn_record.setText("⏹ إيقاف")
            self.btn_record.setStyleSheet(ButtonStyles.danger_button())
            self.lbl_recording.setText("🔴 تسجيل...")
            self.lbl_recording.setStyleSheet(RECORDING_ACTIVE_STYLE)
        else:
            self.btn_record.setText("⏺ تسجيل")
            self.btn_record.setStyleSheet(ButtonStyles.secondary_button())
            self.lbl_recording.setText("")

    def reset_sliders(self, brightness: int = 0, contrast: int = 100, saturation: int = 100) -> None:
        self.slider_brightness.blockSignals(True)
        self.slider_contrast.blockSignals(True)
        self.slider_saturation.blockSignals(True)

        self.slider_brightness.setValue(brightness)
        self.slider_contrast.setValue(contrast)
        self.slider_saturation.setValue(saturation)

        self.lbl_brightness_val.setText(str(brightness))
        self.lbl_contrast_val.setText(str(contrast))
        self.lbl_saturation_val.setText(str(saturation))

        self.slider_brightness.blockSignals(False)
        self.slider_contrast.blockSignals(False)
        self.slider_saturation.blockSignals(False)

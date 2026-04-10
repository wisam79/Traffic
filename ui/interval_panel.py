"""
لوحة الفترات الزمنية - Interval Panel
========================================
ويدجة مضغوطة لإدارة فترات العد — مصممة لتناسب شريط الأدوات الجانبي (160px).

المسؤوليات:
- اختيار فترة العد (كامل، 5 دقائق، مخصص...)
- عرض تقدم الفترة الحالية مع شريط تقدم
- عرض سجل الفترات المنتهية كقائمة مضغوطة

المرتبط به:
- يُستورد من: ui/video_toolbar.py
- يرتبط بـ: engine/interval_counter.py
"""

import logging
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QComboBox, QLabel, QProgressBar, QPushButton,
    QListWidget, QListWidgetItem, QSpinBox, QFrame
)
from PySide6.QtCore import Qt, QTimer

from ui.styles import CONTROL_PANEL_STYLE
from ui.themes import (
    InputStyles, Spacing, Typography,
    ThemeColors, ButtonStyles
)
from engine.interval_counter import IntervalCounter, IntervalRecord
from ui.interval_report_dialog import IntervalReportDialog

logger = logging.getLogger(__name__)


class IntervalPanel(QWidget):
    """
    لوحة إدارة الفترات الزمنية المضغوطة
    =====================================
    مصممة لتناسب العمود الجانبي الأيمن بعرض 160px.
    """

    def __init__(self):
        super().__init__()
        self._interval_counter: Optional[IntervalCounter] = None
        self.on_interval_changed: Optional[Callable[[int], None]] = None

        self.cmb_interval = None
        self.spin_custom = None
        self.lbl_elapsed = None
        self.progress_bar = None
        self.lst_history = None
        self.btn_reset_intervals = None
        self.btn_report = None
        self._report_dialog = None

        self._setup_ui()

        self._progress_timer = QTimer()
        self._progress_timer.timeout.connect(self._update_progress)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("فترة العد")
        group.setStyleSheet(CONTROL_PANEL_STYLE)
        gl = QVBoxLayout(group)
        gl.setSpacing(3)
        gl.setContentsMargins(4, 14, 4, 4)

        self.cmb_interval = QComboBox()
        self.cmb_interval.setStyleSheet(InputStyles.combo_box())
        for seconds, label in IntervalCounter.PRESETS:
            self.cmb_interval.addItem(label, seconds)
        self.cmb_interval.addItem("مخصص", -1)
        self.cmb_interval.currentIndexChanged.connect(self._on_interval_selected)
        gl.addWidget(self.cmb_interval)

        custom_row = QHBoxLayout()
        custom_row.setSpacing(2)

        custom_lbl = QLabel("د:")
        custom_lbl.setFixedWidth(14)
        custom_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: {Typography.SIZE_XS}px;")
        custom_row.addWidget(custom_lbl)

        self.spin_custom = QSpinBox()
        self.spin_custom.setRange(1, 999)
        self.spin_custom.setValue(5)
        self.spin_custom.setSuffix(" د")
        self.spin_custom.setStyleSheet(InputStyles.spin_box())
        self.spin_custom.setEnabled(False)
        self.spin_custom.valueChanged.connect(self._on_custom_changed)
        custom_row.addWidget(self.spin_custom, stretch=1)

        gl.addLayout(custom_row)

        self.lbl_elapsed = QLabel("--:-- / --:--")
        self.lbl_elapsed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_elapsed.setStyleSheet(
            f"color: {ThemeColors.ACCENT_CYAN}; "
            f"font-family: {Typography.FONT_FAMILY_MONO}; "
            f"font-size: {Typography.SIZE_SM}px; "
            f"font-weight: bold;"
        )
        gl.addWidget(self.lbl_elapsed)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {ThemeColors.BACKGROUND_MEDIUM};
                border: 1px solid {ThemeColors.BORDER_DARK};
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ThemeColors.ACCENT_CYAN}, stop:1 {ThemeColors.INFO});
                border-radius: 1px;
            }}
            """
        )
        gl.addWidget(self.progress_bar)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {ThemeColors.BORDER_DARK};")
        gl.addWidget(sep)

        hist_label = QLabel("السجل")
        hist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hist_label.setStyleSheet(
            f"color: {ThemeColors.TEXT_MUTED}; "
            f"font-size: {Typography.SIZE_XS}px; "
            f"font-weight: bold;"
        )
        gl.addWidget(hist_label)

        self.lst_history = QListWidget()
        self.lst_history.setMaximumHeight(90)
        self.lst_history.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {ThemeColors.BACKGROUND_DARK};
                border: 1px solid {ThemeColors.BORDER_DARK};
                border-radius: 4px;
                font-size: {Typography.SIZE_XS}px;
                color: {ThemeColors.TEXT_PRIMARY};
                padding: 2px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 2px 4px;
                border-bottom: 1px solid {ThemeColors.BORDER_DARK};
                border-radius: 2px;
            }}
            QListWidget::item:selected {{
                background-color: {ThemeColors.BACKGROUND_LIGHT};
            }}
            """
        )
        gl.addWidget(self.lst_history)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(2)

        self.btn_report = QPushButton("📊 تقرير")
        self.btn_report.setStyleSheet(ButtonStyles.info_button())
        self.btn_report.setFixedHeight(22)
        self.btn_report.clicked.connect(self._on_show_report)
        buttons_row.addWidget(self.btn_report)

        self.btn_reset_intervals = QPushButton("🔄 مسح")
        self.btn_reset_intervals.setStyleSheet(ButtonStyles.secondary_button())
        self.btn_reset_intervals.setFixedHeight(22)
        self.btn_reset_intervals.clicked.connect(self._on_reset)
        buttons_row.addWidget(self.btn_reset_intervals)

        gl.addLayout(buttons_row)

        layout.addWidget(group)

    def set_interval_counter(self, counter: IntervalCounter) -> None:
        self._interval_counter = counter

    def _on_interval_selected(self, index: int) -> None:
        seconds = self.cmb_interval.itemData(index)
        is_custom = (seconds == -1)
        self.spin_custom.setEnabled(is_custom)

        if is_custom:
            self._on_custom_changed(self.spin_custom.value())
        else:
            if self.on_interval_changed:
                self.on_interval_changed(seconds)

        self.progress_bar.setVisible(seconds != 0)

    def _on_custom_changed(self, minutes: int) -> None:
        if self.on_interval_changed:
            self.on_interval_changed(minutes * 60)

    def _on_reset(self) -> None:
        if self._interval_counter:
            self._interval_counter.reset()
        self.lst_history.clear()
        logger.info("تم مسح سجل الفترات")

    def _on_show_report(self) -> None:
        if not self._interval_counter:
            return

        records = self._interval_counter.get_history()
        if not records:
            return

        if self._report_dialog is None or not self._report_dialog.isVisible():
            self._report_dialog = IntervalReportDialog(self)
            self._report_dialog.show()

        self._report_dialog.update_data(
            records=records,
            interval_seconds=self._interval_counter.get_interval(),
            direction_label=self._get_direction_label()
        )
        self._report_dialog.raise_()
        self._report_dialog.activateWindow()

    def _get_direction_label(self) -> str:
        if not self._interval_counter:
            return ""
        interval = self._interval_counter.get_interval()
        for seconds, label in IntervalCounter.PRESETS:
            if seconds == interval:
                return label
        return f"مخصص ({interval // 60} دقيقة)"

    def on_interval_completed(self, record: IntervalRecord) -> None:
        total = record.stats.get('total', 0)
        duration = IntervalCounter.format_seconds(record.duration_seconds)
        in_c = record.stats.get('in_count', 0)
        out_c = record.stats.get('out_count', 0)

        text = f"#{record.index + 1}  {total} ({in_c}↑ {out_c}↓)  {duration}"

        item = QListWidgetItem(text)
        if total >= 50:
            item.setForeground(self._qcolor(ThemeColors.SUCCESS))
        elif total >= 20:
            item.setForeground(self._qcolor(ThemeColors.INFO))
        elif total > 0:
            item.setForeground(self._qcolor(ThemeColors.WARNING))
        else:
            item.setForeground(self._qcolor(ThemeColors.TEXT_MUTED))

        self.lst_history.addItem(item)
        self.lst_history.scrollToBottom()

    def _qcolor(self, hex_color: str):
        from PySide6.QtGui import QColor
        return QColor(hex_color)

    def _update_progress(self) -> None:
        if not self._interval_counter or not self._interval_counter.is_active:
            return

        interval = self._interval_counter.get_interval()
        elapsed = self._interval_counter.get_elapsed()

        if interval == IntervalCounter.INTERVAL_NONE:
            total_elapsed = self._interval_counter.get_total_elapsed()
            self.lbl_elapsed.setText(IntervalCounter.format_seconds(total_elapsed))
            self.progress_bar.setValue(0)
        else:
            self.lbl_elapsed.setText(
                f"{IntervalCounter.format_seconds(elapsed)} / "
                f"{IntervalCounter.format_seconds(interval)}"
            )
            progress = self._interval_counter.get_progress()
            self.progress_bar.setValue(int(progress * 100))

    def start_updates(self) -> None:
        self._progress_timer.start(1000)

    def stop_updates(self) -> None:
        self._progress_timer.stop()
        self.lbl_elapsed.setText("--:-- / --:--")
        self.progress_bar.setValue(0)

    def get_selected_interval(self) -> int:
        index = self.cmb_interval.currentIndex()
        seconds = self.cmb_interval.itemData(index)
        if seconds == -1:
            return self.spin_custom.value() * 60
        return seconds

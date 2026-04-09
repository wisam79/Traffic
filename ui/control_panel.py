"""
ملف لوحة التحكم - Control Panel
=================================
يُنشئ لوحة التحكم اليمنى مع الأزرار والإحصائيات.

المسؤوليات:
- إنشاء مجموعة اختيار مصدر الفيديو
- إنشاء مجموعة أزرار التحكم
- إنشاء بطاقات الإحصائيات الاحترافية
- تحديث الإحصائيات

المرتبط به:
- يُستورد من: main_window.py
- مرتبط بـ: ai_thread.py (تحديث الإحصائيات)
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QGridLayout, QPushButton, QLabel, QLineEdit, QFileDialog,
    QListWidget, QListWidgetItem, QMenu, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal

logger = logging.getLogger(__name__)

from ui.styles import (
    CONTROL_PANEL_STYLE, BUTTON_START_STYLE, BUTTON_STOP_STYLE,
    BUTTON_CLEAR_STYLE, BUTTON_RESET_STYLE, STAT_LABEL_STYLE,
    STAT_TOTAL_VALUE_STYLE, STAT_IN_VALUE_STYLE, STAT_OUT_VALUE_STYLE,
    STAT_VEHICLE_VALUE_STYLE
)
from ui.themes import (
    InputStyles, ListStyles, Spacing, Typography,
    ThemeColors, StatCardStyles, MiscStyles
)


class ControlPanel(QWidget):
    """
    لوحة التحكم اليمنى
    ===================
    تحتوي على جميع عناصر التحكم والعرض.
    """

    source_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMaximumWidth(340)
        self.setMinimumWidth(280)

        self.txt_source = None
        self.btn_select_source = None
        self.btn_show_info = None
        self.btn_load_video = None
        self.btn_start_stop = None
        self.btn_clear_line = None
        self.btn_reset_counts = None
        self.lst_recent_files = None

        self.lbl_total_value = None
        self.lbl_in_value = None
        self.lbl_out_value = None
        self.lbl_car_value = None
        self.lbl_truck_value = None
        self.lbl_motorcycle_value = None
        self.lbl_bus_value = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(MiscStyles.scroll_area())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(Spacing.MD)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)

        source_group = self._create_source_group()
        layout.addWidget(source_group)

        recent_group = self._create_recent_files_group()
        layout.addWidget(recent_group)

        controls_group = self._create_controls_group()
        layout.addWidget(controls_group)

        stats_section = self._create_stats_section()
        layout.addWidget(stats_section)

        layout.addStretch()

        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _create_source_group(self) -> QGroupBox:
        group = QGroupBox("مصدر الفيديو")
        layout = QVBoxLayout(group)
        layout.setSpacing(Spacing.SM)

        source_layout = QHBoxLayout()

        self.txt_source = QLineEdit()
        self.txt_source.setPlaceholderText("رابط RTSP أو مسار ملف أو رقم كاميرا")
        self.txt_source.setText("0")
        self.txt_source.setStyleSheet(InputStyles.line_edit())
        source_layout.addWidget(self.txt_source, stretch=1)

        self.btn_select_source = QPushButton("📂")
        self.btn_select_source.setFixedSize(36, 36)
        self.btn_select_source.setToolTip("تصفح ملفات الفيديو")
        self.btn_select_source.setStyleSheet(InputStyles.combo_box())
        self.btn_select_source.clicked.connect(self._on_browse_file)
        source_layout.addWidget(self.btn_select_source)

        layout.addLayout(source_layout)

        self.btn_show_info = QPushButton("ℹ️ معلومات الفيديو")
        self.btn_show_info.setStyleSheet(MiscStyles.tool_button())
        layout.addWidget(self.btn_show_info)

        return group

    def _create_recent_files_group(self) -> QGroupBox:
        group = QGroupBox("الأخيرة")
        layout = QVBoxLayout(group)
        layout.setSpacing(Spacing.XS)

        self.lst_recent_files = QListWidget()
        self.lst_recent_files.setMaximumHeight(80)
        self.lst_recent_files.setStyleSheet(ListStyles.list_widget())
        self.lst_recent_files.itemClicked.connect(self._on_recent_file_clicked)
        self.lst_recent_files.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lst_recent_files.customContextMenuRequested.connect(self._on_recent_file_context_menu)
        layout.addWidget(self.lst_recent_files)

        btn_clear_recent = QPushButton("مسح القائمة")
        btn_clear_recent.setStyleSheet(MiscStyles.tool_button())
        btn_clear_recent.clicked.connect(self._on_clear_recent)
        layout.addWidget(btn_clear_recent)

        return group

    def _create_controls_group(self) -> QGroupBox:
        group = QGroupBox("التحكم")
        group.setStyleSheet(CONTROL_PANEL_STYLE)
        layout = QVBoxLayout(group)
        layout.setSpacing(Spacing.SM)

        self.btn_load_video = QPushButton("▶ تحميل الفيديو")
        self.btn_load_video.setStyleSheet(BUTTON_START_STYLE)
        layout.addWidget(self.btn_load_video)

        self.btn_start_stop = QPushButton("⏸ بدء التحليل")
        self.btn_start_stop.setStyleSheet(BUTTON_STOP_STYLE)
        self.btn_start_stop.setEnabled(False)
        layout.addWidget(self.btn_start_stop)

        row = QHBoxLayout()
        row.setSpacing(Spacing.SM)

        self.btn_clear_line = QPushButton("🗑 مسح الخط")
        self.btn_clear_line.setStyleSheet(BUTTON_CLEAR_STYLE)
        row.addWidget(self.btn_clear_line)

        self.btn_reset_counts = QPushButton("🔄 إعادة العد")
        self.btn_reset_counts.setStyleSheet(BUTTON_RESET_STYLE)
        row.addWidget(self.btn_reset_counts)

        layout.addLayout(row)

        return group

    def _create_stats_section(self) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setSpacing(Spacing.MD)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("أعداد المركبات")
        title.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY}; font-size: {Typography.SIZE_XL}px; font-weight: bold; font-family: {Typography.FONT_FAMILY};")
        layout.addWidget(title)

        top_row = QHBoxLayout()
        top_row.setSpacing(Spacing.SM)

        top_row.addWidget(self._create_stat_card("الإجمالي", "0", STAT_TOTAL_VALUE_STYLE, StatCardStyles.total_card()))
        top_row.addWidget(self._create_stat_card("داخل", "0", STAT_IN_VALUE_STYLE, StatCardStyles.in_card()))
        top_row.addWidget(self._create_stat_card("خارج", "0", STAT_OUT_VALUE_STYLE, StatCardStyles.out_card()))

        layout.addLayout(top_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(MiscStyles.separator())
        layout.addWidget(sep)

        types_label = QLabel("حسب النوع")
        types_label.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: {Typography.SIZE_SM}px; font-weight: bold;")
        layout.addWidget(types_label)

        types_grid = QGridLayout()
        types_grid.setSpacing(Spacing.SM)

        self.lbl_car_value = self._add_vehicle_type(types_grid, 0, "🚗 سيارات", "0")
        self.lbl_truck_value = self._add_vehicle_type(types_grid, 1, "🚛 شاحنات", "0")
        self.lbl_motorcycle_value = self._add_vehicle_type(types_grid, 2, "🏍 دراجات", "0")
        self.lbl_bus_value = self._add_vehicle_type(types_grid, 3, "🚌 حافلات", "0")

        layout.addLayout(types_grid)

        return section

    def _create_stat_card(self, label_text: str, value_text: str, value_style: str, card_style: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(card_style)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(Spacing.XS)
        card_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(label_text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: {Typography.SIZE_SM}px; font-weight: bold;")
        card_layout.addWidget(lbl)

        val = QLabel(value_text)
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val.setStyleSheet(value_style)
        card_layout.addWidget(val)

        if label_text == "الإجمالي":
            self.lbl_total_value = val
        elif label_text == "داخل":
            self.lbl_in_value = val
        elif label_text == "خارج":
            self.lbl_out_value = val

        return card

    def _add_vehicle_type(self, grid: QGridLayout, row: int, label_text: str, value_text: str) -> QLabel:
        card = QFrame()
        card.setStyleSheet(StatCardStyles.vehicle_card())
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        card_layout.setSpacing(Spacing.SM)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: {Typography.SIZE_BASE}px;")
        card_layout.addWidget(lbl)

        card_layout.addStretch()

        val = QLabel(value_text)
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val.setStyleSheet(STAT_VEHICLE_VALUE_STYLE)
        card_layout.addWidget(val)

        grid.addWidget(card, row, 0)

        return val

    def _on_browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختيار ملف فيديو",
            "",
            "ملفات فيديو (*.mp4 *.avi *.mkv *.mov);;جميع الملفات (*)"
        )
        if file_path:
            self.txt_source.setText(file_path)

    def update_stats(self, stats: dict) -> None:
        try:
            self.lbl_total_value.setText(str(stats.get('total', 0)))
            self.lbl_in_value.setText(str(stats.get('in_count', 0)))
            self.lbl_out_value.setText(str(stats.get('out_count', 0)))
            self.lbl_car_value.setText(str(stats.get('car', 0)))
            self.lbl_truck_value.setText(str(stats.get('truck', 0)))
            self.lbl_motorcycle_value.setText(str(stats.get('motorcycle', 0)))
            self.lbl_bus_value.setText(str(stats.get('bus', 0)))
        except (AttributeError, TypeError, KeyError) as e:
            logger.error("Failed to update stats: %s", e)

    def update_recent_files(self, recent_files: list) -> None:
        self.lst_recent_files.clear()
        for file_path in recent_files:
            file_name = Path(file_path).name
            item = QListWidgetItem(f"📁 {file_name}")
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            item.setToolTip(file_path)
            self.lst_recent_files.addItem(item)

    def _on_recent_file_clicked(self, item) -> None:
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.txt_source.setText(file_path)
            self.source_selected.emit(file_path)

    def _on_recent_file_context_menu(self, pos) -> None:
        item = self.lst_recent_files.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        remove_action = menu.addAction("إزالة من القائمة")

        action = menu.exec(self.lst_recent_files.mapToGlobal(pos))

        if action == remove_action:
            row = self.lst_recent_files.row(item)
            self.lst_recent_files.takeItem(row)

    def _on_clear_recent(self) -> None:
        self.lst_recent_files.clear()

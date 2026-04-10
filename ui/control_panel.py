"""
ملف لوحة التحكم - Control Panel
=================================
لوحة التحكم اليسرى المضغوطة مع الأزرار والإحصائيات.
مُصممة لتناسب بدون تمرير.

المرتبط به:
- يُستورد من: main_window.py
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QGridLayout, QPushButton, QLabel, QLineEdit, QFileDialog,
    QListWidget, QListWidgetItem, QMenu, QFrame
)
from PySide6.QtCore import Qt, Signal

from ui.styles import (
    CONTROL_PANEL_STYLE, BUTTON_START_STYLE, BUTTON_STOP_STYLE,
    BUTTON_CLEAR_STYLE, BUTTON_RESET_STYLE,
    STAT_TOTAL_VALUE_STYLE, STAT_IN_VALUE_STYLE, STAT_OUT_VALUE_STYLE,
    STAT_VEHICLE_VALUE_STYLE
)
from ui.themes import (
    InputStyles, ListStyles, Spacing, Typography,
    ThemeColors, StatCardStyles, MiscStyles, ButtonStyles, StatusBarStyles
)

logger = logging.getLogger(__name__)


class ControlPanel(QWidget):
    """
    لوحة التحكم اليسرى المضغوطة
    =============================
    """

    source_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMaximumWidth(300)
        self.setMinimumWidth(240)

        self.txt_source = None
        self.btn_select_source = None
        self.btn_show_info = None
        self.btn_detect_cameras = None
        self.btn_load_video = None
        self.btn_start_stop = None
        self.btn_clear_line = None
        self.btn_reset_counts = None
        self.lst_recent_files = None
        self.btn_export = None
        self.btn_about = None
        self.btn_save_session = None
        self.btn_load_session = None

        self.lbl_total_value = None
        self.lbl_in_value = None
        self.lbl_out_value = None
        self.lbl_car_value = None
        self.lbl_truck_value = None
        self.lbl_motorcycle_value = None
        self.lbl_bus_value = None

        # Callback لإزالة ملف من القائمة الأخيرة
        self.on_remove_recent_file = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(Spacing.XS)
        layout.setContentsMargins(Spacing.XS, Spacing.XS, Spacing.XS, Spacing.XS)

        layout.addWidget(self._create_source_group())
        layout.addWidget(self._create_recent_group())
        layout.addWidget(self._create_stats_section())
        layout.addWidget(self._create_controls_group())
        layout.addStretch()

    def _create_source_group(self) -> QGroupBox:
        group = QGroupBox("المصدر")
        group.setStyleSheet(CONTROL_PANEL_STYLE)
        gl = QVBoxLayout(group)
        gl.setSpacing(2)
        gl.setContentsMargins(6, 14, 6, 6)

        row = QHBoxLayout()
        row.setSpacing(2)

        self.txt_source = QLineEdit()
        self.txt_source.setPlaceholderText("ملف/كاميرا/RTSP")
        self.txt_source.setText("0")
        self.txt_source.setStyleSheet(InputStyles.line_edit())
        row.addWidget(self.txt_source, stretch=1)

        self.btn_select_source = QPushButton("📂")
        self.btn_select_source.setFixedSize(30, 30)
        self.btn_select_source.setToolTip("تصفح")
        self.btn_select_source.setStyleSheet(InputStyles.combo_box())
        self.btn_select_source.clicked.connect(self._on_browse_file)
        row.addWidget(self.btn_select_source)

        self.btn_detect_cameras = QPushButton("📷")
        self.btn_detect_cameras.setFixedSize(30, 30)
        self.btn_detect_cameras.setToolTip("اكتشاف كاميرات")
        self.btn_detect_cameras.setStyleSheet(InputStyles.combo_box())
        self.btn_detect_cameras.clicked.connect(self._on_detect_cameras)
        row.addWidget(self.btn_detect_cameras)

        gl.addLayout(row)

        self.btn_show_info = QPushButton("ℹ️ معلومات")
        self.btn_show_info.setToolTip("معلومات الفيديو")
        self.btn_show_info.setStyleSheet(MiscStyles.tool_button())
        gl.addWidget(self.btn_show_info)

        return group

    def _create_recent_group(self) -> QGroupBox:
        group = QGroupBox("الأخيرة")
        group.setStyleSheet(CONTROL_PANEL_STYLE)
        gl = QVBoxLayout(group)
        gl.setSpacing(2)
        gl.setContentsMargins(6, 14, 6, 6)

        self.lst_recent_files = QListWidget()
        self.lst_recent_files.setMaximumHeight(50)
        self.lst_recent_files.setStyleSheet(ListStyles.list_widget())
        self.lst_recent_files.itemClicked.connect(self._on_recent_file_clicked)
        self.lst_recent_files.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lst_recent_files.customContextMenuRequested.connect(self._on_recent_file_context_menu)
        gl.addWidget(self.lst_recent_files)

        return group

    def _create_stats_section(self) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setSpacing(Spacing.XS)
        layout.setContentsMargins(0, 0, 0, 0)

        top_row = QHBoxLayout()
        top_row.setSpacing(2)

        top_row.addWidget(self._make_card("إجمالي", "0", STAT_TOTAL_VALUE_STYLE, StatCardStyles.total_card()))
        top_row.addWidget(self._make_card("داخل", "0", STAT_IN_VALUE_STYLE, StatCardStyles.in_card()))
        top_row.addWidget(self._make_card("خارج", "0", STAT_OUT_VALUE_STYLE, StatCardStyles.out_card()))

        layout.addLayout(top_row)

        types_grid = QGridLayout()
        types_grid.setSpacing(2)
        self.lbl_car_value = self._add_type(types_grid, 0, "🚗", "0")
        self.lbl_truck_value = self._add_type(types_grid, 1, "🚛", "0")
        self.lbl_motorcycle_value = self._add_type(types_grid, 2, "🏍", "0")
        self.lbl_bus_value = self._add_type(types_grid, 3, "🚌", "0")
        layout.addLayout(types_grid)

        return section

    def _make_card(self, label_text: str, value_text: str, value_style: str, card_style: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(card_style)
        cl = QVBoxLayout(card)
        cl.setSpacing(0)
        cl.setContentsMargins(4, 4, 4, 4)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(label_text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(StatusBarStyles.card_label())
        cl.addWidget(lbl)

        val = QLabel(value_text)
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val.setStyleSheet(value_style)
        cl.addWidget(val)

        if label_text == "إجمالي":
            self.lbl_total_value = val
        elif label_text == "داخل":
            self.lbl_in_value = val
        elif label_text == "خارج":
            self.lbl_out_value = val

        return card

    def _add_type(self, grid: QGridLayout, row: int, icon: str, value_text: str) -> QLabel:
        card = QFrame()
        card.setStyleSheet(StatCardStyles.vehicle_card())
        cl = QHBoxLayout(card)
        cl.setContentsMargins(4, 1, 4, 1)
        cl.setSpacing(4)

        lbl = QLabel(icon)
        lbl.setStyleSheet(f"font-size: {Typography.SIZE_SM}px;")
        cl.addWidget(lbl)

        cl.addStretch()

        val = QLabel(value_text)
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val.setStyleSheet(STAT_VEHICLE_VALUE_STYLE)
        cl.addWidget(val)

        grid.addWidget(card, row, 0)
        return val

    def _create_controls_group(self) -> QGroupBox:
        group = QGroupBox("التحكم")
        group.setStyleSheet(CONTROL_PANEL_STYLE)
        gl = QVBoxLayout(group)
        gl.setSpacing(2)
        gl.setContentsMargins(6, 14, 6, 6)

        self.btn_load_video = QPushButton("▶ تحميل")
        self.btn_load_video.setToolTip("تحميل الفيديو (Ctrl+O)")
        self.btn_load_video.setStyleSheet(BUTTON_START_STYLE)
        gl.addWidget(self.btn_load_video)

        self.btn_start_stop = QPushButton("⏸ تحليل")
        self.btn_start_stop.setToolTip("بدء/إيقاف التحليل (Space)")
        self.btn_start_stop.setStyleSheet(BUTTON_STOP_STYLE)
        self.btn_start_stop.setEnabled(False)
        gl.addWidget(self.btn_start_stop)

        row1 = QHBoxLayout()
        row1.setSpacing(2)

        self.btn_clear_line = QPushButton("🗑 خط")
        self.btn_clear_line.setToolTip("مسح الخطوط")
        self.btn_clear_line.setStyleSheet(BUTTON_CLEAR_STYLE)
        row1.addWidget(self.btn_clear_line)

        self.btn_reset_counts = QPushButton("🔄 عد")
        self.btn_reset_counts.setToolTip("إعادة العدادات")
        self.btn_reset_counts.setStyleSheet(BUTTON_RESET_STYLE)
        row1.addWidget(self.btn_reset_counts)

        gl.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(2)

        self.btn_export = QPushButton("📊 تصدير")
        self.btn_export.setToolTip("تصدير CSV/JSON")
        self.btn_export.setStyleSheet(ButtonStyles.info_button())
        row2.addWidget(self.btn_export)

        self.btn_about = QPushButton("ℹ️")
        self.btn_about.setToolTip("حول التطبيق")
        self.btn_about.setStyleSheet(MiscStyles.tool_button())
        row2.addWidget(self.btn_about)

        gl.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(2)

        self.btn_save_session = QPushButton("💾 حفظ")
        self.btn_save_session.setToolTip("حفظ الجلسة")
        self.btn_save_session.setStyleSheet(ButtonStyles.secondary_button())
        row3.addWidget(self.btn_save_session)

        self.btn_load_session = QPushButton("📂 تحميل")
        self.btn_load_session.setToolTip("تحميل جلسة")
        self.btn_load_session.setStyleSheet(ButtonStyles.secondary_button())
        row3.addWidget(self.btn_load_session)

        gl.addLayout(row3)

        return group

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

    def _on_browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختيار ملف فيديو", "",
            "ملفات فيديو (*.mp4 *.avi *.mkv *.mov);;جميع الملفات (*)"
        )
        if file_path:
            self.txt_source.setText(file_path)

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
        remove_action = menu.addAction("إزالة")
        action = menu.exec(self.lst_recent_files.mapToGlobal(pos))
        if action == remove_action:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            self.lst_recent_files.takeItem(self.lst_recent_files.row(item))
            # تحديث مدير الملفات الأخيرة
            if self.on_remove_recent_file and file_path:
                self.on_remove_recent_file(file_path)

    def _on_clear_recent(self) -> None:
        self.lst_recent_files.clear()

    def _on_detect_cameras(self) -> None:
        from ui.video_source_manager import VideoSourceManager
        from PySide6.QtWidgets import QMessageBox
        cameras = VideoSourceManager.discover_cameras()
        if cameras:
            self.txt_source.setText(cameras[0])
            QMessageBox.information(
                self, "الكاميرات",
                f"تم اكتشاف {len(cameras)} كاميرا:\n" + "\n".join(f"  كاميرا {c}" for c in cameras)
            )
        else:
            QMessageBox.information(self, "الكاميرات", "لم يتم اكتشاف أي كاميرا")

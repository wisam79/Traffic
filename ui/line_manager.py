"""
ملف إدارة الخطوط - Line Manager Widget
========================================
واجهة لعرض وإدارة جميع خطوط العد.

المسؤوليات:
- عرض قائمة الخطوط
- تحديد/حذف الخطوط
- تغيير أوضاع الرسم
- أزرار التراجع/إعادة

المرتبط به:
- يُستورد من: video_panel.py
- يتحكم في: drawing_modes.py
"""

from typing import Callable, Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QComboBox,
    QMessageBox
)
from PySide6.QtCore import Qt

from ui.drawing_modes import DrawingMode, LineData
from ui.styles import CONTROL_PANEL_STYLE


class LineManagerWidget(QWidget):
    """
    ويدجت إدارة الخطوط
    ====================
    يُعرض في لوحة الفيديو للسماح للمستخدم بإدارة الخطوط.
    """

    def __init__(self):
        """تهيئة ويدجت الإدارة."""
        super().__init__()

        # العناصر
        self.lst_lines = None
        self.cmb_mode = None
        self.btn_undo = None
        self.btn_redo = None
        self.btn_delete = None
        self.btn_clear_all = None
        self.lbl_line_count = None

        # إنشاء الواجهة
        self._setup_ui()

    def _setup_ui(self) -> None:
        """إنشاء العناصر."""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # ==================================================================
        # صف وضع الرسم
        # ==================================================================
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("وضع الرسم:"))

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItem("خط واحد", DrawingMode.SINGLE_LINE)
        self.cmb_mode.addItem("خطوط متعددة", DrawingMode.MULTI_LINE)
        self.cmb_mode.setItemData(0, DrawingMode.SINGLE_LINE, Qt.ItemDataRole.UserRole)
        self.cmb_mode.setItemData(1, DrawingMode.MULTI_LINE, Qt.ItemDataRole.UserRole)
        mode_layout.addWidget(self.cmb_mode)

        layout.addLayout(mode_layout)

        # ==================================================================
        # أزرار التحكم
        # ==================================================================
        btn_layout = QHBoxLayout()

        self.btn_undo = QPushButton("↶ تراجع")
        self.btn_undo.setFixedHeight(28)
        btn_layout.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("↷ إعادة")
        self.btn_redo.setFixedHeight(28)
        btn_layout.addWidget(self.btn_redo)

        self.btn_delete = QPushButton("🗑 حذف المحدد")
        self.btn_delete.setFixedHeight(28)
        self.btn_delete.setStyleSheet("background-color: #f44336; color: white;")
        btn_layout.addWidget(self.btn_delete)

        layout.addLayout(btn_layout)

        self.btn_clear_all = QPushButton("⊗ مسح الكل")
        self.btn_clear_all.setFixedHeight(32)
        self.btn_clear_all.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        layout.addWidget(self.btn_clear_all)

        # ==================================================================
        # قائمة الخطوط
        # ==================================================================
        layout.addWidget(QLabel("الخطوط المحددة:"))

        self.lst_lines = QListWidget()
        self.lst_lines.setMaximumHeight(150)
        self.lst_lines.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.lst_lines)

        # عداد
        self.lbl_line_count = QLabel("عدد الخطوط: 0")
        self.lbl_line_count.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self.lbl_line_count)

    def update_line_list(self, lines: List[LineData]) -> None:
        """
        تحديث قائمة الخطوط

        المُعاملات (Args):
            lines: قائمة الخطوط الجديدة
        """
        self.lst_lines.clear()

        for line_data in lines:
            # Validate line_data attributes for type safety
            if not hasattr(line_data, 'points') or not hasattr(line_data, 'line_id'):
                continue
            if not isinstance(line_data.points, list) or not line_data.points:
                continue
            if not isinstance(line_data.line_id, int):
                continue

            if len(line_data.points) == 2:
                # خط عادي
                p1, p2 = line_data.points
                text = f"خط #{line_data.line_id}: ({p1[0]},{p1[1]}) → ({p2[0]},{p2[1]})"
            else:
                # مضلع
                text = f"منطقة #{line_data.line_id}: {len(line_data.points)} نقاط"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, line_data.line_id)
            self.lst_lines.addItem(item)

        self.lbl_line_count.setText(f"عدد الخطوط: {len(lines)}")

    def get_selected_line_id(self) -> Optional[int]:
        """الحصول على معرف الخط المحدد."""
        current_item = self.lst_lines.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def get_selected_drawing_mode(self) -> DrawingMode:
        """الحصول على وضع الرسم المحدد."""
        return self.cmb_mode.currentData()

"""
نافذة تقرير الفترات - Interval Report Dialog
===============================================
نافذة احترافية لعرض تقرير تفصيلي لعد المركبات حسب الفترات الزمنية.
تنسيق هندسة المرور: كل فترة في صف مع تفاصيل أنواع المركبات والوقت.

المرتبط به:
- يُستورد من: ui/interval_panel.py
- يرتبط بـ: engine/interval_counter.py
"""

import csv
import json
import logging
from datetime import datetime
from typing import List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QFileDialog, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ui.themes import ThemeColors, Typography, Spacing, ButtonStyles
from engine.interval_counter import IntervalRecord

logger = logging.getLogger(__name__)


class IntervalReportDialog(QDialog):
    """
    نافذة تقرير الفترات التفصيلي
    =============================
    تعرض جدولاً احترافياً بتنسيق هندسة المرور.
    """

    VEHICLE_COLUMNS = [
        ("bus", "حافلة"),
        ("motorcycle", "دراجة"),
        ("truck", "شاحنة"),
        ("car", "سيارة"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تقرير عد المركبات")
        self.setMinimumSize(700, 450)
        self.resize(800, 550)
        self._records: List[IntervalRecord] = []
        self._interval_seconds: int = 0
        self._direction_label: str = ""

        self.tbl_report = None
        self.lbl_summary = None

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(Spacing.MD)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)

        header_row = QHBoxLayout()

        title = QLabel("تقرير عد المركبات التفصيلي")
        title.setStyleSheet(
            f"color: {ThemeColors.TEXT_PRIMARY}; "
            f"font-size: {Typography.SIZE_XL}px; "
            f"font-weight: bold;"
        )
        header_row.addWidget(title)
        header_row.addStretch()
        layout.addLayout(header_row)

        info_row = QHBoxLayout()
        self._lbl_date = QLabel("")
        self._lbl_date.setStyleSheet(
            f"color: {ThemeColors.TEXT_SECONDARY}; "
            f"font-size: {Typography.SIZE_SM}px;"
        )
        info_row.addWidget(self._lbl_date)

        self._lbl_direction = QLabel("")
        self._lbl_direction.setStyleSheet(
            f"color: {ThemeColors.INFO}; "
            f"font-size: {Typography.SIZE_SM}px; "
            f"font-weight: bold;"
        )
        info_row.addWidget(self._lbl_direction)
        info_row.addStretch()
        layout.addLayout(info_row)

        self.tbl_report = QTableWidget(0, 0)
        self.tbl_report.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_report.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_report.setAlternatingRowColors(True)
        self.tbl_report.verticalHeader().setVisible(False)
        self.tbl_report.horizontalHeader().setStretchLastSection(True)
        self.tbl_report.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.tbl_report, stretch=1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {ThemeColors.BORDER_DARK};")
        layout.addWidget(sep)

        bottom_row = QHBoxLayout()

        self.lbl_summary = QLabel("")
        self.lbl_summary.setStyleSheet(
            f"color: {ThemeColors.TEXT_SECONDARY}; "
            f"font-size: {Typography.SIZE_SM}px; "
            f"font-family: {Typography.FONT_FAMILY_MONO};"
        )
        bottom_row.addWidget(self.lbl_summary, stretch=1)

        btn_export_csv = QPushButton("CSV تصدير")
        btn_export_csv.setStyleSheet(ButtonStyles.info_button())
        btn_export_csv.clicked.connect(self._export_csv)
        bottom_row.addWidget(btn_export_csv)

        btn_export_json = QPushButton("JSON تصدير")
        btn_export_json.setStyleSheet(ButtonStyles.secondary_button())
        btn_export_json.clicked.connect(self._export_json)
        bottom_row.addWidget(btn_export_json)

        btn_close = QPushButton("إغلاق")
        btn_close.setStyleSheet(ButtonStyles.secondary_button())
        btn_close.clicked.connect(self.close)
        bottom_row.addWidget(btn_close)

        layout.addLayout(bottom_row)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {ThemeColors.BACKGROUND_DARKEST};
            }}
            QTableWidget {{
                background-color: {ThemeColors.BACKGROUND_DARK};
                alternate-background-color: {ThemeColors.BACKGROUND_MEDIUM};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_DARK};
                font-size: {Typography.SIZE_SM}px;
                color: {ThemeColors.TEXT_PRIMARY};
                font-family: {Typography.FONT_FAMILY};
            }}
            QTableWidget::item {{
                padding: 4px 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {ThemeColors.INFO};
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BACKGROUND_LIGHT};
                color: {ThemeColors.TEXT_PRIMARY};
                border: 1px solid {ThemeColors.BORDER_DARK};
                padding: 6px 8px;
                font-size: {Typography.SIZE_SM}px;
                font-weight: bold;
            }}
            """
        )

    def update_data(
        self,
        records: List[IntervalRecord],
        interval_seconds: int,
        direction_label: str = ""
    ) -> None:
        self._records = records
        self._interval_seconds = interval_seconds
        self._direction_label = direction_label

        self._lbl_date.setText(f"التاريخ: {datetime.now().strftime('%A  %d/%m/%Y')}")
        self._lbl_direction.setText(direction_label)

        self._populate_table()
        self._update_summary()

    def _populate_table(self) -> None:
        headers = ["#", "الوقت"]
        for key, name in self.VEHICLE_COLUMNS:
            headers.append(name)
        headers.extend(["داخل", "خارج", "الإجمالي"])

        self.tbl_report.setColumnCount(len(headers))
        self.tbl_report.setHorizontalHeaderLabels(headers)
        self.tbl_report.setRowCount(len(self._records))

        total_row = {
            "bus": 0, "motorcycle": 0, "truck": 0, "car": 0,
            "in_count": 0, "out_count": 0, "total": 0
        }

        for row, record in enumerate(self._records):
            start_str = datetime.fromtimestamp(record.start_time).strftime("%H:%M")
            end_str = datetime.fromtimestamp(record.end_time).strftime("%H:%M")

            self._set_item(row, 0, f"#{record.index + 1}", align=Qt.AlignmentFlag.AlignCenter)
            self._set_item(row, 1, f"{start_str}-{end_str}", align=Qt.AlignmentFlag.AlignCenter,
                           color=ThemeColors.ACCENT_CYAN)

            for col_offset, (key, _) in enumerate(self.VEHICLE_COLUMNS):
                val = record.stats.get(key, 0)
                self._set_item(row, 2 + col_offset, str(val), align=Qt.AlignmentFlag.AlignCenter)
                total_row[key] += val

            in_c = record.stats.get("in_count", 0)
            out_c = record.stats.get("out_count", 0)
            total_c = record.stats.get("total", 0)

            self._set_item(row, len(headers) - 3, str(in_c), align=Qt.AlignmentFlag.AlignCenter,
                           color=ThemeColors.INFO)
            self._set_item(row, len(headers) - 2, str(out_c), align=Qt.AlignmentFlag.AlignCenter,
                           color=ThemeColors.WARNING)
            self._set_item(row, len(headers) - 1, str(total_c), align=Qt.AlignmentFlag.AlignCenter,
                           color=ThemeColors.SUCCESS, bold=True)

            total_row["in_count"] += in_c
            total_row["out_count"] += out_c
            total_row["total"] += total_c

        total_row_idx = self.tbl_report.rowCount()
        self.tbl_report.insertRow(total_row_idx)

        self._set_item(total_row_idx, 0, "", align=Qt.AlignmentFlag.AlignCenter, bold=True)
        self._set_item(total_row_idx, 1, "المجموع", align=Qt.AlignmentFlag.AlignCenter,
                       color=ThemeColors.TEXT_PRIMARY, bold=True)

        for col_offset, (key, _) in enumerate(self.VEHICLE_COLUMNS):
            self._set_item(total_row_idx, 2 + col_offset, str(total_row[key]),
                           align=Qt.AlignmentFlag.AlignCenter, bold=True)

        self._set_item(total_row_idx, len(headers) - 3, str(total_row["in_count"]),
                       align=Qt.AlignmentFlag.AlignCenter, color=ThemeColors.INFO, bold=True)
        self._set_item(total_row_idx, len(headers) - 2, str(total_row["out_count"]),
                       align=Qt.AlignmentFlag.AlignCenter, color=ThemeColors.WARNING, bold=True)
        self._set_item(total_row_idx, len(headers) - 1, str(total_row["total"]),
                       align=Qt.AlignmentFlag.AlignCenter, color=ThemeColors.SUCCESS, bold=True)

        for i in range(len(headers)):
            self.tbl_report.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.Stretch
            )

    def _set_item(
        self,
        row: int,
        col: int,
        text: str,
        align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
        color: Optional[str] = None,
        bold: bool = False
    ) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(align)
        if color:
            item.setForeground(QColor(color))
        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        self.tbl_report.setItem(row, col, item)

    def _update_summary(self) -> None:
        if not self._records:
            self.lbl_summary.setText("لا توجد بيانات بعد")
            return

        total_vehicles = sum(r.stats.get("total", 0) for r in self._records)
        total_duration = sum(r.duration_seconds for r in self._records)
        avg = total_vehicles / len(self._records) if self._records else 0

        self.lbl_summary.setText(
            f"الفترات: {len(self._records)} | "
            f"الإجمالي: {total_vehicles} | "
            f"المتوسط/فترة: {avg:.1f} | "
            f"المدة الكلية: {IntervalRecord.__module__ and ''}"
            f"{self._format_duration(total_duration)}"
        )

    @staticmethod
    def _format_duration(seconds: float) -> str:
        h = int(seconds) // 3600
        m = (int(seconds) % 3600) // 60
        s = int(seconds) % 60
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    def _export_csv(self) -> None:
        if not self._records:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "تصدير التقرير",
            f"traffic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV (*.csv)"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([f"التاريخ: {datetime.now().strftime('%A %d/%m/%Y')}"])
                writer.writerow([f"الاتجاه: {self._direction_label}"])
                writer.writerow([])

                headers = ["#", "الوقت"]
                for key, name in self.VEHICLE_COLUMNS:
                    headers.append(name)
                headers.extend(["داخل", "خارج", "الإجمالي"])
                writer.writerow(headers)

                for record in self._records:
                    start_str = datetime.fromtimestamp(record.start_time).strftime("%H:%M")
                    end_str = datetime.fromtimestamp(record.end_time).strftime("%H:%M")
                    row = [f"#{record.index + 1}", f"{start_str}-{end_str}"]
                    for key, _ in self.VEHICLE_COLUMNS:
                        row.append(record.stats.get(key, 0))
                    row.extend([
                        record.stats.get("in_count", 0),
                        record.stats.get("out_count", 0),
                        record.stats.get("total", 0)
                    ])
                    writer.writerow(row)

            logger.info(f"تم تصدير التقرير CSV: {filepath}")
        except Exception as e:
            logger.error(f"فشل تصدير CSV: {e}")

    def _export_json(self) -> None:
        if not self._records:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "تصدير التقرير",
            f"traffic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON (*.json)"
        )
        if not filepath:
            return

        try:
            data = {
                "date": datetime.now().strftime("%A %d/%m/%Y"),
                "direction": self._direction_label,
                "interval_seconds": self._interval_seconds,
                "intervals": []
            }
            for record in self._records:
                start_str = datetime.fromtimestamp(record.start_time).strftime("%H:%M")
                end_str = datetime.fromtimestamp(record.end_time).strftime("%H:%M")
                entry = {
                    "interval": record.index + 1,
                    "time_range": f"{start_str}-{end_str}",
                    "start_time": datetime.fromtimestamp(record.start_time).isoformat(),
                    "end_time": datetime.fromtimestamp(record.end_time).isoformat(),
                    "duration_seconds": round(record.duration_seconds, 1),
                    "counts": {}
                }
                for key, _ in self.VEHICLE_COLUMNS:
                    entry["counts"][key] = record.stats.get(key, 0)
                entry["counts"]["in_count"] = record.stats.get("in_count", 0)
                entry["counts"]["out_count"] = record.stats.get("out_count", 0)
                entry["counts"]["total"] = record.stats.get("total", 0)
                data["intervals"].append(entry)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"تم تصدير التقرير JSON: {filepath}")
        except Exception as e:
            logger.error(f"فشل تصدير JSON: {e}")

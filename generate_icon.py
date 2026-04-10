#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate app icon for Smart Intersection Vehicle Counting System
Creates a multi-resolution .ico file with a traffic/intersection theme.
"""

import os
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QFont, QIcon
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtWidgets import QApplication

import sys

def draw_icon(painter: QPainter, size: int):
    s = size

    bg = QColor("#1a1a2e")
    painter.fillRect(0, 0, s, s, bg)

    cx, cy = s / 2, s / 2
    r = s * 0.42

    road_h = QColor("#2d2d44")
    road_v = QColor("#2d2d44")
    painter.setPen(Qt.PenStyle.NoPen)
    rw = s * 0.22

    painter.setBrush(QBrush(road_h))
    painter.drawRect(int(cx - r - rw/2), int(cy - rw/2), int(r * 2 + rw), int(rw))

    painter.setBrush(QBrush(road_v))
    painter.drawRect(int(cx - rw/2), int(cy - r - rw/2), int(rw), int(r * 2 + rw))

    line_color = QColor("#e94560")
    dash_pen = QPen(line_color, max(1, s * 0.02), Qt.PenStyle.DashLine)
    painter.setPen(dash_pen)
    painter.drawLine(int(cx - r), int(cy), int(cx - rw/2 - 2), int(cy))
    painter.drawLine(int(cx + rw/2 + 2), int(cy), int(cx + r), int(cy))
    painter.drawLine(int(cx), int(cy - r), int(cx), int(cy - rw/2 - 2))
    painter.drawLine(int(cx), int(cy + rw/2 + 2), int(cx), int(cy + r))

    center_circle_r = s * 0.10
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor("#0f3460")))
    painter.drawEllipse(QPointF(cx, cy), center_circle_r, center_circle_r)

    inner_r = center_circle_r * 0.65
    painter.setBrush(QBrush(QColor("#16213e")))
    painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

    car_colors = [QColor("#e94560"), QColor("#0f3460"), QColor("#e9b44c"), QColor("#50b8e7")]
    car_positions = [
        (cx - r * 0.6, cy - rw * 0.28, s * 0.06, s * 0.04),
        (cx + r * 0.35, cy + rw * 0.28, s * 0.06, s * 0.04),
        (cx - rw * 0.28, cy + r * 0.5, s * 0.04, s * 0.06),
        (cx + rw * 0.28, cy - r * 0.4, s * 0.04, s * 0.06),
    ]
    painter.setPen(Qt.PenStyle.NoPen)
    for color, (x, y, w, h) in zip(car_colors, car_positions):
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(QRectF(x - w/2, y - h/2, w, h), s * 0.008, s * 0.008)

    green = QColor("#4ade80")
    painter.setBrush(QBrush(green))
    gr = s * 0.025
    painter.drawEllipse(QPointF(cx + center_circle_r * 0.45, cy - center_circle_r * 0.45), gr, gr)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#e94560"))
    rr = s * 0.018
    painter.drawEllipse(QPointF(cx - center_circle_r * 0.45, cy + center_circle_r * 0.45), rr, rr)

    font_size = max(6, int(s * 0.14))
    font = QFont("Segoe UI", font_size)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("#ffffff"))
    painter.drawText(QRectF(0, s * 0.72, s, s * 0.26), Qt.AlignmentFlag.AlignCenter, "TR")

    border_pen = QPen(QColor("#e94560"), max(1, s * 0.025))
    painter.setPen(border_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    m = s * 0.02
    painter.drawRoundedRect(QRectF(m, m, s - 2*m, s - 2*m), s * 0.12, s * 0.12)


def generate_icon(output_dir: str = None):
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

    os.makedirs(output_dir, exist_ok=True)

    sizes = [16, 24, 32, 48, 64, 128, 256]
    pixmaps = []

    for size in sizes:
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        draw_icon(painter, size)
        painter.end()
        pixmaps.append(pm)

    ico_path = os.path.join(output_dir, "app_icon.ico")
    png_path = os.path.join(output_dir, "app_icon.png")

    pm256 = pixmaps[-1]
    pm256.save(ico_path, "ico")
    pm256.save(png_path, "png")

    for pm in pixmaps:
        sz = pm.width()
        p = os.path.join(output_dir, f"app_icon_{sz}x{sz}.png")
        pm.save(p, "png")

    print(f"Icon generated successfully!")
    print(f"  ICO: {ico_path}")
    print(f"  PNG: {png_path}")
    return ico_path, png_path


if __name__ == "__main__":
    app = QApplication(sys.argv)
    generate_icon()

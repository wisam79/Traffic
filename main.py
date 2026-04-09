#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
نظام عد المركبات الذكي - تقاطعات المرور
=========================================
Smart Intersection Vehicle Counting System

نقطة الدخول الرئيسية للتطبيق.
هذا الملف بسيط جداً - كل العمل في core/app.py

الاستخدام:
    python main.py

المتطلبات:
    - Python 3.10+
    - PySide6
    - onnxruntime-gpu (أو onnxruntime)
    - opencv-python
    - vidgear
    - supervision
    - numpy

المؤلف: Enterprise AI Team
الإصدار: 2.0
"""

import sys
import os

# إضافة مسار المشروع للـ Python path
# هذا يسمح باستيراد الملفات من أي مكان في المشروع
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    """
    الدالة الرئيسية
    ================
    نقطة الدخول البسيطة التي تُشغل التطبيق.
    كل الإعداد في core/app.py
    """
    from core.app import run
    sys.exit(run())


if __name__ == "__main__":
    main()

"""
ملف إعداد التطبيق الرئيسي - Main Application Setup
====================================================
يُهيئ التطبيق: السجلات، الخطوط، والنافذة الرئيسية.

المسؤوليات:
- إعداد نظام السجلات (logging)
- إعداد التطبيق PySide6
- إنشاء وعرض النافذة الرئيسية

المرتبط به:
- يُستورد من: main.py
- ينشئ: ui/main_window.py
"""

import sys
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from core.config import LOG_LEVEL, LOG_FORMAT, APP_FONT_NAME, APP_FONT_SIZE
from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """
    إعداد نظام السجلات
    ====================
    يُهيئ تنسيق ومستوى رسائل السجل.
    تُستدعى مرة واحدة عند بدء التطبيق.
    """
    try:
        level = getattr(logging, LOG_LEVEL)
    except AttributeError:
        level = logging.WARNING
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT
    )
    logger.info("تم إعداد نظام السجلات بنجاح")


def create_application() -> QApplication:
    """
    إنشاء تطبيق PySide6
    ======================
    يُنشئ كائن QApplication ويُعد الخصائص العامة.

    المرجع (Returns):
        كائن QApplication جاهز
    """
    # إنشاء التطبيق
    existing_app = QApplication.instance()
    if existing_app is not None:
        app = existing_app
    else:
        app = QApplication(sys.argv)

    # تعيين الخط العام
    font = QFont(APP_FONT_NAME, APP_FONT_SIZE)
    app.setFont(font)

    # تعيين النمط الداكن
    app.setStyle("Fusion")

    logger.info("تم إنشاء تطبيق PySide6")
    return app


def run() -> int:
    """
    تشغيل التطبيق
    ===============
    الدالة الرئيسية التي تُشغل كل شيء.

    الخطوات:
    1. إعداد السجلات
    2. إنشاء QApplication
    3. إنشاء وعرض MainWindow
    4. تشغيل حلقة الأحداث

    المرجع (Returns):
        رمز الخروج (0 = نجاح)
    """
    # الخطوة 1: إعداد السجلات
    setup_logging()

    logger.info("=== بدء تطبيق نظام عد المركبات الذكي ===")

    # الخطوة 2: إنشاء التطبيق
    app = create_application()

    # الخطوة 3: إنشاء وعرض النافذة الرئيسية
    window = MainWindow()
    window.show()

    logger.info("تم عرض النافذة الرئيسية")

    # الخطوة 4: تشغيل حلقة الأحداث
    # app.exec() تُسيطر على الخيط حتى إغلاق التطبيق
    exit_code = app.exec()

    logger.info("=== انتهى تطبيق نظام عد المركبات الذكي ===")

    return exit_code

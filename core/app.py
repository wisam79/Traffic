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
import os
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon

from core.config import LOG_LEVEL, LOG_FORMAT, APP_FONT_NAME, APP_FONT_SIZE, APP_ICON_PATH
from ui.main_window import MainWindow
from ui.themes import ThemeColors

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

    # تعيين أيقونة التطبيق
    if os.path.exists(APP_ICON_PATH):
        app.setWindowIcon(QIcon(APP_ICON_PATH))

    logger.info("تم إنشاء تطبيق PySide6")
    return app


def run() -> int:
    setup_logging()

    logger.info("=== بدء تطبيق نظام عد المركبات الذكي ===")

    app = create_application()

    splash = None
    try:
        from PySide6.QtWidgets import QSplashScreen
        from PySide6.QtGui import QPixmap
        from PySide6.QtCore import Qt

        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.GlobalColor.transparent)
        splash = QSplashScreen(pixmap)
        splash.setStyleSheet(f"""
            QSplashScreen {{
                background-color: {ThemeColors.BACKGROUND_DARK};
                border: 2px solid {ThemeColors.SUCCESS};
                border-radius: 12px;
            }}
        """)
        splash.showMessage(
            "جاري تحميل النموذج...\nLoading AI Model...",
            Qt.AlignmentFlag.AlignCenter,
            ThemeColors.SUCCESS
        )
        splash.show()
        app.processEvents()
    except Exception:
        splash = None

    window = MainWindow()
    window.show()

    if splash:
        splash.finish(window)

    logger.info("تم عرض النافذة الرئيسية")

    exit_code = app.exec()

    logger.info("=== انتهى تطبيق نظام عد المركبات الذكي ===")

    return exit_code

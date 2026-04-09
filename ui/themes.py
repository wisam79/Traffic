"""
ملف الثيمات الاحترافية - Professional Theme System
====================================================
نظام تصميم احترافي للتطبيق بالكامل.

المسؤوليات:
- نظام ألوان متسق
- أنماط الأزرار مع تأثيرات
- أنماط البطاقات والمجموعات
- أنظمة الخطوط والطباعة
- تأثيرات الحركة والانتقالات

المرتبط به:
- يُستخدم من: جميع مكونات الواجهة
"""


# ==============================================================================
# نظام الألوان
# ==============================================================================

class ThemeColors:
    """
    نظام الألوان الاحترافي
    ======================
    ألوان متناسقة للتصميم الداكن الحديث.
    """
    
    # الألوان الأساسية
    BACKGROUND_DARKEST = "#0d0d0d"
    BACKGROUND_DARK = "#1a1a1a"
    BACKGROUND_MEDIUM = "#252525"
    BACKGROUND_LIGHT = "#2f2f2f"
    
    # الحدود والفواصل
    BORDER_DARK = "#3a3a3a"
    BORDER_MEDIUM = "#4a4a4a"
    BORDER_LIGHT = "#5a5a5a"
    
    # النصوص
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    TEXT_MUTED = "#808080"
    TEXT_DISABLED = "#606060"
    
    # ألوان النجاح والحالة
    SUCCESS = "#4CAF50"
    SUCCESS_DARK = "#3d8b40"
    SUCCESS_LIGHT = "#5cbf60"
    
    # ألوان الخطأ والتحذير
    ERROR = "#f44336"
    ERROR_DARK = "#d32f2f"
    ERROR_LIGHT = "#ef5350"
    
    # ألوان المعلومات
    INFO = "#2196F3"
    INFO_DARK = "#1976D2"
    INFO_LIGHT = "#64B5F6"
    
    # ألوان التنبيه
    WARNING = "#FF9800"
    WARNING_DARK = "#F57C00"
    WARNING_LIGHT = "#FFB74D"
    
    # ألوان مميزة
    ACCENT_CYAN = "#00BCD4"
    ACCENT_PURPLE = "#9C27B0"
    ACCENT_TEAL = "#009688"
    ACCENT_PINK = "#E91E63"
    
    # التدرجات
    GRADIENT_HEADER = """
        qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #2a2a2a, 
            stop:0.5 #222222,
            stop:1 #1a1a1a)
    """
    
    GRADIENT_CARD = """
        qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #252525,
            stop:1 #1f1f1f)
    """


# ==============================================================================
# أنظمة الخطوط
# ==============================================================================

class Typography:
    """
    نظام الطباعة والخطوط
    ======================
    """
    
    # الخط الرئيسي
    FONT_FAMILY = "Segoe UI"
    FONT_FAMILY_MONO = "Consolas"
    
    # أحجام الخطوط
    SIZE_XS = 10    # نصوص صغيرة جداً
    SIZE_SM = 11    # نصوص ثانوية
    SIZE_BASE = 12  # النص الأساسي
    SIZE_LG = 13    # عناوين صغيرة
    SIZE_XL = 14    # عناوين
    SIZE_2XL = 16   # عناوين كبيرة
    SIZE_3XL = 18   # عناوين رئيسية
    SIZE_4XL = 24   # أرقام كبيرة


# ==============================================================================
# المسافات
# ==============================================================================

class Spacing:
    """
    نظام المسافات
    ===============
    مسافات متناسقة للتصميم.
    """
    
    XS = 4    # مسافات صغيرة جداً
    SM = 6    # مسافات صغيرة
    MD = 8    # مسافات متوسطة
    LG = 12   # مسافات كبيرة
    XL = 16   # مسافات أكبر
    XXL = 24  # مسافات كبيرة جداً


# ==============================================================================
# أنماط الأزرار الاحترافية
# ==============================================================================

class ButtonStyles:
    """
    أنماط الأزرار مع جميع الحالات
    ===============================
    """
    
    @staticmethod
    def primary_button():
        """الزر الأساسي (أخضر)."""
        return f"""
            QPushButton {{
                background-color: {ThemeColors.SUCCESS};
                color: {ThemeColors.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-size: {Typography.SIZE_BASE}px;
                font-weight: bold;
                font-family: {Typography.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.SUCCESS_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.SUCCESS_DARK};
            }}
            QPushButton:disabled {{
                background-color: {ThemeColors.BORDER_DARK};
                color: {ThemeColors.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def danger_button():
        """زر الخطر/الإيقاف (أحمر)."""
        return f"""
            QPushButton {{
                background-color: {ThemeColors.ERROR};
                color: {ThemeColors.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-size: {Typography.SIZE_BASE}px;
                font-weight: bold;
                font-family: {Typography.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.ERROR_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.ERROR_DARK};
            }}
            QPushButton:disabled {{
                background-color: {ThemeColors.BORDER_DARK};
                color: {ThemeColors.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def warning_button():
        """زر التنبيه (برتقالي)."""
        return f"""
            QPushButton {{
                background-color: {ThemeColors.WARNING};
                color: {ThemeColors.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-size: {Typography.SIZE_BASE}px;
                font-weight: bold;
                font-family: {Typography.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.WARNING_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.WARNING_DARK};
            }}
            QPushButton:disabled {{
                background-color: {ThemeColors.BORDER_DARK};
                color: {ThemeColors.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def info_button():
        """زر المعلومات (أزرق)."""
        return f"""
            QPushButton {{
                background-color: {ThemeColors.INFO};
                color: {ThemeColors.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-size: {Typography.SIZE_BASE}px;
                font-weight: bold;
                font-family: {Typography.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.INFO_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.INFO_DARK};
            }}
            QPushButton:disabled {{
                background-color: {ThemeColors.BORDER_DARK};
                color: {ThemeColors.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def secondary_button():
        """زر ثانوي (رمادي)."""
        return f"""
            QPushButton {{
                background-color: {ThemeColors.BACKGROUND_MEDIUM};
                color: {ThemeColors.TEXT_PRIMARY};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                border-radius: 6px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-size: {Typography.SIZE_BASE}px;
                font-weight: bold;
                font-family: {Typography.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.BACKGROUND_LIGHT};
                border-color: {ThemeColors.BORDER_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.BORDER_DARK};
            }}
            QPushButton:disabled {{
                background-color: {ThemeColors.BACKGROUND_DARK};
                color: {ThemeColors.TEXT_DISABLED};
                border-color: {ThemeColors.BORDER_DARK};
            }}
        """
    
    @staticmethod
    def icon_button():
        """زر الأيقونات (صغير)."""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {ThemeColors.TEXT_SECONDARY};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                border-radius: 4px;
                padding: {Spacing.XS}px;
                font-size: {Typography.SIZE_SM}px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.BACKGROUND_MEDIUM};
                color: {ThemeColors.TEXT_PRIMARY};
                border-color: {ThemeColors.BORDER_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.BORDER_DARK};
            }}
            QPushButton:disabled {{
                background-color: transparent;
                color: {ThemeColors.TEXT_DISABLED};
                border-color: {ThemeColors.BORDER_DARK};
            }}
        """


# ==============================================================================
# أنماط البطاقات والمجموعات
# ==============================================================================

class CardStyles:
    """
    أنماط البطاقات والمجموعات
    ===========================
    """
    
    @staticmethod
    def card():
        """بطاقة عادية."""
        return f"""
            QFrame {{
                background: {ThemeColors.GRADIENT_CARD};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                border-radius: 8px;
                padding: {Spacing.MD}px;
            }}
        """
    
    @staticmethod
    def group_box():
        """صندوق مجموعة."""
        return f"""
            QGroupBox {{
                color: {ThemeColors.TEXT_PRIMARY};
                font-size: {Typography.SIZE_LG}px;
                font-weight: bold;
                font-family: {Typography.FONT_FAMILY};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                border-radius: 8px;
                margin-top: {Spacing.LG}px;
                padding-top: {Spacing.LG}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: {Spacing.MD}px;
                padding: 0 {Spacing.SM}px;
                color: {ThemeColors.INFO};
            }}
        """
    
    @staticmethod
    def info_panel():
        """لوحة معلومات."""
        return f"""
            QFrame {{
                background: {ThemeColors.GRADIENT_CARD};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                border-radius: 8px;
                padding: {Spacing.LG}px;
            }}
        """


# ==============================================================================
# أنماط أدوات الإدخال
# ==============================================================================

class InputStyles:
    """
    أنماط أدوات الإدخال
    =====================
    """
    
    @staticmethod
    def line_edit():
        """حقل إدخال نص."""
        return f"""
            QLineEdit {{
                background-color: {ThemeColors.BACKGROUND_MEDIUM};
                color: {ThemeColors.TEXT_PRIMARY};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                border-radius: 6px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-size: {Typography.SIZE_BASE}px;
                font-family: {Typography.FONT_FAMILY};
                selection-background-color: {ThemeColors.INFO};
            }}
            QLineEdit:focus {{
                border: 2px solid {ThemeColors.INFO};
                background-color: {ThemeColors.BACKGROUND_LIGHT};
            }}
            QLineEdit:disabled {{
                background-color: {ThemeColors.BACKGROUND_DARK};
                color: {ThemeColors.TEXT_DISABLED};
                border-color: {ThemeColors.BORDER_DARK};
            }}
        """
    
    @staticmethod
    def combo_box():
        """قائمة منسدلة."""
        return f"""
            QComboBox {{
                background-color: {ThemeColors.BACKGROUND_MEDIUM};
                color: {ThemeColors.TEXT_PRIMARY};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                border-radius: 6px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-size: {Typography.SIZE_BASE}px;
                font-family: {Typography.FONT_FAMILY};
            }}
            QComboBox:hover {{
                border-color: {ThemeColors.BORDER_LIGHT};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: {Spacing.SM}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ThemeColors.BACKGROUND_MEDIUM};
                color: {ThemeColors.TEXT_PRIMARY};
                selection-background-color: {ThemeColors.INFO};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
            }}
        """
    
    @staticmethod
    def slider():
        """شريط التمرير."""
        return f"""
            QSlider::groove:horizontal {{
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                height: 6px;
                background: {ThemeColors.BACKGROUND_MEDIUM};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {ThemeColors.INFO};
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {ThemeColors.INFO_LIGHT};
            }}
            QSlider::sub-page:horizontal {{
                background: {ThemeColors.SUCCESS};
                border-radius: 3px;
            }}
        """
    
    @staticmethod
    def progress_bar():
        """شريط التقدم."""
        return f"""
            QProgressBar {{
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                border-radius: 6px;
                text-align: center;
                background-color: {ThemeColors.BACKGROUND_MEDIUM};
                height: 20px;
                color: {ThemeColors.TEXT_PRIMARY};
                font-size: {Typography.SIZE_SM}px;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.SUCCESS};
                border-radius: 5px;
            }}
        """


# ==============================================================================
# أنماط القوائم
# ==============================================================================

class ListStyles:
    """
    أنماط القوائم
    ===============
    """
    
    @staticmethod
    def list_widget():
        """ويدجت القائمة."""
        return f"""
            QListWidget {{
                background-color: {ThemeColors.BACKGROUND_MEDIUM};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                border-radius: 6px;
                padding: {Spacing.XS}px;
                font-size: {Typography.SIZE_BASE}px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QListWidget::item {{
                padding: {Spacing.SM}px {Spacing.MD}px;
                border-radius: 4px;
                margin: {Spacing.XS}px 0;
            }}
            QListWidget::item:hover {{
                background-color: {ThemeColors.BACKGROUND_LIGHT};
            }}
            QListWidget::item:selected {{
                background-color: {ThemeColors.INFO};
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """


# ==============================================================================
# أنماط النصوص
# ==============================================================================

class LabelStyles:
    """
    أنماط النصوص
    ===============
    """
    
    @staticmethod
    def primary_text():
        """نص أساسي."""
        return f"color: {ThemeColors.TEXT_PRIMARY}; font-size: {Typography.SIZE_BASE}px;"
    
    @staticmethod
    def secondary_text():
        """نص ثانوي."""
        return f"color: {ThemeColors.TEXT_SECONDARY}; font-size: {Typography.SIZE_SM}px;"
    
    @staticmethod
    def muted_text():
        """نص باهت."""
        return f"color: {ThemeColors.TEXT_MUTED}; font-size: {Typography.SIZE_SM}px;"
    
    @staticmethod
    def heading():
        """عنوان."""
        return f"color: {ThemeColors.TEXT_PRIMARY}; font-size: {Typography.SIZE_XL}px; font-weight: bold;"
    
    @staticmethod
    def value_text():
        """نص قيمة (أرقام)."""
        return f"color: {ThemeColors.SUCCESS}; font-size: {Typography.SIZE_XL}px; font-weight: bold; font-family: {Typography.FONT_FAMILY_MONO};"
    
    @staticmethod
    def status_success():
        """حالة نجاح."""
        return f"color: {ThemeColors.SUCCESS}; font-size: {Typography.SIZE_SM}px; font-weight: bold;"
    
    @staticmethod
    def status_error():
        """حالة خطأ."""
        return f"color: {ThemeColors.ERROR}; font-size: {Typography.SIZE_SM}px; font-weight: bold;"
    
    @staticmethod
    def status_warning():
        """حالة تحذير."""
        return f"color: {ThemeColors.WARNING}; font-size: {Typography.SIZE_SM}px; font-weight: bold;"
    
    @staticmethod
    def mono_text():
        """نص أحادي العرض."""
        return f"color: {ThemeColors.INFO}; font-size: {Typography.SIZE_SM}px; font-family: {Typography.FONT_FAMILY_MONO};"


class StatCardStyles:
    """
    أنماط بطاقات الإحصائيات
    ========================
    بطاقات احترافية لعرض الأرقام.
    """

    @staticmethod
    def total_card():
        return f"""
            QFrame {{
                background: {ThemeColors.GRADIENT_CARD};
                border: 1px solid {ThemeColors.SUCCESS};
                border-radius: 8px;
                padding: {Spacing.SM}px;
            }}
            QFrame:hover {{
                border-color: {ThemeColors.SUCCESS_LIGHT};
            }}
        """

    @staticmethod
    def in_card():
        return f"""
            QFrame {{
                background: {ThemeColors.GRADIENT_CARD};
                border: 1px solid {ThemeColors.INFO};
                border-radius: 8px;
                padding: {Spacing.SM}px;
            }}
            QFrame:hover {{
                border-color: {ThemeColors.INFO_LIGHT};
            }}
        """

    @staticmethod
    def out_card():
        return f"""
            QFrame {{
                background: {ThemeColors.GRADIENT_CARD};
                border: 1px solid {ThemeColors.WARNING};
                border-radius: 8px;
                padding: {Spacing.SM}px;
            }}
            QFrame:hover {{
                border-color: {ThemeColors.WARNING_LIGHT};
            }}
        """

    @staticmethod
    def vehicle_card():
        return f"""
            QFrame {{
                background: {ThemeColors.GRADIENT_CARD};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
                border-radius: 6px;
                padding: {Spacing.XS}px {Spacing.SM}px;
            }}
        """


class MiscStyles:
    """
    أنماط متنوعة
    =============
    """

    @staticmethod
    def scroll_area():
        return f"""
            QScrollArea {{
                background-color: {ThemeColors.BACKGROUND_DARK};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {ThemeColors.BACKGROUND_DARK};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {ThemeColors.BORDER_MEDIUM};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ThemeColors.BORDER_LIGHT};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """

    @staticmethod
    def separator():
        return f"""
            QFrame {{
                color: {ThemeColors.BORDER_MEDIUM};
                max-height: 1px;
            }}
        """

    @staticmethod
    def tool_button():
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {ThemeColors.TEXT_SECONDARY};
                border: none;
                border-radius: 4px;
                padding: {Spacing.XS}px {Spacing.SM}px;
                font-size: {Typography.SIZE_SM}px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.BACKGROUND_LIGHT};
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.BORDER_DARK};
            }}
            QPushButton:checked {{
                background-color: {ThemeColors.BACKGROUND_LIGHT};
                color: {ThemeColors.INFO};
                border: 1px solid {ThemeColors.BORDER_MEDIUM};
            }}
        """

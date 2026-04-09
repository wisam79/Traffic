"""
ملف أنماط واجهة المستخدم - UI Styles
======================================
يحتوي على جميع أنماط CSS لواجهة المستخدم.
مُحدث لاستخدام نظام الثيمات الاحترافي.

المرتبط به:
- يُستورد من: جميع مكونات ui/
- يستخدم: ui/themes.py (نظام الثيمات)
"""

from ui.themes import (
    ThemeColors, Typography, Spacing,
    ButtonStyles, CardStyles, InputStyles,
    ListStyles, LabelStyles, StatCardStyles, MiscStyles
)

VIDEO_HEADER_STYLE = f"""
QWidget {{
    background: {ThemeColors.GRADIENT_HEADER.strip()};
    border: 1px solid {ThemeColors.BORDER_MEDIUM};
    border-radius: 6px;
    padding: {Spacing.SM}px;
}}
QLabel {{
    color: {ThemeColors.TEXT_PRIMARY};
    font-size: {Typography.SIZE_XL}px;
    font-weight: bold;
    padding: 0 {Spacing.SM}px;
    font-family: {Typography.FONT_FAMILY};
}}
QPushButton {{
    background-color: {ThemeColors.BACKGROUND_MEDIUM};
    color: {ThemeColors.TEXT_PRIMARY};
    border: 1px solid {ThemeColors.BORDER_MEDIUM};
    border-radius: 4px;
    padding: {Spacing.XS}px {Spacing.SM}px;
    font-size: {Typography.SIZE_BASE}px;
    font-family: {Typography.FONT_FAMILY};
}}
QPushButton:hover {{
    background-color: {ThemeColors.BACKGROUND_LIGHT};
    border-color: {ThemeColors.BORDER_LIGHT};
}}
"""

VIDEO_DISPLAY_STYLE = f"""
ZoomableGraphicsView {{
    background-color: {ThemeColors.BACKGROUND_DARKEST};
    border: 2px solid {ThemeColors.BORDER_MEDIUM};
    border-radius: 8px;
}}
"""

STATUS_BAR_STYLE = f"""
QWidget {{
    background-color: {ThemeColors.BACKGROUND_DARK};
    border: 1px solid {ThemeColors.BORDER_MEDIUM};
    border-radius: 6px;
    padding: {Spacing.SM}px;
}}
QLabel {{
    color: {ThemeColors.TEXT_SECONDARY};
    font-size: {Typography.SIZE_SM}px;
    padding: {Spacing.XS}px {Spacing.SM}px;
    font-family: {Typography.FONT_FAMILY};
}}
"""

CONTROL_PANEL_STYLE = CardStyles.group_box()

BUTTON_START_STYLE = ButtonStyles.primary_button()
BUTTON_STOP_STYLE = ButtonStyles.danger_button()
BUTTON_CLEAR_STYLE = ButtonStyles.warning_button()
BUTTON_RESET_STYLE = ButtonStyles.info_button()

STAT_LABEL_STYLE = f"QLabel {{ {LabelStyles.primary_text()} }}"
STAT_VALUE_STYLE = f"QLabel {{ {LabelStyles.value_text()} }}"

MAIN_WINDOW_STYLE = f"""
QMainWindow {{
    background-color: {ThemeColors.BACKGROUND_DARKEST};
}}
"""

STAT_TOTAL_VALUE_STYLE = f"""
    QLabel {{
        color: {ThemeColors.SUCCESS};
        font-size: {Typography.SIZE_4XL}px;
        font-weight: bold;
        font-family: {Typography.FONT_FAMILY_MONO};
    }}
"""

STAT_IN_VALUE_STYLE = f"""
    QLabel {{
        color: {ThemeColors.INFO};
        font-size: {Typography.SIZE_2XL}px;
        font-weight: bold;
        font-family: {Typography.FONT_FAMILY_MONO};
    }}
"""

STAT_OUT_VALUE_STYLE = f"""
    QLabel {{
        color: {ThemeColors.WARNING};
        font-size: {Typography.SIZE_2XL}px;
        font-weight: bold;
        font-family: {Typography.FONT_FAMILY_MONO};
    }}
"""

STAT_VEHICLE_VALUE_STYLE = f"""
    QLabel {{
        color: {ThemeColors.ACCENT_CYAN};
        font-size: {Typography.SIZE_LG}px;
        font-weight: bold;
        font-family: {Typography.FONT_FAMILY_MONO};
    }}
"""

STATUS_LIVE_STYLE = f"color: {ThemeColors.ERROR}; font-size: {Typography.SIZE_BASE}px; font-weight: bold;"
STATUS_STOPPED_STYLE = f"color: {ThemeColors.TEXT_MUTED}; font-size: {Typography.SIZE_BASE}px; font-weight: bold;"
STATUS_LINE_SET_STYLE = f"color: {ThemeColors.SUCCESS}; font-family: {Typography.FONT_FAMILY_MONO}; font-weight: bold; font-size: {Typography.SIZE_SM}px;"
STATUS_LINE_UNSET_STYLE = f"color: {ThemeColors.WARNING}; font-family: {Typography.FONT_FAMILY_MONO}; font-size: {Typography.SIZE_SM}px;"
INSTRUCTION_DEFAULT_STYLE = f"color: {ThemeColors.TEXT_MUTED}; font-size: {Typography.SIZE_SM}px;"
INSTRUCTION_ACTIVE_STYLE = f"color: {ThemeColors.WARNING}; font-size: {Typography.SIZE_SM}px; font-weight: bold;"
INSTRUCTION_SUCCESS_STYLE = f"color: {ThemeColors.SUCCESS}; font-size: {Typography.SIZE_SM}px; font-weight: bold;"
INSTRUCTION_ERROR_STYLE = f"color: {ThemeColors.ERROR}; font-size: {Typography.SIZE_SM}px; font-weight: bold;"
COORDS_STYLE = f"color: {ThemeColors.INFO}; font-family: {Typography.FONT_FAMILY_MONO}; font-size: {Typography.SIZE_SM}px;"
RECORDING_ACTIVE_STYLE = f"font-size: {Typography.SIZE_BASE}px; font-weight: bold; color: {ThemeColors.ERROR};"

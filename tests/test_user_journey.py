"""
اختبارات رحلة المستخدم (E2E) - User Journey Tests
===================================================
تختبر هذه الوحدة واجهة المستخدم الرسومية (GUI) تسلسلياً 
باستخدام `pytest-qt` لضمان أن تفاعل المستخدم من البداية
إلى النهاية يعمل بشكل متناغم وخالٍ من الأخطاء.

مسار رحلة المستخدم (The User Journey):
1. إدخال مسار مصدر الفيديو
2. الضغط على "تحميل الفيديو" (ظهور الإطار الأول وتمكين الأزرار)
3. رسم خط العد على شاشة الفيديو
4. الضغط على "بدء التحليل" (بدء الذكاء الاصطناعي وكتابة الإحصائيات)
5. الضغط على "إيقاف البث"
6. مسح الخط وإعادة العدادات
"""

import sys
import os
import queue
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QMessageBox

from ui.main_window import MainWindow
from ui.drawing_modes import DrawingMode

# إضافة المشروع كمسار أساسي
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_opencv():
    """يحاكي OpenCV لتجنب طلب كاميرا حقيقية أو ملف فيديو حقيقي"""
    with patch("cv2.VideoCapture") as mock_cap_class:
        # إنشاء وهمي 
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        
        # عند استدعاء read() ستُرجع إطاراً عشوائياً (اختبار)
        mock_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, mock_frame)
        
        mock_cap_class.return_value = mock_cap
        
        # لـ VideoIngestor
        yield mock_cap_class


@pytest.fixture
def mock_yolo():
    """يحاكي نموذج YOLO26 لتسريع الاختبار وتفادي تحميل النموذج الثقيل"""
    with patch("engine.detector.ObjectDetector.__init__", return_value=None), \
         patch("engine.detector.ObjectDetector.detect") as mock_detect:
         
        from supervision import Detections
        # يُرجع كشوفات فارغة لتمرير الاختبار بسرعة بدون أخطاء حسابية
        mock_detect.return_value = Detections.empty()
        yield mock_detect


def test_user_journey_end_to_end(qtbot, mock_opencv, mock_yolo):
    """
    اختبار لرحلة المستخدم المتكاملة في النظام
    =========================================
    """
    # 1. تشغيل النافذة الرئيسية
    window = MainWindow()
    qtbot.addWidget(window)
    
    # التأكد من الحالة الابتدائية
    assert window.control_panel.btn_start_stop.isEnabled() is False, "يجب أن يكون زر البدء معطلاً في البداية"
    assert window.control_panel.btn_load_video.isEnabled() is True, "زر تحميل الفيديو يعمل"

    # 2. إدخال مصدر الفيديو والتحميل (استخدام كاميرا وهمية 0 لتجاوز فحص مسار الملف)
    window.control_panel.txt_source.setText("0")
    qtbot.mouseClick(window.control_panel.btn_load_video, Qt.MouseButton.LeftButton)
    
    # بعد التحميل، يجب أن يتم تمكين زر البدء، وتعطيل زر التحميل
    assert window.control_panel.btn_start_stop.isEnabled() is True, "زر البدء يجب تمكينه"
    assert window.control_panel.btn_load_video.isEnabled() is False, "زر التحميل يجب تعطيله"
    
    # 3. رسم خط العد (الماوس على VideoPanel)
    # التأكد أن وضع الرسم هو "خط واحد" المفضل افتراضيا
    drawer = window.video_panel.advanced_line_drawer
    assert drawer.drawing_mode == DrawingMode.SINGLE_LINE
    
    # محاكاة نقرات داخل حيز الفيديو
    drawer.set_frame_bounds(640, 480) # تأكيد الحدود
    result_click1 = drawer.handle_click(100, 200)
    result_click2 = drawer.handle_click(500, 200)
    
    assert result_click1 == "point_a_set"
    assert result_click2 == "line_complete"
    assert len(drawer.lines) == 1
    
    # تمرير الإحداثيات للنافذة لربطها بـ AI (يحاكي _on_line_defined)
    window._on_line_defined((100, 200), (500, 200))

    # 4. بدء التحليل
    qtbot.mouseClick(window.control_panel.btn_start_stop, Qt.MouseButton.LeftButton)
    
    # يجب أن تتغير حالة الأزرار
    assert window.is_ingestor_running is True, "مُدخل الفيديو يجب أن يكون قيد التشغيل"
    assert window.ai_engine is not None, "الذكاء الاصطناعي يجب أن يعمل"
    assert window.control_panel.btn_start_stop.text() == "⏹ إيقاف البث"
    
    # ننتظر قليلا لمحاكاة مرور بضع إطارات عبر الخيط (Thread)
    qtbot.wait(1500)
    
    # 5. إيقاف البث
    qtbot.mouseClick(window.control_panel.btn_start_stop, Qt.MouseButton.LeftButton)
    
    # بعد الإيقاف، يجب أن تتوقف الموارد ويفعل زر التحميل
    assert window.is_ingestor_running is False
    assert window._is_streaming is False
    assert window.control_panel.btn_load_video.isEnabled() is True
    assert window.control_panel.btn_start_stop.isEnabled() is False  # معطل لأن البث توقف وتحتاج للتحميل مجددا
    
    # 6. تجربة أزرار المسح
    qtbot.mouseClick(window.control_panel.btn_clear_line, Qt.MouseButton.LeftButton)
    assert len(drawer.lines) == 0, "يجب مسح الخطوط المنشأة"
    
    qtbot.mouseClick(window.control_panel.btn_reset_counts, Qt.MouseButton.LeftButton)
    assert window.control_panel.lbl_total_value.text() == "0", "العداد يجب أن يكون للصفر"
    

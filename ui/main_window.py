"""
ملف النافذة الرئيسية - Main Window
===================================
النافذة الرئيسية للتطبيق.
تُدير التواصل بين لوحة الفيديو ولوحة التحكم وخيط الذكاء الاصطناعي.

المسؤوليات:
- تجميع لوحة الفيديو ولوحة التحكم
- ربط Signals/Slots
- بدء/إيقاف البث
- معالجة أحداث الأزرار
- تحديث واجهة المستخدم

المرتبط به:
- يُستورد من: core/app.py
- يحتوي على: ui/video_panel.py, ui/control_panel.py
- يتواصل مع: engine/ai_thread.py
"""

import os
import logging
import threading
import time
from typing import Optional

import numpy as np

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Slot, QTimer, QSettings
from PySide6.QtGui import QFont

from core.config import (
    MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, APP_FONT_NAME, APP_FONT_SIZE,
    MODEL_PATH
)
from ui.video_panel import VideoPanel
from ui.video_toolbar import VideoToolbar
from ui.control_panel import ControlPanel
from ui.styles import (
    MAIN_WINDOW_STYLE, BUTTON_START_STYLE, BUTTON_STOP_STYLE,
    STATUS_LIVE_STYLE, STATUS_STOPPED_STYLE,
    STATUS_LINE_SET_STYLE, STATUS_LINE_UNSET_STYLE,
    INSTRUCTION_SUCCESS_STYLE, INSTRUCTION_DEFAULT_STYLE
)
from ui.themes import Spacing
from ui.video_source_manager import VideoSourceManager, VideoInfo
from engine.ai_thread import AIEngineThread
from video.ingestor import VideoIngestor
from state.app_state import app_state

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    النافذة الرئيسية للتطبيق
    ==========================
    تربط جميع المكونات معاً.
    """

    def __init__(self):
        """تهيئة النافذة الرئيسية."""
        super().__init__()

        # ======================================================================
        # إعداد النافذة
        # ======================================================================
        self.setWindowTitle("نظام عد المركبات الذكي - تقاطعات المرور")
        self.resize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)
        
        # تطبيق النمط العام مع تحسينات
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        # ======================================================================
        # الطابور المشترك
        # ======================================================================
        # هذا الطابور هو القناة الوحيدة بين VideoIngestor و AIEngine
        import queue
        self.raw_frame_queue = queue.Queue(maxsize=2)

        # ======================================================================
        # مدير مصادر الفيديو
        # ======================================================================
        self.video_source_manager = VideoSourceManager()

        # معلومات الفيديو الحالية
        self.current_video_info: Optional[VideoInfo] = None

        # ======================================================================
        # حماية إعادة الدخول
        # ======================================================================
        self._is_starting = False
        self._is_stopping = False
        self._is_streaming = False
        self.is_ingestor_running = False
        self._error_shown = False
        self._last_frame_time = 0
        self._settings = QSettings("SmartTraffic", "TrafficCounter")

        self.setAcceptDrops(True)

        # ======================================================================
        # المكونات - ستُهيأ لاحقاً
        # ======================================================================
        self.video_panel: Optional[VideoPanel] = None
        self.video_toolbar: Optional[VideoToolbar] = None
        self.control_panel: Optional[ControlPanel] = None
        self.video_ingestor: Optional[VideoIngestor] = None
        self.ai_engine: Optional[AIEngineThread] = None
        self.ingestor_thread: Optional[threading.Thread] = None

        # إعداد الواجهة
        self._setup_ui()

        # مؤقت تحديث FPS
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self._update_fps_display)
        self.fps_timer.start(500)  # كل 500ms

    def _setup_ui(self) -> None:
        """
        إنشاء وترتيب جميع عناصر النافذة
        ==================================
        تُنشئ التخطيط الأفقي: لوحة الفيديو (يسار) + لوحة التحكم (يمين).
        """
        # العنصر المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setMinimumSize(900, 600)

        # التخطيط الرئيسي مع مسافات محسنة
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(Spacing.LG)
        main_layout.setContentsMargins(
            Spacing.LG,    # يسار
            Spacing.LG,    # أعلى
            Spacing.LG,    # يمين
            Spacing.LG     # أسفل
        )

        # ======================================================================
        # لوحة التحكم (يسار)
        # ======================================================================
        self.control_panel = ControlPanel()
        main_layout.addWidget(self.control_panel)

        # ======================================================================
        # لوحة الفيديو (وسط - أكبر مساحة)
        # ======================================================================
        self.video_panel = VideoPanel()
        main_layout.addWidget(self.video_panel, stretch=5)

        # ======================================================================
        # شريط أدوات الفيديو (يمين)
        # ======================================================================
        self.video_toolbar = VideoToolbar()
        main_layout.addWidget(self.video_toolbar)

        # ======================================================================
        # ربط إشارات شريط الأدوات
        # ======================================================================
        self.video_toolbar.brightness_changed.connect(self.video_panel.on_brightness_change)
        self.video_toolbar.contrast_changed.connect(self.video_panel.on_contrast_change)
        self.video_toolbar.saturation_changed.connect(self.video_panel.on_saturation_change)
        self.video_toolbar.reset_adjust_requested.connect(self._on_toolbar_reset_adjust)
        self.video_toolbar.screenshot_requested.connect(self._on_toolbar_screenshot)
        self.video_toolbar.record_requested.connect(self._on_toolbar_record)

        # ======================================================================
        # ربط الأحداث
        # ======================================================================
        self.control_panel.btn_load_video.clicked.connect(self._on_load_video)
        self.control_panel.btn_start_stop.clicked.connect(self._on_start_stop)
        self.control_panel.btn_clear_line.clicked.connect(self._on_clear_line)
        self.control_panel.btn_reset_counts.clicked.connect(self._on_reset_counts)

        # ربط callback إزالة ملف من القائمة الأخيرة
        self.control_panel.on_remove_recent_file = self.video_source_manager.remove_from_recent

        # ربط callback الخط
        self.video_panel.set_line_callback(self._on_line_defined)

        # ربط زر عرض المعلومات
        self.control_panel.btn_show_info.clicked.connect(self._on_show_video_info)

        # ربط الأزرار الإضافية
        self.control_panel.btn_export.clicked.connect(self._export_stats)
        self.control_panel.btn_about.clicked.connect(self._show_about)
        self.control_panel.btn_save_session.clicked.connect(self._save_session)
        self.control_panel.btn_load_session.clicked.connect(self._load_session)

        # اختصارات لوحة المفاتيح
        from PySide6.QtGui import QShortcut, QKeySequence
        space_shortcut = QShortcut(QKeySequence("Space"), self)
        space_shortcut.activated.connect(self._on_start_stop_safe)
        QShortcut(QKeySequence("Ctrl+O"), self, self._on_load_video)
        QShortcut(QKeySequence("Ctrl+S"), self, self._on_screenshot_shortcut)
        QShortcut(QKeySequence("F11"), self, self._toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self, self._on_escape)

        # تحديث قائمة الملفات الأخيرة
        self._update_recent_files_list()

        self._restore_settings()

    # ======================================================================
    # معالجة أحداث الأزرار
    # ======================================================================

    def _on_load_video(self) -> None:
        """
        معالجة زر تحميل الفيديو (لعرض الإطار الأول)
        """
        if self._is_streaming:
            QMessageBox.warning(self, "خطأ", "أوقف البث أولاً قبل تحميل فيديو جديد.")
            return

        source = self.control_panel.txt_source.text().strip(' "\'')
        if not source:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال مصدر فيديو.")
            return

        # إضافة للملفات الأخيرة واستخراج الإطار
        self._add_to_recent_files(str(source))

        import cv2
        _src = source
        try:
            _src = int(source)
        except ValueError:
            if not source.startswith(("rtsp://", "http://", "https://")) and not os.path.exists(source):
                QMessageBox.warning(self, "خطأ", f"الملف غير موجود: {source}")
                return

        cap = cv2.VideoCapture(_src)
        try:
            if not cap.isOpened():
                QMessageBox.warning(self, "خطأ", "فشل الوصول إلى مصدر الفيديو.")
                return

            ret, frame = cap.read()
        finally:
            cap.release()
        
        if ret and frame is not None:
            h, w = frame.shape[:2]
            self.video_panel.advanced_line_drawer.set_frame_bounds(w, h)
            self.video_panel.video_manager.update_frame(frame)
            # تمكين زر البدء وتعطيل زر التحميل
            self.control_panel.btn_start_stop.setEnabled(True)
            self.control_panel.btn_start_stop.setStyleSheet(BUTTON_START_STYLE)
            self.control_panel.btn_load_video.setEnabled(False)
            logger.info("تم تحميل الفيديو والتقاط الإطار الأول بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "فشل قراءة الإطار الأول من الفيديو.")

    def _on_start_stop(self) -> None:
        """
        معالجة زر البدء/الإيقاف
        =========================
        يُبدل بين حالتي البدء والإيقاف.
        """
        if self._is_starting or self._is_stopping:
            return

        if not self._is_streaming:
            self._start_stream()
        else:
            self._stop_stream()

    def _on_start_stop_safe(self) -> None:
        """
        معالجة اختصار المسافة بأمان
        =============================
        يتجاهل الاختصار إذا كان التركيز على حقل إدخال نصي.
        """
        from PySide6.QtWidgets import QLineEdit, QTextEdit
        focus_widget = QApplication.focusWidget()
        if isinstance(focus_widget, (QLineEdit, QTextEdit)):
            return
        self._on_start_stop()

    def _on_clear_line(self) -> None:
        """
        معالجة زر مسح الخط
        =====================
        يمسح الخط المرئي والخط في AI Engine.
        """
        reply = QMessageBox.question(
            self, "تأكيد", "هل تريد مسح جميع الخطوط؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        # مسح الخطوط المرئية عبر AdvancedLineDrawer
        self.video_panel.advanced_line_drawer.clear_all()

        # مسح الخط في AI Engine
        if self.ai_engine:
            self.ai_engine.line_zone_manager.clear_line()

        # تحديث شريط الحالة
        self.video_panel.lbl_line_status.setText("الخط: لم يُحدد")
        self.video_panel.lbl_line_status.setStyleSheet(STATUS_LINE_UNSET_STYLE)
        self.video_panel.lbl_instruction.setText("💡 انقر مرتين على الفيديو لرسم خط العد")
        self.video_panel.lbl_instruction.setStyleSheet(INSTRUCTION_DEFAULT_STYLE)

        logger.info("تم مسح الخط")

    def _on_reset_counts(self) -> None:
        """
        معالجة زر إعادة العد
        ======================
        يعيد جميع العدادات إلى الصفر في المحرك والواجهة.
        """
        reply = QMessageBox.question(
            self, "تأكيد", "هل تريد إعادة تعيين جميع العدادات؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        # إعادة تعيين العدادات في AI Engine
        if self.ai_engine and self.ai_engine.isRunning():
            self.ai_engine.reset_counts()

        # تحديث الإحصائيات في الواجهة
        self.control_panel.update_stats({
            'total': 0, 'in_count': 0, 'out_count': 0,
            'car': 0, 'truck': 0, 'motorcycle': 0, 'bus': 0
        })

        logger.info("تم إعادة العد")

    # ======================================================================
    # إدارة البث
    # ======================================================================

    def _start_stream(self) -> None:
        """
        بدء بث الفيديو والمعالجة
        ==========================
        الخطوات:
        1. التحقق من مصدر الفيديو
        2. بدء VideoIngestor
        3. بدء AIEngineThread
        4. ربط Signals/Slots
        5. تحديث الواجهة
        """
        if self._is_starting:
            return
        self._is_starting = True

        # التحقق من وجود ملف النموذج
        if not os.path.exists(MODEL_PATH):
            QMessageBox.critical(self, "خطأ", f"ملف النموذج غير موجود:\n{MODEL_PATH}")
            self._is_starting = False
            return

        # الحصول على المصدر
        source = self.control_panel.txt_source.text().strip(' "\'')
        if not source:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال مصدر فيديو.")
            self._is_starting = False
            return

        # التحقق من النوع (رقم أو مسار)
        try:
            source = int(source)
        except ValueError:
            # التحقق من وجود الملف
            if not source.startswith(("rtsp://", "http://", "https://")):
                if not os.path.exists(source):
                    QMessageBox.warning(self, "خطأ", f"الملف غير موجود: {source}")
                    self._is_starting = False
                    return

        logger.info(f"جاري بدء البث من: {source}")

        # إضافة للملفات الأخيرة
        self._add_to_recent_files(str(source))

        # تحديث الحالة
        app_state.set_video_source(str(source))
        app_state.set_streaming(True)

        # ==================================================================
        # بدء VideoIngestor
        # ==================================================================
        self.is_ingestor_running = True

        self.video_ingestor = VideoIngestor(
            source=source,
            raw_frame_queue=self.raw_frame_queue
        )

        if not self.video_ingestor.start():
            QMessageBox.critical(self, "خطأ", "فشل بدء بث الفيديو.")
            app_state.set_streaming(False)
            self._is_starting = False
            return

        # تشغيل خيط الالتقاط
        self.ingestor_thread = threading.Thread(
            target=self.video_ingestor.read_loop,
            daemon=True,
            name="VideoIngestorThread"
        )
        self.ingestor_thread.start()

        # ==================================================================
        # بدء AIEngineThread
        # ==================================================================
        self.ai_engine = AIEngineThread(
            raw_frame_queue=self.raw_frame_queue
        )

        # ربط Signals
        self.ai_engine.frame_ready.connect(self._on_frame_ready)
        self.ai_engine.stats_ready.connect(self._on_stats_ready)
        self.ai_engine.error_occurred.connect(self._on_error)

        # تشغيل الخيط
        self.ai_engine.start()

        # استعادة خط العد من الحالة المشتركة (إن وُجد)
        saved_line = app_state.get_line_coordinates()
        if saved_line is not None:
            self.ai_engine.set_line_coordinates("saved", saved_line)

        # ==================================================================
        # تحديث الواجهة
        # ==================================================================
        self.control_panel.btn_start_stop.setText("⏹ إيقاف البث")
        self.control_panel.btn_start_stop.setStyleSheet(BUTTON_STOP_STYLE)
        self.control_panel.txt_source.setEnabled(False)
        self.control_panel.btn_select_source.setEnabled(False)
        self.control_panel.btn_load_video.setEnabled(False)

        self.video_panel.lbl_status_indicator.setText("🔴 مباشر")
        self.video_panel.lbl_status_indicator.setStyleSheet(STATUS_LIVE_STYLE)

        self._is_starting = False
        self._is_streaming = True

        logger.info("تم بدء البث بنجاح")

    def _stop_stream(self) -> None:
        """
        إيقاف بث الفيديو والمعالجة
        ============================
        توقف جميع الخيوط وتحرر الموارد.
        """
        if self._is_stopping:
            return
        self._is_stopping = True

        logger.info("جاري إيقاف البث...")

        # إيقاف AI Engine
        if self.ai_engine:
            self.ai_engine.stop_processing()
            self.ai_engine.quit()
            self.ai_engine.wait(3000)
            self.ai_engine = None

        # إيقاف Video Ingestor
        self.is_ingestor_running = False
        if self.video_ingestor:
            self.video_ingestor.stop()
            self.video_ingestor = None

        if self.ingestor_thread and self.ingestor_thread.is_alive():
            self.ingestor_thread.join(timeout=2.0)
            self.ingestor_thread = None

        # تحديث الحالة
        app_state.set_streaming(False)

        # تحديث الواجهة
        self.control_panel.btn_start_stop.setText("▶ بدء التحليل")
        self.control_panel.btn_start_stop.setStyleSheet(BUTTON_START_STYLE)
        self.control_panel.txt_source.setEnabled(True)
        self.control_panel.btn_select_source.setEnabled(True)
        self.control_panel.btn_load_video.setEnabled(True)
        self.control_panel.btn_start_stop.setEnabled(False)

        self.video_panel.lbl_status_indicator.setText("⚫ متوقف")
        self.video_panel.lbl_status_indicator.setStyleSheet(STATUS_STOPPED_STYLE)

        self._is_stopping = False
        self._is_streaming = False

        logger.info("تم إيقاف البث")

    # ======================================================================
    # Slots استقبال البيانات من AI Engine
    # ======================================================================

    @Slot(object)
    def _on_frame_ready(self, frame: np.ndarray) -> None:
        """
        Slot استقبال إطار جاهز
        ========================
        يُطبق تعديلات الفيديو ثُم يُعرض الإطار على لوحة الفيديو.

        المُعاملات (Args):
            frame: إطار مُرسوم عليه بصيغة BGR

        المرتبط به:
        - يُستدعى من: ai_thread.py (Signal frame_ready)
        - يُطبق عليه: video_controller.process_frame()
        - يُرسل إلى: video_panel.video_manager
        """
        try:
            # تحديث حدود الإطار عند أول إطار (إن لم تكن مُحددة)
            if frame is not None and isinstance(frame, np.ndarray):
                h, w = frame.shape[:2]
                drawer = self.video_panel.advanced_line_drawer
                if drawer.frame_width != w or drawer.frame_height != h:
                    drawer.set_frame_bounds(w, h)

            # تطبيق تعديلات الفيديو (سطوع، تباين، تشبع)
            processed_frame = self.video_panel.video_controller.process_frame(frame)

            # عرض الإطار
            self.video_panel.video_manager.update_frame(processed_frame)

            if self.video_toolbar:
                recording_text = self.video_panel.video_controller.recorder.get_recording_status_text()
                self.video_toolbar.lbl_recording.setText(recording_text)

            self._last_frame_time = time.time()

        except Exception as e:
            logger.error(f"خطأ في عرض الإطار: {e}")

    @Slot(object)
    def _on_stats_ready(self, stats: dict) -> None:
        """
        Slot استقبال إحصائيات جديدة
        =============================
        يُحدث لوحة التحكم بالأعداد الجديدة.

        المُعاملات (Args):
            stats: قاموس الإحصائيات

        المرتبط به:
        - يُستدعى من: ai_thread.py (Signal stats_ready)
        - يُرسل إلى: control_panel
        """
        try:
            self.control_panel.update_stats(stats)
            if stats.get('total', 0) > 0 and stats.get('total', 0) % 100 == 0:
                self.video_panel.lbl_instruction.setText(f"🎯 تم عد {stats['total']} مركبة!")
                self.video_panel.lbl_instruction.setStyleSheet(INSTRUCTION_SUCCESS_STYLE)
        except Exception as e:
            logger.error(f"خطأ في تحديث الإحصائيات: {e}")

    @Slot(str)
    def _on_error(self, error_msg: str) -> None:
        """
        Slot استقبال رسالة خطأ
        ========================
        يُظهر رسالة خطأ للمستخدم.

        المُعاملات (Args):
            error_msg: نص رسالة الخطأ

        المرتبط به:
        - يُستدعى من: ai_thread.py (Signal error_occurred)
        """
        logger.error(f"خطأ AI Engine: {error_msg}")
        if not self._error_shown:
            self._error_shown = True
            QMessageBox.critical(self, "خطأ AI Engine", error_msg)
            QTimer.singleShot(5000, self._reset_error_flag)

    def _reset_error_flag(self) -> None:
        self._error_shown = False

    def _on_line_defined(self, line_id, point_a, point_b) -> None:
        logger.info(f"تم تحديد الخط [{line_id}]: {point_a} -> {point_b}")

        # تخزين الإحداثيات في الحالة المشتركة
        app_state.set_line_coordinates((point_a, point_b))

        # إرسال إلى AI Engine إذا كان يعمل
        if self.ai_engine and self.ai_engine.isRunning():
            self.ai_engine.set_line_coordinates(line_id, (point_a, point_b))

        # تحديث شريط الحالة
        self.video_panel.lbl_line_status.setText(f"الخط: {point_a} → {point_b}")
        self.video_panel.lbl_line_status.setStyleSheet(STATUS_LINE_SET_STYLE)
        self.video_panel.lbl_instruction.setText("✅ تم تعيين الخط! سيتم عد المركبات")
        self.video_panel.lbl_instruction.setStyleSheet(INSTRUCTION_SUCCESS_STYLE)

    def _update_fps_display(self) -> None:
        """
        تحديث عرض FPS
        ===============
        يُحدث label FPS كل 500ms.
        """
        if self.video_panel and self.video_panel.video_manager:
            stats = self.video_panel.video_manager.get_stats()
            fps = stats.get('fps', 0)
            if self.video_panel and self.video_panel.video_manager:
                zoom = self.video_panel.video_manager.get_zoom_level()
                self.video_panel.lbl_fps.setText(f"FPS: {fps} | {zoom}%")
            else:
                self.video_panel.lbl_fps.setText(f"FPS: {fps}")

            if self._is_streaming and self._last_frame_time > 0:
                if time.time() - self._last_frame_time > 5:
                    self.video_panel.lbl_status_indicator.setText("⚠️ انقطع البث")
                    self.video_panel.lbl_status_indicator.setStyleSheet("color: #FF9800; font-size: 12px; font-weight: bold;")

    # ======================================================================
    # إدارة مصادر الفيديو
    # ======================================================================

    def _on_show_video_info(self) -> None:
        """
        معالجة زر عرض معلومات الفيديو
        ================================
        يُظهر/يُخفي معلومات الفيديو ويحدث البيانات.
        يُشغل تحميل المعلومات في خيط خلفي لمنع تجميد الواجهة.
        """
        # الحصول على المصدر الحالي
        source = self.control_panel.txt_source.text().strip()
        if not source:
            QMessageBox.information(self, "معلومات الفيديو", "الرجاء إدخال مصدر فيديو أولاً.")
            return

        # التحقق من حالة العرض
        is_visible = self.video_panel.video_info_display.isVisible()
        
        if not is_visible:
            # تعطيل الزر ومنع النقرات المتكررة
            self.control_panel.btn_show_info.setEnabled(False)
            self.video_panel.lbl_status_indicator.setText("⏳ جاري التحميل...")

            def _load_info():
                try:
                    info = self.video_source_manager.get_video_info(source)
                    # تحديث الواجهة في الخيط الرئيسي
                    QTimer.singleShot(0, lambda: self._on_video_info_loaded(info))
                except Exception as e:
                    QTimer.singleShot(0, lambda: self._on_video_info_error(str(e)))

            threading.Thread(target=_load_info, daemon=True, name="VideoInfoLoader").start()
        else:
            # إخفاء العرض
            self.video_panel.show_video_info(False)

    def _on_video_info_loaded(self, info) -> None:
        """يُستدعى عند تحميل معلومات الفيديو بنجاح (في الخيط الرئيسي)."""
        self.current_video_info = info
        self.video_panel.video_info_display.update_info(info)
        self.video_panel.show_video_info(True)
        self.video_panel.lbl_status_indicator.setText("✅ تم التحميل")
        self.control_panel.btn_show_info.setEnabled(True)

    def _on_video_info_error(self, error_msg: str) -> None:
        """يُستدعى عند فشل تحميل معلومات الفيديو (في الخيط الرئيسي)."""
        QMessageBox.warning(self, "خطأ", f"فشل الحصول على معلومات الفيديو: {error_msg}")
        self.video_panel.lbl_status_indicator.setText("⚫ متوقف")
        self.control_panel.btn_show_info.setEnabled(True)

    def _update_recent_files_list(self) -> None:
        """تحديث قائمة الملفات الأخيرة في الواجهة."""
        recent_files = self.video_source_manager.get_recent_files()
        self.control_panel.update_recent_files(recent_files)

    def _add_to_recent_files(self, source: str) -> None:
        """
        إضافة مصدر إلى القائمة الأخيرة

        المُعاملات (Args):
            source: مصدر الفيديو
        """
        if os.path.exists(str(source)):
            self.video_source_manager._add_to_recent_files(str(source))
            self._update_recent_files_list()

    def _restore_settings(self) -> None:
        self.resize(
            self._settings.value("window/width", 1280, type=int),
            self._settings.value("window/height", 720, type=int)
        )
        last_source = self._settings.value("last_source", "", type=str)
        if last_source:
            self.control_panel.txt_source.setText(last_source)

    def _save_settings(self) -> None:
        self._settings.setValue("window/width", self.width())
        self._settings.setValue("window/height", self.height())
        source = self.control_panel.txt_source.text().strip()
        if source:
            self._settings.setValue("last_source", source)

    def _on_screenshot_shortcut(self) -> None:
        self.video_panel._on_screenshot()

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _on_escape(self) -> None:
        if self.isFullScreen():
            self.showNormal()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv')):
                self.control_panel.txt_source.setText(path)
                self._on_load_video()
                break

    def _export_stats(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        import csv
        import json
        from datetime import datetime

        filepath, _ = QFileDialog.getSaveFileName(
            self, "تصدير الإحصائيات", f"traffic_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "CSV (*.csv);;JSON (*.json)"
        )
        if not filepath:
            return

        stats = app_state.get_stats()
        try:
            if filepath.endswith('.json'):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, ensure_ascii=False, indent=2)
            else:
                with open(filepath, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["القيمة", "العدد"])
                    for key, value in stats.items():
                        writer.writerow([key, value])
            logger.info(f"تم تصدير الإحصائيات: {filepath}")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل التصدير: {e}")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "حول التطبيق",
            "<h3>نظام عد المركبات الذكي</h3>"
            "<p>الإصدار 2.0</p>"
            "<p>نظام متقدم لعد المركبات عند التقاطعات</p>"
            "<p>يستخدم تقنيات YOLO26 + ByteTrack للكشف والتتبع</p>"
            "<hr>"
            "<p>🛠 التقنيات: PySide6, ONNX Runtime, OpenCV, Supervision</p>"
        )

    def _save_session(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        import json
        from datetime import datetime

        filepath, _ = QFileDialog.getSaveFileName(
            self, "حفظ الجلسة", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON (*.json)"
        )
        if not filepath:
            return

        session = {
            "source": self.control_panel.txt_source.text(),
            "stats": app_state.get_stats(),
            "lines": [],
            "saved_at": datetime.now().isoformat()
        }
        for line in self.video_panel.advanced_line_drawer.lines:
            if len(line.points) >= 2:
                session["lines"].append({
                    "id": line.line_id,
                    "points": line.points
                })

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
            logger.info(f"تم حفظ الجلسة: {filepath}")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل حفظ الجلسة: {e}")

    def _load_session(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        import json

        filepath, _ = QFileDialog.getOpenFileName(
            self, "تحميل الجلسة", "", "JSON (*.json)"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session = json.load(f)

            if session.get("source"):
                self.control_panel.txt_source.setText(session["source"])

            if session.get("lines"):
                self.video_panel.advanced_line_drawer.clear_all()
                for line_data in session["lines"]:
                    points = line_data.get("points", [])
                    if not isinstance(points, list) or len(points) < 2:
                        continue
                    try:
                        p0 = points[0]
                        p1 = points[1]
                        if (isinstance(p0, (list, tuple)) and len(p0) == 2
                                and isinstance(p1, (list, tuple)) and len(p1) == 2
                                and all(isinstance(v, (int, float)) for v in p0 + p1)):
                            self.video_panel.advanced_line_drawer.handle_click(int(p0[0]), int(p0[1]))
                            self.video_panel.advanced_line_drawer.handle_click(int(p1[0]), int(p1[1]))
                    except (TypeError, ValueError, IndexError):
                        logger.warning(f"تجاهل خط غير صالح في الجلسة: {line_data}")
                        continue

            if session.get("stats"):
                self.control_panel.update_stats(session["stats"])

            logger.info(f"تم تحميل الجلسة: {filepath}")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل تحميل الجلسة: {e}")

    def _on_toolbar_reset_adjust(self) -> None:
        self.video_panel.on_reset_adjust()
        self.video_toolbar.reset_sliders()

    def _on_toolbar_screenshot(self) -> None:
        count = self.video_panel.on_screenshot()
        if count:
            self.video_toolbar.lbl_screenshot_count.setText(f"صور: {count}")

    def _on_toolbar_record(self) -> None:
        result = self.video_panel.on_record()
        if result is not None:
            is_recording = self.video_panel.video_controller.recorder.is_recording
            self.video_toolbar.set_recording_active(is_recording)
            if not is_recording:
                count = self.video_panel.video_controller.recorder.total_recordings
                self.video_toolbar.lbl_recording_count.setText(f"تسجيلات: {count}")

    def closeEvent(self, event) -> None:
        """
        معالجة إغلاق النافذة
        ======================
        تُوقف جميع الخيوط قبل الإغلاق.
        """
        logger.info("جاري إغلاق التطبيق...")
        self.fps_timer.stop()
        self._save_settings()
        self._stop_stream()
        event.accept()
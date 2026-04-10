"""
ملف عرض معلومات الفيديو - Video Info Display
===============================================
يُعرض معلومات الفيديو بشكل مفصل وجميل.

المسؤوليات:
- عرض جميع معلومات الفيديو
- تحديث المعلومات في الزمن الحقيقي
- عرض حالة التحميل

المرتبط به:
- يُستورد من: video_panel.py
- يستقبل معلومات من: video_source_manager.py
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QFrame
)
from PySide6.QtCore import Qt

from ui.video_source_manager import VideoInfo
from ui.themes import ThemeColors, Typography, Spacing, CardStyles, LabelStyles, MiscStyles, StatusBarStyles


class VideoInfoDisplay(QWidget):
    """
    عرض معلومات الفيديو
    ====================
    يُظهر بطاقة معلومات أنيقة مع شريط تقدم.
    """

    def __init__(self):
        """تهيئة العرض."""
        super().__init__()
        
        # العناصر (تُهيأ كـ None ثم تُعيَّن في _setup_ui)
        self._lbl_source_name = None
        self._lbl_resolution = None
        self._lbl_fps = None
        self._lbl_duration = None
        self._lbl_frames = None
        self._lbl_codec = None
        self._lbl_file_size = None
        self._lbl_source_type = None
        self._progress_bar = None
        self._lbl_status = None

        # إنشاء الواجهة
        self._setup_ui()

    def _setup_ui(self) -> None:
        """إنشاء العناصر."""
        layout = QVBoxLayout(self)
        layout.setSpacing(Spacing.SM)
        layout.setContentsMargins(8, 8, 8, 8)

        # ==================================================================
        # بطاقة المعلومات
        # ==================================================================
        info_card = QFrame()
        info_card.setStyleSheet(CardStyles.info_panel())
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(Spacing.SM)

        # اسم المصدر
        self._lbl_source_name = QLabel("المصدر: --")
        self._lbl_source_name.setStyleSheet(StatusBarStyles.info_source_name())
        info_layout.addWidget(self._lbl_source_name)

        # خط فاصل
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet(MiscStyles.info_separator())
        info_layout.addWidget(line1)

        # صف المعلومات الأول
        row1 = QHBoxLayout()
        
        self._lbl_source_type = QLabel("النوع: --")
        row1.addWidget(self._lbl_source_type)
        
        self._lbl_resolution = QLabel("الدقة: --")
        row1.addWidget(self._lbl_resolution)
        
        self._lbl_fps = QLabel("FPS: --")
        row1.addWidget(self._lbl_fps)
        
        info_layout.addLayout(row1)

        # صف المعلومات الثاني
        row2 = QHBoxLayout()
        
        self._lbl_duration = QLabel("المدة: --")
        row2.addWidget(self._lbl_duration)
        
        self._lbl_frames = QLabel("الإطارات: --")
        row2.addWidget(self._lbl_frames)
        
        self._lbl_codec = QLabel("الكوديك: --")
        row2.addWidget(self._lbl_codec)
        
        info_layout.addLayout(row2)

        # صف المعلومات الثالث
        row3 = QHBoxLayout()
        self._lbl_file_size = QLabel("الحجم: --")
        row3.addWidget(self._lbl_file_size)
        info_layout.addLayout(row3)

        layout.addWidget(info_card)

        # ==================================================================
        # شريط التقدم
        # ==================================================================
        progress_layout = QVBoxLayout()
        
        self._lbl_status = QLabel("جاهز للتحميل")
        self._lbl_status.setStyleSheet(StatusBarStyles.info_status_text())
        progress_layout.addWidget(self._lbl_status)

        self._progress_bar = QProgressBar()
        self._progress_bar.setStyleSheet(f"""
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
        """)
        self._progress_bar.setValue(0)
        progress_layout.addWidget(self._progress_bar)

        layout.addLayout(progress_layout)

    @property
    def lbl_source_name(self) -> QLabel:
        if self._lbl_source_name is None:
            raise RuntimeError("UI not initialized - lbl_source_name not set")
        return self._lbl_source_name

    @property
    def lbl_resolution(self) -> QLabel:
        if self._lbl_resolution is None:
            raise RuntimeError("UI not initialized - lbl_resolution not set")
        return self._lbl_resolution

    @property
    def lbl_fps(self) -> QLabel:
        if self._lbl_fps is None:
            raise RuntimeError("UI not initialized - lbl_fps not set")
        return self._lbl_fps

    @property
    def lbl_duration(self) -> QLabel:
        if self._lbl_duration is None:
            raise RuntimeError("UI not initialized - lbl_duration not set")
        return self._lbl_duration

    @property
    def lbl_frames(self) -> QLabel:
        if self._lbl_frames is None:
            raise RuntimeError("UI not initialized - lbl_frames not set")
        return self._lbl_frames

    @property
    def lbl_codec(self) -> QLabel:
        if self._lbl_codec is None:
            raise RuntimeError("UI not initialized - lbl_codec not set")
        return self._lbl_codec

    @property
    def lbl_file_size(self) -> QLabel:
        if self._lbl_file_size is None:
            raise RuntimeError("UI not initialized - lbl_file_size not set")
        return self._lbl_file_size

    @property
    def lbl_source_type(self) -> QLabel:
        if self._lbl_source_type is None:
            raise RuntimeError("UI not initialized - lbl_source_type not set")
        return self._lbl_source_type

    @property
    def progress_bar(self) -> QProgressBar:
        if self._progress_bar is None:
            raise RuntimeError("UI not initialized - progress_bar not set")
        return self._progress_bar

    @property
    def lbl_status(self) -> QLabel:
        if self._lbl_status is None:
            raise RuntimeError("UI not initialized - lbl_status not set")
        return self._lbl_status

    def update_info(self, video_info: VideoInfo) -> None:
        """
        تحديث معلومات الفيديو

        المُعاملات (Args):
            video_info: كائن VideoInfo بالمعلومات
        """
        if video_info is None:
            return
        if not video_info.is_valid:
            self.lbl_source_name.setText(f"X خطأ: {video_info.error_message}")
            self.lbl_source_name.setStyleSheet(StatusBarStyles.info_source_error())
            return

        # تحديث المعلومات
        self.lbl_source_name.setText(f"OK {video_info.file_name}")
        self.lbl_source_name.setStyleSheet(StatusBarStyles.info_source_name())

        self.lbl_source_type.setText(f"النوع: {video_info.source_type}")
        self.lbl_resolution.setText(f"الدقة: {video_info.get_resolution_text()}")
        fps_text = "N/A" if video_info.fps == 0 else f"{video_info.fps:.2f}"
        self.lbl_fps.setText(f"FPS: {fps_text}")
        self.lbl_duration.setText(f"المدة: {video_info.get_duration_text()}")
        frames_text = "غير متاح" if video_info.source_type in ("كاميرا", "بث RTSP", "بث HTTP") else str(video_info.total_frames)
        self.lbl_frames.setText(f"الإطارات: {frames_text}")
        self.lbl_codec.setText(f"الكوديك: {video_info.codec if video_info.codec else 'غير معروف'}")
        self.lbl_file_size.setText(f"الحجم: {video_info.get_file_size_text()}")

    def set_progress(self, value: int, status_text: str = "") -> None:
        """
        تحديث شريط التقدم

        المُعاملات (Args):
            value: القيمة (0-100)
            status_text: نص الحالة
        """
        self.progress_bar.setValue(value)
        if status_text:
            self.lbl_status.setText(status_text)

    def reset(self) -> None:
        """إعادة تعيين العرض."""
        self.lbl_source_name.setText("المصدر: --")
        self.lbl_resolution.setText("الدقة: --")
        self.lbl_fps.setText("FPS: --")
        self.lbl_duration.setText("المدة: --")
        self.lbl_frames.setText("الإطارات: --")
        self.lbl_codec.setText("الكوديك: --")
        self.lbl_file_size.setText("الحجم: --")
        self.lbl_source_type.setText("النوع: --")
        self.progress_bar.setValue(0)
        self.lbl_status.setText("جاهز للتحميل")

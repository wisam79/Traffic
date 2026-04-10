"""
ملف إدارة مصادر الفيديو - Video Source Manager
==================================================
يُدير تحميل وعرض معلومات مصادر الفيديو المختلفة.

المسؤوليات:
- دعم مصادر متعددة (ملف، كاميرا، RTSP، URL)
- استخراج معلومات الفيديو (الدقة، FPS، المدة، الكوديك)
- التحقق من صحة المصدر قبل التحميل
- إنشاء صور مصغرة
- إدارة الملفات الأخيرة

المرتبط به:
- يُستورد من: video_panel.py, main_window.py
- يتصل بـ: video_ingestor.py
"""

import os
import cv2
import logging
from typing import Optional, Dict, List, Tuple
from datetime import timedelta
from pathlib import Path

from PySide6.QtCore import QSettings

logger = logging.getLogger(__name__)


# ==============================================================================
# أنواع مصادر الفيديو
# ==============================================================================

class VideoSourceType:
    """أنواع مصادر الفيديو."""
    FILE = "ملف فيديو"
    CAMERA = "كاميرا"
    RTSP = "بث RTSP"
    HTTP = "بث HTTP"


# ==============================================================================
# معلومات الفيديو
# ==============================================================================

class VideoInfo:
    """
    معلومات الفيديو
    ================
    يُخزن جميع خصائص الفيديو.
    """

    def __init__(self):
        """تهيئة معلومات الفيديو."""
        # المعلومات الأساسية
        self.file_path: str = ""
        self.source_type: str = ""
        self.is_valid: bool = False

        # خصائص الفيديو
        self.width: int = 0
        self.height: int = 0
        self.fps: float = 0.0
        self.total_frames: int = 0
        self.duration_seconds: float = 0.0
        self.codec: str = ""

        # معلومات الملف
        self.file_size_bytes: int = 0
        self.file_extension: str = ""
        self.file_name: str = ""

        # رسالة الخطأ (إذا وجدت)
        self.error_message: str = ""

    def get_resolution_text(self) -> str:
        """الحصول على نص الدقة."""
        return f"{self.width}×{self.height}"

    def get_duration_text(self) -> str:
        """الحصول على نص المدة."""
        if self.duration_seconds <= 0:
            return "بث مباشر"
        
        duration = timedelta(seconds=int(self.duration_seconds))
        return str(duration)

    def get_file_size_text(self) -> str:
        """الحصول على نص حجم الملف."""
        if self.file_size_bytes <= 0:
            return "غير متاح"
        
        size_mb = self.file_size_bytes / (1024 * 1024)
        return f"{size_mb:.2f} MB"

    def get_summary(self) -> str:
        """الحصول على ملخص المعلومات."""
        if not self.is_valid:
            return f"خطأ: {self.error_message}"
        
        return (
            f"الدقة: {self.get_resolution_text()}\n"
            f"معدل الإطارات: {self.fps:.2f} FPS\n"
            f"المدة: {self.get_duration_text()}\n"
            f"إجمالي الإطارات: {self.total_frames}\n"
            f"الكوديك: {self.codec if self.codec else 'غير معروف'}\n"
            f"حجم الملف: {self.get_file_size_text()}"
        )


# ==============================================================================
# مدير مصادر الفيديو
# ==============================================================================

class VideoSourceManager:
    """
    مدير مصادر الفيديو
    ===================
    يُدير تحميل والتحقق من مصادر الفيديو المختلفة.

    المرتبط به:
    - يُنشأ من: main_window.py
    - يتحقق من: مصادر الفيديو
    - يُرجع معلومات إلى: video_panel.py
    """

    def __init__(self, max_recent_files: int = 10):
        self.max_recent_files = max_recent_files
        self._settings = QSettings("SmartTraffic", "TrafficCounter")
        self.recent_files: List[str] = self._settings.value("recent_files", [], type=list)

        self.supported_video_extensions = {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', 
            '.flv', '.webm', '.m4v', '.mpeg', '.mpg'
        }

    @staticmethod
    def discover_cameras(max_check: int = 5) -> list:
        """
        اكتشاف الكاميرات المتاحة
        ==========================
        يتحقق من أول max_check مؤشرات كاميرا.
        """
        import cv2
        cameras = []
        for i in range(max_check):
            cap = cv2.VideoCapture(i)
            try:
                if cap.isOpened():
                    cameras.append(str(i))
            finally:
                cap.release()
        return cameras

    def detect_source_type(self, source) -> str:
        """
        اكتشاف نوع مصدر الفيديو

        المُعاملات (Args):
            source: المصدر (رقم، مسار، رابط)

        المرجع (Returns):
            نوع المصدر (VideoSourceType)
        """
        # كاميرا (رقم)
        if isinstance(source, int):
            return VideoSourceType.CAMERA
        if isinstance(source, float) and source.is_integer():
            return VideoSourceType.CAMERA

        source_str = str(source).strip()

        # كاميرا (نص يمثل رقماً مثل "0" أو "1")
        try:
            int_val = int(source_str)
            return VideoSourceType.CAMERA
        except (ValueError, TypeError):
            pass

        source_str_lower = source_str.lower()

        # RTSP
        if source_str_lower.startswith('rtsp://'):
            return VideoSourceType.RTSP

        # HTTP/HTTPS
        if source_str_lower.startswith(('http://', 'https://')):
            return VideoSourceType.HTTP
        
        # ملف
        if os.path.exists(source_str) or source_str.endswith(tuple(self.supported_video_extensions)):
            return VideoSourceType.FILE
        
        return VideoSourceType.FILE  # افتراضي

    def get_video_info(self, source) -> VideoInfo:
        """
        الحصول على معلومات الفيديو

        المُعاملات (Args):
            source: مصدر الفيديو

        المرجع (Returns):
            كائن VideoInfo بالمعلومات
        """
        video_info = VideoInfo()
        video_info.file_path = str(source)
        video_info.source_type = self.detect_source_type(source)

        try:
            # ==================================================================
            # كاميرا
            # ==================================================================
            if video_info.source_type == VideoSourceType.CAMERA:
                return self._get_camera_info(int(source), video_info)
            
            # ==================================================================
            # بث مباشر (RTSP/HTTP)
            # ==================================================================
            elif video_info.source_type in [VideoSourceType.RTSP, VideoSourceType.HTTP]:
                return self._get_stream_info(source, video_info)
            
            # ==================================================================
            # ملف فيديو
            # ==================================================================
            else:
                return self._get_file_info(source, video_info)

        except Exception as e:
            video_info.is_valid = False
            video_info.error_message = str(e)
            logger.error(f"خطأ في الحصول على معلومات الفيديو: {e}")
            return video_info

    def _get_file_info(self, source: str, video_info: VideoInfo) -> VideoInfo:
        """الحصول على معلومات ملف فيديو."""
        # التحقق من وجود الملف
        if not os.path.exists(source):
            video_info.is_valid = False
            video_info.error_message = "الملف غير موجود"
            return video_info

        # معلومات الملف
        video_info.file_name = Path(source).stem
        video_info.file_extension = Path(source).suffix

        try:
            video_info.file_size_bytes = os.path.getsize(source)
        except OSError:
            video_info.file_size_bytes = 0

        # فتح الفيديو
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            video_info.is_valid = False
            video_info.error_message = "فشل فتح ملف الفيديو"
            return video_info

        try:
            # استخراج المعلومات
            video_info.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            video_info.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            video_info.fps = cap.get(cv2.CAP_PROP_FPS)
            video_info.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            # Check for very small fps values to avoid division issues
            if video_info.fps and video_info.fps > 0.001:
                video_info.duration_seconds = video_info.total_frames / video_info.fps
            else:
                video_info.duration_seconds = 0
            
            # الكوديك (أحياناً غير متاح)
            codec_int = int(cap.get(cv2.CAP_PROP_FOURCC))
            if codec_int > 0:
                try:
                    video_info.codec = "".join([chr((codec_int >> 8 * i) & 0xFF) for i in range(4)])
                except (ValueError, TypeError):
                    video_info.codec = "غير معروف"

            video_info.is_valid = True

            # إضافة للملفات الأخيرة
            self._add_to_recent_files(source)

            return video_info

        finally:
            cap.release()

    def _get_camera_info(self, camera_index: int, video_info: VideoInfo) -> VideoInfo:
        """الحصول على معلومات الكاميرا."""
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            video_info.is_valid = False
            video_info.error_message = f"فشل فتح الكاميرا {camera_index}"
            return video_info

        try:
            video_info.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            video_info.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            video_info.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0  # افتراضي
            video_info.is_valid = True
            video_info.file_name = f"كاميرا {camera_index}"

            return video_info

        finally:
            cap.release()

    def _get_stream_info(self, url: str, video_info: VideoInfo) -> VideoInfo:
        """الحصول على معلومات البث المباشر."""
        video_info.file_name = url
        video_info.fps = 30.0  # افتراضي للبث

        cap = None
        try:
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                video_info.error_message = "فشل فتح البث المباشر"
                return video_info

            video_info.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            video_info.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            video_info.is_valid = True

            return video_info

        except Exception as e:
            video_info.error_message = str(e)
            return video_info

        finally:
            if cap is not None:
                cap.release()

    def validate_source(self, source) -> Tuple[bool, str]:
        """
        التحقق من صحة مصدر الفيديو

        المُعاملات (Args):
            source: المصدر للتحقق

        المرجع (Returns):
            (صحيح/خطأ، رسالة الخطأ)
        """
        video_info = self.get_video_info(source)
        return (video_info.is_valid, video_info.error_message)

    def generate_thumbnail(self, source, timestamp_seconds: float = 0.0) -> Optional[object]:
        """
        إنشاء صورة مصغرة من الفيديو

        المُعاملات (Args):
            source: مصدر الفيديو
            timestamp_seconds: الوقت بالصواني للصورة

        المرجع (Returns):
            إطار (numpy array) أو None
        """
        cap = None
        try:
            cap = cv2.VideoCapture(str(source))
            
            if not cap.isOpened():
                return None

            # الانتقال للوقت المحدد
            if timestamp_seconds > 0:
                cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_seconds * 1000)

            # قراءة إطار
            ret, frame = cap.read()

            if ret:
                # تصغير الحجم
                height, width = frame.shape[:2]
                new_width = 320
                new_height = int(height * (new_width / width))
                frame = cv2.resize(frame, (new_width, new_height))
                
                return frame

            return None

        except Exception as e:
            logger.error(f"خطأ في إنشاء الصورة المصغرة: {e}")
            return None

        finally:
            if cap is not None:
                cap.release()

    # ======================================================================
    # إدارة الملفات الأخيرة
    # ======================================================================

    def _add_to_recent_files(self, file_path: str) -> None:
        file_path = os.path.abspath(file_path)
        
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        self.recent_files.insert(0, file_path)
        
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]

        self._persist_recent_files()

    def get_recent_files(self) -> List[str]:
        """الحصول على قائمة الملفات الأخيرة."""
        # التحقق من وجود الملفات
        valid_files = []
        for file_path in self.recent_files:
            if os.path.exists(file_path):
                valid_files.append(file_path)
        
        return valid_files

    def clear_recent_files(self) -> None:
        self.recent_files.clear()
        self._persist_recent_files()

    def remove_from_recent(self, file_path: str) -> None:
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
            self._persist_recent_files()

    def _persist_recent_files(self) -> None:
        self._settings.setValue("recent_files", self.recent_files)

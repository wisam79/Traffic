"""
ملف التقاط الفيديو - Video Ingestor
====================================
يُدير التقاط الفيديو من مصادر مختلفة (كاميرا، ملف، RTSP)
يستخدم OpenCV (cv2.VideoCapture) للالتقاط مع قراءة في خيط منفصل.

المسؤوليات:
- بدء/إيقاف البث من المصدر
- قراءة الإطارات بشكل مستمر
- دفع الإطارات إلى طابور مشترك مع سياسة تجاه للإطارات القديمة

المرتبط به:
- يُستورد من: app.py (لبدء خيط الالتقاط)
- يُرسل البيانات إلى: raw_frame_queue (طابور مشترك)
- يستقبل من: ai_thread.py (يسحب من نفس الطابور)
"""

import queue
import logging
import threading
import time
from typing import Optional
import cv2

logger = logging.getLogger(__name__)

# امتدادات ملفات الفيديو المدعومة للتحكم بسرعة التشغيل
VIDEO_FILE_EXTENSIONS = (
    ".mp4", ".avi", ".mkv", ".mov", ".wmv",
    ".flv", ".webm", ".m4v", ".mpeg", ".mpg"
)


class VideoIngestor:
    """
    مُدير التقاط الفيديو
    =====================
    يُغلف cv2.VideoCapture ويُوفر واجهة بسيطة للتطبيق.
    يُشغل خيط قراءة داخلي ويدفع الإطارات للطابور.
    """

    def __init__(self, source: str, raw_frame_queue: queue.Queue, max_queue_size: int = 2):
        """
        تهيئة مُدير الفيديو

        المُعاملات (Args):
            source: مصدر الفيديو (0 للكاميرا، مسار لملف)
            raw_frame_queue: الطابور المشترك
            max_queue_size: الحد الأقصى لحجم الطابور
        """
        self.source = source
        self.raw_frame_queue = raw_frame_queue
        self.max_queue_size = max_queue_size

        self.stream: Optional[cv2.VideoCapture] = None
        self._stop_event = threading.Event()
        self._stream_lock = threading.Lock()

    def start(self) -> bool:
        """بدء التقاط الفيديو باستخدام OpenCV"""
        try:
            stream = cv2.VideoCapture(self.source)
            if not stream.isOpened():
                logger.error(f"فشل فتح مصدر الفيديو: {self.source}")
                stream.release()
                return False

            with self._stream_lock:
                self.stream = stream

            self._stop_event.clear()
            logger.info(f"تم بدء بث الفيديو بنجاح (OpenCV): {self.source}")
            return True

        except Exception as e:
            logger.error(f"أثناء بدء البث: {e}")
            self._stop_event.set()
            return False

    def read_loop(self) -> None:
        """حلقة القراءة المستمرة للخيط مع تنظيم السرعة (FPS Pacing) للوصول للاختبار الحقيقي."""
        if not self.stream or self._stop_event.is_set():
            logger.warning("لم يُبدأ البث بعد.")
            return

        # حساب تأخير الإطار للتحكم بسرعة القراءة
        fps = self.stream.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 120:
            fps = 30.0
        frame_delay = 1.0 / fps

        # تحديد ما إذا كان المصدر ملف فيديو يحتاج تنظيم سرعة
        is_video_file = str(self.source).lower().endswith(VIDEO_FILE_EXTENSIONS)

        try:
            while not self._stop_event.is_set():
                loop_start = time.perf_counter()

                with self._stream_lock:
                    if self.stream is None:
                        break
                    ret, frame = self.stream.read()

                if not ret or frame is None:
                    if not ret:
                        source_str = str(self.source)
                        if source_str.startswith(("rtsp://", "http://", "https://")):
                            logger.warning("فقدان الاتصال بالبث — محاولة إعادة الاتصال...")
                            with self._stream_lock:
                                if self.stream:
                                    self.stream.release()
                            for attempt in range(3):
                                if self._stop_event.is_set():
                                    break
                                time.sleep(2)
                                new_stream = cv2.VideoCapture(self.source)
                                if new_stream.isOpened():
                                    with self._stream_lock:
                                        self.stream = new_stream
                                    logger.info(f"تم إعادة الاتصال (محاولة {attempt + 1})")
                                    break
                                else:
                                    new_stream.release()
                            else:
                                logger.error("فشل إعادة الاتصال بعد 3 محاولات")
                                break
                            continue
                    break

                try:
                    self.raw_frame_queue.put_nowait(frame)
                except queue.Full:
                    try:
                        self.raw_frame_queue.get_nowait()
                        self.raw_frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass

                # التحكم بسرعة التشغيل (Pacing) لملفات الفيديو
                if is_video_file:
                    elapsed = time.perf_counter() - loop_start
                    sleep_time = frame_delay - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)

        except Exception as e:
            logger.error(f"خطأ في حلقة القراءة (cv2): {e}")
        finally:
            self.stop()

    def stop(self) -> None:
        """إيقاف التقاط الفيديو"""
        self._stop_event.set()

        with self._stream_lock:
            if self.stream:
                self.stream.release()
                self.stream = None

        # إعطاء خيط القراءة فرصة للتوقف قبل تنظيف الطابور
        time.sleep(0.15)

        while not self.raw_frame_queue.empty():
            try:
                self.raw_frame_queue.get_nowait()
            except queue.Empty:
                break

        logger.info("تم إيقاف فيديو بنجاح.")

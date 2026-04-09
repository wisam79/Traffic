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
from typing import Optional
import cv2

logger = logging.getLogger(__name__)


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
        self.is_running = False
        self._lock = threading.Lock()

    def start(self) -> bool:
        """بدء التقاط الفيديو باستخدام OpenCV"""
        try:
            self.stream = cv2.VideoCapture(self.source)
            if not self.stream.isOpened():
                logger.error(f"فشل فتح مصدر الفيديو: {self.source}")
                return False

            self.is_running = True
            logger.info(f"تم بدء بث الفيديو بنجاح (OpenCV): {self.source}")
            return True

        except Exception as e:
            logger.error(f"أثناء بدء البث: {e}")
            self.is_running = False
            return False

    def read_loop(self) -> None:
        """حلقة القراءة المستمرة للخيط مع تنظيم السرعة (FPS Pacing) للوصول للاختبار الحقيقي."""
        if not self.stream or not self.is_running:
            logger.warning("لم يُبدأ البث بعد.")
            return

        import time
        # حساب تأخير الإطار للتحكم بسرعة القراءة
        fps = self.stream.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 120:
            fps = 30.0
        frame_delay = 1.0 / fps

        try:
            while self.is_running:
                loop_start = time.perf_counter()

                ret, frame = self.stream.read()
                
                if not ret or frame is None:
                    logger.warning("استلام إطار فارغ، قد يكون البث انتهى")
                    self.is_running = False
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
                if str(self.source).endswith((".mp4", ".avi", ".mkv")):
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
        with self._lock:
            if not self.is_running:
                return

            logger.info("جاري إيقاف التقاط الفيديو...")
            self.is_running = False

            if self.stream:
                self.stream.release()
                self.stream = None

            # تفريغ الطابور
            while not self.raw_frame_queue.empty():
                try:
                    self.raw_frame_queue.get_nowait()
                except queue.Empty:
                    break

            logger.info("تم إيقاف فيديو بنجاح.")


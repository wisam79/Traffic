"""
ملف المعالجة المسبقة - Frame Preprocessor
===========================================
يُحول إطارات الفيديو إلى الصيغة المناسبة لنموذج YOLO ONNX.

المسؤوليات:
- تغيير حجم الإطار باستخدام Letterbox (حفاظ على النسبة)
- تحويل الألوان من BGR إلى RGB
- تسوية القيم إلى [0, 1]
- تحويل التنسيق من HWC إلى CHW
- إضافة بُعد الدفعة (batch dimension)
- تخزين معلومات التحجيم لإعادة تحويل الإحداثيات

المرتبط به:
- يُستورد من: ai_thread.py
- يستقبل: إطارات OpenCV (BGR, HWC)
- يُرسل: مصفوفة numpy (RGB, CHW, batch) + معلومات التحجيم
"""

import cv2
import numpy as np
from typing import Tuple, Dict


class FramePreprocessor:
    """
    مُعالج الإطارات المسبق
    ========================
    يُجهز الإطارات للإدخال في نموذج YOLO.
    يستخدم Letterbox لحفاظ على نسبة الأبعاد.
    يُخزن معلومات التحجيم لإعادة تحويل الإحداثيات.
    """

    def __init__(self, target_size: Tuple[int, int] = (640, 640)):
        """
        تهيئة المُعالج

        المُعاملات (Args):
            target_size: الحجم الهدف (العرض، الارتفاع) بالبكسل
        """
        if target_size[0] <= 0 or target_size[1] <= 0:
            raise ValueError(f"Invalid target_size: {target_size}, must be positive")
        self.target_size = target_size

        # معلومات التحجيم الأخيرة (تُحدث مع كل إطار)
        self.last_scale_info: Dict = {}

    def preprocess(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        معالجة الإطار مسبقاً باستخدام Letterbox

        الخطوات:
        1. حساب معاملات التحجيم
        2. تغيير الحجم مع الحفاظ على النسبة (letterbox)
        3. تحويل من BGR إلى RGB
        4. تسوية القيم من [0-255] إلى [0-1]
        5. تحويل التنسيق من HWC إلى CHW
        6. إضافة بُعد الدفعة

        المُعاملات (Args):
            frame: إطار OpenCV بتنسيق BGR، شكل (H, W, 3)

        المرجع (Returns):
            Tuple من:
            - مصفوفة numpy جاهزة للنموذج، شكل (1, 3, H, W)
            - قاموس معلومات التحجيم {"scale", "pad_x", "pad_y", "orig_w", "orig_h"}
        """
        # التحقق من صحة الإدخال
        if frame is None:
            raise ValueError("Input frame is None")
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError(f"Expected 3-channel image, got shape {frame.shape}")
        if frame.shape[0] == 0 or frame.shape[1] == 0:
            raise ValueError("Input frame has invalid dimensions")

        orig_h, orig_w = frame.shape[:2]
        target_w, target_h = self.target_size

        # ======================================================================
        # الخطوة 1: حساب معاملات Letterbox
        # ======================================================================
        # نسبة التحجيم — أصغر نسبة لم تتجاوز الحجم الهدف
        scale = min(target_w / orig_w, target_h / orig_h)

        # الحجم الجديد بعد التحجيم
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        # الحشو المطلوب لملء الحجم الهدف
        pad_x = (target_w - new_w) // 2
        pad_y = (target_h - new_h) // 2

        # تخزين معلومات التحجيم
        scale_info = {
            "scale": scale,
            "pad_x": pad_x,
            "pad_y": pad_y,
            "orig_w": orig_w,
            "orig_h": orig_h
        }
        self.last_scale_info = scale_info

        # ======================================================================
        # الخطوة 2: تطبيق Letterbox
        # ======================================================================
        # تغيير الحجم مع الحفاظ على النسبة
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # إنشاء صورة بالحجم الهدف مملوءة باللون الرمادي (114)
        letterboxed = np.full(
            (target_h, target_w, 3),
            114,  # رمادي — القيمة المعتمدة في YOLO
            dtype=np.uint8
        )

        # وضع الصورة المُحجمة في المنتصف
        letterboxed[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized

        # ======================================================================
        # الخطوة 3: تحويل الألوان من BGR إلى RGB
        # ======================================================================
        rgb = cv2.cvtColor(letterboxed, cv2.COLOR_BGR2RGB)

        # ======================================================================
        # الخطوة 4: تسوية القيم
        # ======================================================================
        normalized = rgb.astype(np.float32) / 255.0

        # ======================================================================
        # الخطوة 5: تحويل التنسيق من HWC إلى CHW
        # ======================================================================
        transposed = np.transpose(normalized, (2, 0, 1))

        # ======================================================================
        # الخطوة 6: إضافة بُعد الدفعة
        # ======================================================================
        batch = np.expand_dims(transposed, axis=0)

        return batch, scale_info

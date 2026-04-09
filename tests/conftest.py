"""
ملف التهيئة المشتركة للاختبارات - Shared Fixtures
====================================================
يحتوي على fixtures مشتركة بين جميع ملفات الاختبار.

يُحمل تلقائياً بواسطة pytest.
"""

import sys
import os
import queue

import numpy as np
import pytest
import supervision as sv

# إضافة جذر المشروع إلى مسار Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==============================================================================
# Fixtures — إطارات اختبار
# ==============================================================================

@pytest.fixture
def sample_frame_640():
    """إطار اختبار بحجم 640×640 (BGR)"""
    return np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame_1080p():
    """إطار اختبار بحجم 1920×1080 (BGR)"""
    return np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame_720p():
    """إطار اختبار بحجم 1280×720 (BGR)"""
    return np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame_vertical():
    """إطار عمودي 1080×1920 (BGR)"""
    return np.random.randint(0, 255, (1920, 1080, 3), dtype=np.uint8)


@pytest.fixture
def black_frame():
    """إطار أسود 640×480 (BGR)"""
    return np.zeros((480, 640, 3), dtype=np.uint8)


# ==============================================================================
# Fixtures — كشوفات اختبار
# ==============================================================================

@pytest.fixture
def empty_detections():
    """كشوفات فارغة"""
    return sv.Detections.empty()


@pytest.fixture
def sample_detections():
    """كشوفات اختبار — 3 مركبات"""
    return sv.Detections(
        xyxy=np.array([
            [100, 200, 300, 400],  # سيارة
            [500, 100, 700, 350],  # شاحنة
            [200, 300, 350, 500],  # دراجة
        ], dtype=np.float32),
        confidence=np.array([0.9, 0.85, 0.7], dtype=np.float32),
        class_id=np.array([2, 7, 3], dtype=int)  # car, truck, motorcycle
    )


@pytest.fixture
def non_vehicle_detections():
    """كشوفات لغير المركبات (person=0, dog=16)"""
    return sv.Detections(
        xyxy=np.array([
            [100, 200, 200, 400],
            [300, 100, 400, 300],
        ], dtype=np.float32),
        confidence=np.array([0.95, 0.8], dtype=np.float32),
        class_id=np.array([0, 16], dtype=int)
    )


# ==============================================================================
# Fixtures — YOLO26 مخرجات مُحاكاة
# ==============================================================================

@pytest.fixture
def yolo26_raw_output():
    """مخرجات YOLO26 مُحاكاة: (1, 300, 6)"""
    output = np.zeros((1, 300, 6), dtype=np.float32)
    # 3 كشوفات حقيقية
    output[0, 0] = [320, 240, 100, 80, 0.92, 2]   # سيارة - وسط
    output[0, 1] = [100, 100, 60, 50, 0.85, 7]     # شاحنة - أعلى يسار
    output[0, 2] = [500, 400, 40, 30, 0.3, 3]      # دراجة - ثقة ضعيفة
    # البقية أصفار (ثقة 0.0 = تُهمل)
    return output


@pytest.fixture
def yolo26_empty_output():
    """مخرجات YOLO26 بدون كشوفات"""
    return np.zeros((1, 300, 6), dtype=np.float32)


# ==============================================================================
# Fixtures — معلومات التحجيم
# ==============================================================================

@pytest.fixture
def scale_info_1080p():
    """معلومات تحجيم لإطار 1920×1080"""
    # 1920/640 = 3.0, 1080/640 = 1.6875
    # scale = min(640/1920, 640/1080) = min(0.333, 0.593) = 0.333
    scale = 640 / 1920  # 0.3333
    new_w = int(1920 * scale)  # 640
    new_h = int(1080 * scale)  # 360
    pad_x = (640 - new_w) // 2  # 0
    pad_y = (640 - new_h) // 2  # 140
    return {
        "scale": scale,
        "pad_x": pad_x,
        "pad_y": pad_y,
        "orig_w": 1920,
        "orig_h": 1080
    }


@pytest.fixture
def scale_info_identity():
    """معلومات تحجيم بدون تغيير (640×640)"""
    return {
        "scale": 1.0,
        "pad_x": 0,
        "pad_y": 0,
        "orig_w": 640,
        "orig_h": 640
    }


# ==============================================================================
# Fixtures — طابور اختبار
# ==============================================================================

@pytest.fixture
def frame_queue():
    """طابور إطارات للاختبار"""
    return queue.Queue(maxsize=2)

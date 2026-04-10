# Smart Intersection Vehicle Counting System
# نظام عد المركبات الذكي - تقاطعات المرور

Real-time vehicle detection, tracking, and counting at intersections using YOLO26n + ByteTrack + PySide6.

تطبيق سطح مكتب احترافي لكشف وتتبع وعد المركبات في الزمن الحقيقي.

---

## Features | المميزات

- **Real-time Detection**: YOLO26n ONNX model with CUDA/CPU auto-fallback
- **Multi-line Counting**: Draw multiple counting lines with individual in/out stats
- **Vehicle Classification**: Cars, motorcycles, buses, trucks (COCO classes)
- **Video Sources**: Camera, video file, RTSP stream, HTTP stream
- **Recording**: Video recording and screenshot capture
- **Image Adjustments**: Brightness, contrast, saturation controls
- **Dark/Light Theme**: Switchable theme with persistent preference
- **Session Management**: Save/load sessions with line positions and stats
- **Data Export**: CSV and JSON export of counting statistics
- **Keyboard Shortcuts**: Space, Ctrl+O, Ctrl+S, F11, Escape

---

## Project Structure | هيكل المشروع

```
traffic/
├── main.py                          # Entry point | نقطة الدخول
├── requirements.txt                 # Dependencies | المكتبات
├── README.md
│
├── core/                            # Core settings | الإعدادات الأساسية
│   ├── config.py                    # Constants and configuration
│   └── app.py                       # Application setup with splash screen
│
├── engine/                          # AI Engine | محرك الذكاء الاصطناعي
│   ├── ai_thread.py                 # Main processing thread (QThread)
│   ├── preprocessor.py              # Frame preprocessing (letterbox)
│   ├── detector.py                  # Object detection (YOLO26 ONNX)
│   └── tracker.py                   # Tracking (ByteTrack) + LineZone counting
│
├── ui/                              # User Interface | واجهة المستخدم
│   ├── main_window.py               # Main window (signal wiring)
│   ├── video_panel.py               # Video display panel
│   ├── video_player.py              # Zoomable graphics view + display manager
│   ├── video_toolbar.py             # Right sidebar (image adjust, recording)
│   ├── video_controllers.py         # Image adjustment + media recorder
│   ├── video_source_manager.py      # Video source validation + info
│   ├── video_info_display.py        # Video info card with progress
│   ├── drawing_modes.py             # Line drawing tools (single/multi)
│   ├── line_manager.py              # Line management widget
│   ├── control_panel.py             # Left panel (source, stats, controls)
│   ├── styles.py                    # CSS style constants
│   └── themes.py                    # Theme system (dark/light) + design tokens
│
├── video/
│   └── ingestor.py                  # Video capture with FPS pacing + RTSP reconnect
│
├── state/
│   └── app_state.py                 # Thread-safe shared state
│
├── models/
│   └── yolo26n.onnx                 # YOLO26 detection model
│
├── docs/
│   ├── architecture.md              # System architecture
│   ├── configuration.md             # Configuration guide
│   ├── development.md               # Development guide
│   ├── line_drawing_guide.md         # Line drawing user guide
│   └── improvement_plan.md           # Improvement plan
│
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── test_detector.py
│   ├── test_preprocessor.py
│   ├── test_tracker.py
│   ├── test_drawing_modes.py
│   ├── test_video_controllers.py
│   ├── test_pipeline_integration.py
│   └── test_user_journey.py
│
└── recordings/                      # Saved recordings and screenshots
```

---

## Installation | التثبيت

```bash
# Clone the repository
git clone https://github.com/wisam79/Traffic.git
cd Traffic

# Install dependencies
pip install -r requirements.txt

# For GPU acceleration (optional)
pip install onnxruntime-gpu
```

### Requirements

| Package | Purpose |
|---------|---------|
| PySide6 | GUI framework |
| onnxruntime | ONNX model inference |
| opencv-python | Video capture & image processing |
| numpy | Array operations |
| supervision | Detection/tracking/annotation utilities |

---

## Usage | الاستخدام

```bash
python main.py
```

### Steps | الخطوات

1. **Select Video Source**: Enter camera number (e.g., `0`) or browse for a video file
2. **Load Video**: Click the load button to preview the first frame
3. **Start Analysis**: Click start or press `Space`
4. **Draw Counting Line**: Click two points on the video to create a counting line
5. **View Results**: Real-time vehicle counts update in the control panel
6. **Record/Screenshot**: Use the right toolbar for image adjustments and recording

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Space` | Start/Stop analysis |
| `Ctrl+O` | Open video file |
| `Ctrl+S` | Take screenshot |
| `F11` | Toggle fullscreen |
| `Escape` | Exit fullscreen |

---

## Architecture | البنية التقنية

### Data Flow | تدفق البيانات

```
Video Source (Camera/File/RTSP)
    ↓
VideoIngestor (Thread 2: frame capture + FPS pacing)
    ↓ raw_frame_queue (maxsize=2, drop oldest when full)
AIEngineThread (Thread 3: preprocess → detect → track → count → annotate)
    ↓ Qt Signals (frame_ready, stats_ready)
MainWindow (Thread 1: UI update)
    ↓
VideoPanel + ControlPanel + VideoToolbar
```

### Thread Communication | التواصل بين الخيوط

| From → To | Mechanism |
|-----------|-----------|
| VideoIngestor → AIEngine | `queue.Queue` (lock-free, bounded) |
| AIEngine → UI | PySide6 `Signal/Slot` (thread-safe) |
| UI → AIEngine | `Slot` methods (thread-safe) |

For full architecture details, see [docs/architecture.md](docs/architecture.md).

---

## Configuration | التخصيص

All settings are in `core/config.py`. For detailed configuration, see [docs/configuration.md](docs/configuration.md).

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `CONFIDENCE_THRESHOLD` | 0.5 | Minimum detection confidence |
| `IOU_THRESHOLD` | 0.45 | NMS IoU threshold |
| `MODEL_INPUT_SIZE` | (640, 640) | Model input resolution |
| `MAX_QUEUE_SIZE` | 2 | Frame queue size |
| `TRACKER_FRAME_RATE` | 30 | ByteTrack FPS setting |

### Adding Vehicle Classes

Edit `core/config.py`:
```python
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    # Add new classes here using COCO class IDs
}
```

---

## Performance | الأداء

| Mode | Typical FPS | Notes |
|------|-------------|-------|
| GPU (CUDA) | 25-35+ | Requires `onnxruntime-gpu` |
| CPU | 10-20 | Default, works on any machine |

### Performance Tips

- Use `onnxruntime-gpu` for CUDA acceleration
- Lower video resolution reduces processing time
- Increase `CONFIDENCE_THRESHOLD` to reduce false positives
- Stats emission is throttled to every 5th frame to reduce UI overhead

---

## Troubleshooting | حل المشاكل

| Problem | Solution |
|---------|----------|
| "Model not found" | Ensure `models/yolo26n.onnx` exists |
| "Failed to start video" | Check video source path or camera index |
| Slow performance | Install `onnxruntime-gpu`, lower resolution, increase confidence threshold |
| RTSP disconnects | Auto-reconnects up to 3 times (2s delay between attempts) |

---

## Testing | الاختبارات

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test module
python -m pytest tests/test_detector.py -v
```

114 tests covering: detector, preprocessor, tracker, drawing modes, video controllers, pipeline integration, and user journey.

For development setup, see [docs/development.md](docs/development.md).

---

## License

This project is licensed under the MIT License.

---

**Version**: 2.1  
**Date**: 2026  
**Technologies**: PySide6, ONNX Runtime, OpenCV, Supervision, ByteTrack

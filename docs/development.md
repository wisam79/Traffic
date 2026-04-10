# Development Guide | دليل التطوير

## Setup | إعداد بيئة التطوير

```bash
# Clone the repository
git clone https://github.com/wisam79/Traffic.git
cd Traffic

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies (optional)
pip install pytest pytest-qt pytest-benchmark pytest-cov
```

---

## Running Tests | تشغيل الاختبارات

```bash
# All tests
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_detector.py -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=html

# Benchmarks
python -m pytest tests/ --benchmark-only
```

### Test Structure

| File | What it tests |
|------|--------------|
| `test_detector.py` | ONNX model loading, YOLO26/v8/v5 parsing, coordinate rescaling |
| `test_preprocessor.py` | Letterbox, normalization, scale info, edge cases |
| `test_tracker.py` | ByteTrack, vehicle filtering, LineZone counting, reset |
| `test_drawing_modes.py` | LineData, drawing modes, coordinate validation |
| `test_video_controllers.py` | ImageAdjuster, MediaRecorder, VideoController |
| `test_pipeline_integration.py` | Full pipeline: preprocess → detect → track → count |
| `test_user_journey.py` | End-to-end user journey test |

### Shared Fixtures (conftest.py)

- `sample_frame_640` / `sample_frame_1080p` / `sample_frame_720p`: Test frames
- `empty_detections` / `sample_detections`: Supervision detections
- `yolo26_raw_output` / `yolo26_empty_output`: Simulated YOLO26 model output
- `scale_info_1080p` / `scale_info_identity`: Preprocessing scale info
- `frame_queue`: Thread-safe frame queue

---

## Code Style | أسلوب الكود

### General Principles

- **Separation of concerns**: Each module has one responsibility
- **Thread safety**: Use `threading.Lock` or Qt `Signal/Slot` for cross-thread communication
- **Theme consistency**: All styles go through `themes.py` — no hardcoded CSS values
- **Bilingual docstrings**: Arabic primary with English translation
- **No external comments in code**: Code should be self-documenting

### Module Structure

Each Python file follows this structure:
```python
"""Module docstring (bilingual)"""

# Imports (standard library, third-party, local)

# Constants

# Classes

# Functions
```

### Adding a New UI Component

1. Create the widget file in `ui/`
2. Import from `ui.themes` for all styles
3. Import from `ui.styles` for style constants
4. Add styles to `themes.py` if needed (use static methods)
5. Wire signals in `main_window.py`
6. Add tests in `tests/`

### Adding a New Engine Component

1. Create the module in `engine/`
2. Integrate into `ai_thread.py` processing pipeline
3. Use thread-safe communication (Signal/Slot or queue)
4. Add unit tests with mock data from `conftest.py`
5. Add integration test in `test_pipeline_integration.py`

---

## Architecture Rules | قواعد البنية

### Thread Communication
- **Never** call UI methods from background threads
- **Always** use Qt `Signal/Slot` for cross-thread UI updates
- **Use** `queue.Queue` for producer/consumer patterns

### Style Rules
- **Never** hardcode CSS color values in UI code
- **Always** use `ThemeColors` / `LightThemeColors` from `themes.py`
- **Always** use style generator methods from `ButtonStyles`, `CardStyles`, etc.

### State Rules
- **Use** `AppState` for shared mutable state between threads
- **Never** access `AppState` internal variables directly
- **Always** use the getter/setter methods (they handle locking)

---

## Performance Optimization | تحسين الأداء

### Frame Display Pipeline
- Uses `cv2.cvtColor(dst=reused_buffer)` to avoid allocations
- Reuses `QImage` buffer when frame dimensions don't change
- Uses `QGraphicsPixmapItem.setPixmap()` instead of remove/add cycle
- Stores last BGR frame for recording/screenshots (avoids pixmap→BGR roundtrip)

### AI Engine Pipeline
- `frame.copy()` removed — annotation draws directly on the frame
- Stats emission throttled to every 5th frame
- `ImageAdjuster` skips processing when no adjustments active

### Frame Queue
- `maxsize=2` with drop-oldest policy ensures low latency
- `VideoIngestor` does FPS pacing for video files to avoid excessive CPU usage

---

## Debugging | التصحيح

### Enable Debug Logging
```python
# In core/config.py
LOG_LEVEL = "DEBUG"
```

### Common Issues
- **Model not loading**: Check `MODEL_PATH` in config.py, ensure ONNX file exists
- **Low FPS**: Check if CUDA is available (`onnxruntime` uses CPU by default)
- **UI freeze**: Ensure AI processing is not running on the UI thread
- **Memory leak**: Check that old `QGraphicsPixmapItem` instances are being reused

# Configuration Guide | دليل الإعدادات

All configurable settings are in `core/config.py`. Modify this file to customize the application.

جميع الإعدادات القابلة للتعديل موجودة في `core/config.py`.

---

## Model Settings | إعدادات النموذج

### MODEL_PATH
- **Default**: `models/yolo26n.onnx`
- **Description**: Path to the ONNX model file
- **Change if**: You want to use a different YOLO model

### MODEL_INPUT_SIZE
- **Default**: `(640, 640)`
- **Description**: Input resolution for the model (width, height)
- **Options**: `(320, 320)` (faster), `(640, 640)` (balanced), `(1280, 1280)` (more accurate)
- **Note**: Must match the model's training input size

### CONFIDENCE_THRESHOLD
- **Default**: `0.5` (50%)
- **Range**: 0.0 - 1.0
- **Effect**:
  - Lower → More detections, more false positives
  - Higher → Fewer detections, fewer false positives
- **Recommended**:
  - `0.3` for surveillance (catch everything)
  - `0.5` for general use (balanced)
  - `0.7` for precision (few false positives)

### IOU_THRESHOLD
- **Default**: `0.45` (45%)
- **Range**: 0.0 - 1.0
- **Description**: Maximum overlap between bounding boxes (NMS)
- **Effect**:
  - Lower → Fewer overlapping boxes
  - Higher → Allow more overlapping boxes

---

## Vehicle Classes | فئات المركبات

### VEHICLE_CLASSES
```python
VEHICLE_CLASSES = {
    2: "car",          # COCO class ID → name
    3: "motorcycle",
    5: "bus",
    7: "truck"
}
```

### Adding a New Vehicle Class
Use the COCO dataset class IDs:

| ID | Class | Arabic |
|----|-------|--------|
| 0  | person | شخص |
| 1  | bicycle | دراجة |
| 2  | car | سيارة |
| 3  | motorcycle | دراجة نارية |
| 5  | bus | حافلة |
| 7  | truck | شاحنة |

Example — add bicycle counting:
```python
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    1: "bicycle"   # NEW
}

VEHICLE_CLASS_NAMES_AR = {
    "car": "سيارة",
    "motorcycle": "دراجة نارية",
    "bus": "حافلة",
    "truck": "شاحنة",
    "bicycle": "دراجة"   # NEW
}
```

You also need to update `control_panel.py` to display the new class in the stats section.

---

## Video Settings | إعدادات الفيديو

### MAX_QUEUE_SIZE
- **Default**: `2`
- **Description**: Maximum frames in the queue between ingestor and AI engine
- **Effect**:
  - `1`: Minimum latency, may drop more frames
  - `2`: Balanced (default)
  - `5+`: Smoother but higher latency

### TRACKER_FRAME_RATE
- **Default**: `30`
- **Description**: FPS setting for ByteTrack
- **Effect**: Affects tracking quality at different video speeds

---

## UI Settings | إعدادات الواجهة

### APP_FONT_NAME
- **Default**: `"Segoe UI"`
- **Alternatives**: `"Arial"`, `"Tahoma"`, `"Courier New"`

### APP_FONT_SIZE
- **Default**: `10`

### MAIN_WINDOW_WIDTH / MAIN_WINDOW_HEIGHT
- **Default**: `1400` × `900`
- **Note**: Window size is persisted in QSettings and restored on restart

---

## Line Zone Settings | إعدادات خط العد

### LINE_WIDTH
- **Default**: `4`
- **Description**: Width of the counting line overlay

### POINT_MARKER_SIZE / POINT_INNER_SIZE
- **Default**: `16` / `6`
- **Description**: Size of the line endpoint markers

---

## Logging Settings | إعدادات السجل

### LOG_LEVEL
- **Default**: `"INFO"`
- **Options**: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`
- **Tip**: Use `"DEBUG"` when troubleshooting detection issues

### LOG_FORMAT
- **Default**: `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`

---

## Theme Settings | إعدادات الثيم

Themes are managed in `ui/themes.py` and persisted via `QSettings`:

| Setting | Storage | Key |
|---------|---------|-----|
| Current theme | QSettings | `theme` ("dark" or "light") |
| Window size | QSettings | `window/width`, `window/height` |
| Last video source | QSettings | `last_source` |
| Recent files | QSettings | `recent_files` |

To switch themes programmatically:
```python
from ui.themes import ThemeManager
ThemeManager.toggle()  # Switch between dark and light
```

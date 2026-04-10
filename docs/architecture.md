# System Architecture | معمى النظام

## Overview | نظرة عامة

The Smart Intersection Vehicle Counting System follows a **3-thread architecture** with clear separation of concerns:

1. **UI Thread** (Main): PySide6 event loop, rendering, user interaction
2. **Ingestor Thread** (Background): Video frame capture with FPS pacing
3. **AI Engine Thread** (Background): Object detection, tracking, and counting

---

## Component Diagram | مخطط المكونات

```
┌──────────────────────────────────────────────────────────────┐
│                        MainWindow                             │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐             │
│  │ControlPanel│  │ VideoPanel   │  │VideoToolbar│             │
│  │  (Left)   │  │  (Center)    │  │  (Right)   │             │
│  │           │  │              │  │            │             │
│  │ • Source  │  │ • GraphicsView│  │ • Brightness│            │
│  │ • Stats   │  │ • LineDrawer │  │ • Contrast  │             │
│  │ • Buttons │  │ • StatusBar  │  │ • Saturation│             │
│  │ • Recent  │  │ • InfoDisplay│  │ • Screenshot│             │
│  │           │  │              │  │ • Recording │             │
│  └──────────┘  └──────────────┘  └────────────┘             │
└──────────────────────────────────────────────────────────────┘
         ↑ Signal              ↑ Signal            ↑ Direct
         │                     │                    │
┌────────┴─────────────────────┴────────────────────┴──────────┐
│                     AIEngineThread (QThread)                   │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────────────┐    │
│  │ Preprocessor  │→│ Detector │→│ Tracker + LineZone    │    │
│  │ (Letterbox)  │  │ (YOLO26) │  │ (ByteTrack + Count)  │    │
│  └──────────────┘  └──────────┘  └──────────────────────┘    │
└───────────────────────────┬──────────────────────────────────┘
                            ↑ queue.Queue (maxsize=2)
┌───────────────────────────┴──────────────────────────────────┐
│                     VideoIngestor (Thread)                     │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │ OpenCV Cap   │→│ FPS Pacing   │→ raw_frame_queue          │
│  │ (Camera/File │  │ + Frame Drop │                           │
│  │  /RTSP)      │  │ + Reconnect  │                           │
│  └──────────────┘  └──────────────┘                           │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow | تدفق البيانات

### Frame Processing Pipeline

```
1. VideoIngestor captures frame from OpenCV
2. Frame pushed to raw_frame_queue (drop oldest if full)
3. AIEngineThread pulls frame from queue
4. Preprocessor: BGR → Letterbox(640×640) → RGB → Normalize → CHW → Batch
5. Detector: ONNX inference → Parse YOLO26/v8/v5 output → Filter by confidence
6. Tracker: ByteTrack update → Assign tracker IDs
7. Vehicle Filter: Keep only vehicle classes (car, motorcycle, bus, truck)
8. LineZone: Count crossings (in/out per line, per class)
9. Annotator: Draw bounding boxes, labels, counting lines
10. Emit frame_ready signal (annotated BGR frame)
11. Emit stats_ready signal (throttled every 5 frames)
12. MainWindow receives frame → ImageAdjuster → VideoDisplayManager → Screen
```

### Frame Display Pipeline (Optimized)

```
BGR Frame (from AI Engine)
    ↓
ImageAdjuster (skip if no adjustments active)
    ↓
VideoDisplayManager.update_frame()
    ↓
cv2.cvtColor(BGR→RGB, dst=reused_buffer)  ← No allocation
    ↓
QImage(reused_rgb_buffer)                  ← No copy
    ↓
QPixmap.fromImage() → setPixmap()          ← Reuse pixmap_item
    ↓
Screen
```

---

## Thread Safety | أمان الخيوط

### Communication Mechanisms

| From → To | Mechanism | Thread-Safe? |
|-----------|-----------|-------------|
| Ingestor → AIEngine | `queue.Queue` | Yes (built-in) |
| AIEngine → UI | Qt `Signal/Slot` | Yes (auto-queued) |
| UI → AIEngine | `Slot` methods | Yes (queued connection) |
| Shared State | `threading.Lock` | Yes (explicit locks) |

### AppState Locking

`AppState` uses `threading.Lock` for all read/write operations:

```python
class AppState:
    def __init__(self):
        self._lock = threading.Lock()
        self._stats: Dict[str, int] = {}

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return self._stats.copy()  # Return copy, not reference
```

---

## Signal/Slot Wiring | توصيل الإشارات

### AI Engine Signals

| Signal | Emitted By | Connected To | Data |
|--------|-----------|-------------|------|
| `frame_ready` | AIEngineThread | MainWindow._on_frame_ready | numpy BGR array |
| `stats_ready` | AIEngineThread | MainWindow._on_stats_ready | dict (counts) |
| `error_occurred` | AIEngineThread | MainWindow._on_error | str (message) |

### UI Signals

| Signal | From | Connected To |
|--------|------|-------------|
| `btn_start_stop.clicked` | ControlPanel | MainWindow._on_start_stop |
| `btn_load_video.clicked` | ControlPanel | MainWindow._on_load_video |
| `btn_clear_line.clicked` | ControlPanel | MainWindow._on_clear_line |
| `btn_reset_counts.clicked` | ControlPanel | MainWindow._on_reset_counts |
| `brightness_changed` | VideoToolbar | VideoPanel.on_brightness_change |
| `contrast_changed` | VideoToolbar | VideoPanel.on_contrast_change |
| `saturation_changed` | VideoToolbar | VideoPanel.on_saturation_change |
| `screenshot_requested` | VideoToolbar | MainWindow._on_toolbar_screenshot |
| `record_requested` | VideoToolbar | MainWindow._on_toolbar_record |

---

## Theme System | نظام الثيمات

The theme system uses a centralized design token approach:

```
themes.py
├── ThemeColors (Dark)      → Color tokens
├── LightThemeColors (Light) → Light color tokens
├── Typography               → Font sizes, families
├── Spacing                  → Spacing scale
├── ButtonStyles             → Button CSS generators
├── CardStyles               → Card/frame CSS generators
├── InputStyles              → Input widget CSS generators
├── ListStyles               → List widget CSS generators
├── LabelStyles              → Label text style generators
├── StatCardStyles           → Stat card CSS generators
├── MiscStyles               → Separator, tool buttons, etc.
├── StatusBarStyles          → Status bar style generators
└── ThemeManager             → Theme switching + QSettings persistence
```

All style generation uses f-strings with theme color constants — no hardcoded CSS values anywhere in the UI code.

---

## Persistence | التخزين المؤقت

Using `QSettings("SmartTraffic", "TrafficCounter")`:

| Key | Type | Description |
|-----|------|-------------|
| `window/width` | int | Last window width |
| `window/height` | int | Last window height |
| `last_source` | str | Last video source |
| `theme` | str | "dark" or "light" |
| `recent_files` | list | Recent video file paths |

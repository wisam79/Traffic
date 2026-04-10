# Changelog | سجل التغييرات

## [2.1.0] - 2026-04-10

### Added
- Light theme support with `ThemeManager` class and `LightThemeColors`
- Theme persistence via `QSettings` (dark/light preference saved across sessions)
- Splash screen with "Loading AI Model..." message during startup
- Toast notifications for screenshot and recording actions
- `StatusBarStyles` and `MiscStyles` helper methods for consistent UI styling
- `last_bgr_frame` property on `VideoDisplayManager` for direct frame access
- Architecture documentation (`docs/architecture.md`)
- Configuration guide (`docs/configuration.md`)
- Development guide (`docs/development.md`)
- Recent files persistence via `QSettings`

### Changed
- **Performance**: Eliminated redundant BGR→RGB copy in frame display pipeline
- **Performance**: Reuse RGB buffer and QImage when frame dimensions don't change
- **Performance**: Removed `frame.copy()` in AI annotation — draws directly on frame
- **Performance**: ImageAdjuster skips processing entirely when no adjustments active
- **Performance**: Stats emission throttled to every 5th frame (was every frame)
- **Performance**: Recording pipeline uses stored BGR frame instead of pixmap→BGR roundtrip
- **UI**: All hardcoded inline CSS styles moved to `themes.py` theme system
- **UI**: Removed unused `COLORS` dict from `config.py` (superseded by `themes.py`)
- **UI**: Consistent styling for line manager buttons (delete, clear all)
- **UI**: Consistent styling for video info display (source name, separator, status)

### Fixed
- Inline styles bypassing the theme system in `main_window.py`, `line_manager.py`, `video_info_display.py`, `video_panel.py`, `control_panel.py`
- `COLORS` dict in `config.py` was unused and conflicted with `themes.py`
- Recording pipeline did expensive pixmap→QImage→numpy→BGR conversion (now uses direct BGR frame)

---

## [2.0.0] - 2026-04-09

### Added
- Multi-line zone support with `LineZoneManager`
- Per-line in/out counts and per-vehicle-class breakdown
- `VideoToolbar` sidebar widget for image adjustments and recording
- Video source info display with progress bar
- Session save/load functionality
- Data export (CSV/JSON)
- Keyboard shortcuts (Space, Ctrl+O, Ctrl+S, F11)
- Drag-and-drop for video files
- RTSP reconnection with 3 retry attempts
- FPS pacing for video file playback
- Undo/redo for line drawing
- Line manager widget for line selection and deletion

### Changed
- Major refactoring from single-file architecture to modular structure
- Separated UI, engine, video, and state into distinct packages
- Professional theme system with design tokens
- Thread-safe shared state management

---

## [1.0.0] - 2026-03-01

### Added
- Initial release
- Basic vehicle detection using YOLO ONNX model
- Single counting line with in/out counts
- PySide6 dark theme interface
- Camera and video file support

# Host Bridge Implementation Guide

## Overview

The GW2 Farming Bot uses a **host bridge** abstraction to capture game frames and issue input commands. This document outlines the requirements and implementation path for connecting the bot to a real GW2 game client.

## Current State

### What's Already Implemented

- **Bridge Interface Definitions**: [src/adapters/bridge_interfaces.py](../../src/adapters/bridge_interfaces.py)
  - `CaptureBridge` — defines frame capture contract
  - `InputBridge` — defines input automation contract
  - Abstract methods for real implementations

- **Orchestration & Control**: All bot orchestration, API endpoints, telemetry, and control flow are fully functional with synthetic/mocked data

- **Service Layer**: Orchestrators and services are wired to accept bridge implementations via dependency injection

### What's Missing

- **Real Frame Capture**: Capturing actual GW2 window content as NumPy arrays
- **Real Input Automation**: Issuing mouse/keyboard commands to the running GW2 client
- **Host Bridge Initialization**: Wiring real implementations at startup

---

## Bridge Interface Contracts

### CaptureBridge

Located: [src/adapters/bridge_interfaces.py](../../src/adapters/bridge_interfaces.py)

```python
class CaptureBridge(ABC):
    """Capture frames from game client window."""
    
    @abstractmethod
    def capture(self) -> FrameCapture:
        """Return a single frame from the game client.
        
        Returns:
            FrameCapture with:
              - frame: np.ndarray shape (H, W, 3) BGR format
              - timestamp_utc: ISO format UTC string
              - raw_metadata: optional platform-specific data
        """
        pass
```

**Implementation Requirements**:
1. Locate GW2 game window (by title or PID)
2. Capture current frame buffer (no decorators, game surface only)
3. Convert to NumPy BGR array
4. Return with UTC timestamp

**Platform-Specific Approaches**:

| Platform | Method | Library |
|----------|--------|---------|
| **macOS** | CoreGraphics/Metal | `PIL.ImageGrab` or native APIs |
| **Linux** | X11 / Wayland screenshot | `mss`, `pyautogui.screenshot()` |
| **Windows** | Windows GDI / DXGI | `PIL.ImageGrab`, `mss`, or DirectX capture |

---

### InputBridge

Located: [src/adapters/bridge_interfaces.py](../../src/adapters/bridge_interfaces.py)

```python
class InputBridge(ABC):
    """Issue input commands to game client."""
    
    @abstractmethod
    def emit_action(self, action: InputAction) -> bool:
        """Execute a single input action.
        
        Args:
            action: Contains action_type (MOVE_MOUSE, CLICK, TYPE) and parameters
        
        Returns:
            True if action succeeded, False if failed
        """
        pass
```

**Implementation Requirements**:
1. Accept `InputAction` objects (move, click, hold, release, type)
2. Translate to platform input events
3. Route to GW2 window (must handle window focus, coordinate transforms)
4. Respect timing constraints (avoid too-fast sequences)

**Platform-Specific Approaches**:

| Platform | Method | Library |
|----------|--------|---------|
| **macOS** | Quartz events / CGEventPost | `pynput`, native APIs |
| **Linux** | X11 XTest / Wayland events | `pynput`, `xdotool` |
| **Windows** | Windows API SendInput | `pynput`, `pyautogui` |

---

## Current Mock Implementation

The system currently uses mock bridges that return synthetic data:

**Frame Capture Mock**:
```python
# Currently returns empty frames with shape (1080, 1920, 3)
# Detection always succeeds with synthetic scores
```

**Input Mock**:
```python
# Currently always returns True
# No actual mouse/keyboard events issued
```

This allows full orchestration and API testing without a real game client.

---

## Implementation Path

### Phase 1: Platform-Agnostic Frame Capture

**Goal**: Real frame capture from GW2 window

**File to Create**: `src/adapters/host_capture_bridge.py`

**Pseudocode**:
```python
from PIL import ImageGrab
import numpy as np
from datetime import datetime, timezone

class HostCaptureBridge(CaptureBridge):
    def __init__(self, window_title: str = "Guild Wars 2"):
        self.window_title = window_title
    
    def capture(self) -> FrameCapture:
        # 1. Find GW2 window by title
        gw2_window = self._find_window(self.window_title)
        if not gw2_window:
            raise RuntimeError("GW2 window not found")
        
        # 2. Get window bounds (exclude decorations)
        bounds = gw2_window.get_bounds()  # (x, y, width, height)
        
        # 3. Capture frame buffer
        frame_pil = ImageGrab.grab(bbox=bounds)
        
        # 4. Convert to NumPy BGR
        frame_rgb = np.array(frame_pil)
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        
        # 5. Return with metadata
        return FrameCapture(
            frame=frame_bgr,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            raw_metadata={"window_bounds": bounds}
        )
    
    def _find_window(self, title: str):
        # Platform-specific window finder
        # On macOS: use Quartz / Cocoa APIs
        # On Linux: use X11 / wmctrl
        # On Windows: use Windows API / pygetwindow
        pass
```

**Dependencies**:
- `PIL` or `mss` (frame capture)
- `pygetwindow` (window finding, cross-platform)
- `cv2` (already in deps for OpenCV)

---

### Phase 2: Platform-Agnostic Input Automation

**Goal**: Real mouse/keyboard input to GW2 window

**File to Create**: `src/adapters/host_input_bridge.py`

**Pseudocode**:
```python
from pynput.mouse import Mouse, Button
from pynput.keyboard import Controller, Key
from src.core.orchestration.state_types import InputAction

class HostInputBridge(InputBridge):
    def __init__(self, window_title: str = "Guild Wars 2"):
        self.window_title = window_title
        self.mouse = Mouse()
        self.keyboard = Controller()
        self.window = None
    
    def emit_action(self, action: InputAction) -> bool:
        try:
            # 1. Ensure GW2 window has focus
            self.window = self._get_or_find_window()
            if not self._ensure_focused():
                return False
            
            # 2. Execute action based on type
            if action.action_type == "MOVE_MOUSE":
                self.mouse.position = (action.x, action.y)
            
            elif action.action_type == "CLICK":
                # Get window offset for coordinate transform
                offset_x, offset_y = self.window.get_position()
                self.mouse.position = (action.x + offset_x, action.y + offset_y)
                self.mouse.click(Button.left, 1)
            
            elif action.action_type == "TYPE":
                self.keyboard.type(action.text)
            
            elif action.action_type == "KEY_PRESS":
                self.keyboard.press(Key[action.key])
                self.keyboard.release(Key[action.key])
            
            return True
        
        except Exception as e:
            logger.error(f"Input action failed: {e}")
            return False
    
    def _ensure_focused(self) -> bool:
        # Platform-specific: bring window to foreground
        # macOS: NSApplication.shared.activate()
        # Linux: xdotool windowactivate
        # Windows: SetForegroundWindow()
        pass
    
    def _get_or_find_window(self):
        # Cache window handle to avoid repeated lookups
        pass
```

**Dependencies**:
- `pynput` (already in deps for input automation)
- Platform-specific focus APIs (Quartz/Cocoa, X11, Windows API)

---

### Phase 3: Integration into Startup

**File to Modify**: `src/api/main.py`

**Current**:
```python
def create_app() -> FastAPI:
    settings = get_settings()
    storage = Storage(settings.gw2_data_dir)
    
    # Mock bridges (currently used)
    capture_bridge = MockCaptureBridge()
    input_bridge = MockInputBridge()
    
    # ... rest of initialization
```

**Future**:
```python
def create_app() -> FastAPI:
    settings = get_settings()
    storage = Storage(settings.gw2_data_dir)
    
    # Real bridges (conditional on environment)
    if settings.gw2_host_bridge_enabled:
        capture_bridge = HostCaptureBridge(window_title="Guild Wars 2")
        input_bridge = HostInputBridge(window_title="Guild Wars 2")
    else:
        # Mock bridges for testing
        capture_bridge = MockCaptureBridge()
        input_bridge = MockInputBridge()
    
    # ... rest of initialization with real bridges
```

**Add to `.env`**:
```
GW2_HOST_BRIDGE_ENABLED=false  # Set to true when real bridges ready
```

---

## Testing Strategy

### Phase 1-2: Unit Tests for Bridge Implementations

**Test File**: `tests/unit/test_host_capture_bridge.py`

```python
def test_host_capture_produces_valid_frame():
    bridge = HostCaptureBridge()
    frame = bridge.capture()
    
    assert frame.frame.shape == (1080, 1920, 3)
    assert frame.frame.dtype == np.uint8
    assert frame.timestamp_utc is not None

def test_window_not_found_raises_error():
    bridge = HostCaptureBridge(window_title="NonExistent")
    
    with pytest.raises(RuntimeError):
        bridge.capture()
```

### Phase 2: Integration Tests

**Test File**: `tests/integration/test_host_bridge_capture_to_input.py`

```python
def test_capture_and_input_cycle():
    capture = HostCaptureBridge()
    input_bridge = HostInputBridge()
    
    # Capture frame
    frame = capture.capture()
    assert frame is not None
    
    # Issue input action (non-invasive: move mouse only)
    action = InputAction(
        action_type="MOVE_MOUSE",
        x=100, y=100
    )
    success = input_bridge.emit_action(action)
    assert success
```

---

## Platform-Specific Implementation Notes

### macOS

**Frame Capture**:
- Use `PIL.ImageGrab.grab()` with window bounds
- Or native Quartz: `CGWindowListCreateImage()`

**Input**:
- Use `pynput` (high-level, cross-platform)
- Or native Quartz: `CGEventPost()` for lower-level control

**Window Finding**:
- Use `pygetwindow` (simplest)
- Or native: `CGWindowListCopyWindowInfo()`

**Example**:
```python
import subprocess
import pygetwindow

gw2_window = pygetwindow.getWindowsWithTitle("Guild Wars 2")[0]
gw2_window.activate()  # Bring to focus
```

### Linux (X11)

**Frame Capture**:
- Use `mss` (fast, low-overhead)
- Or `ImageGrab` via X11 backend

**Input**:
- Use `pynput` or `xdotool`
- Ensure DISPLAY variable set

**Window Finding**:
- `wmctrl -l` to list windows
- `xdotool search --name "Guild Wars 2"`

**Example**:
```python
import mss
import subprocess

sct = mss.mss()
gw2_window_info = sct.monitors[1]  # Primary monitor
frame = sct.grab(gw2_window_info)
```

### Windows

**Frame Capture**:
- Use `PIL.ImageGrab` or `mss`
- Or DirectX11 capture for best perf

**Input**:
- Use `pynput` (simplest)
- Or `pyautogui` (higher-level)

**Window Finding**:
- `pygetwindow` (easiest)
- Or Windows API `FindWindow()`

---

## Performance Considerations

### Latency Budget (SC-008, SC-009)

- **Capture latency**: Target ≤100ms per frame
- **Input latency**: Target ≤50ms per command
- **Total capture-to-decision**: Target ≤500ms median, ≤900ms p95

**Optimization Tips**:
1. Cache window bounds to avoid repeated lookups
2. Use frame pooling to reduce allocation overhead
3. Minimize coordinate transformations
4. Batch input commands when possible

### Throughput

- **Frame capture**: Aim for min 10 FPS (100ms between frames)
- **Input queue**: Non-blocking, fire-and-forget semantics

---

## Error Handling & Recovery

### Capture Failures

If frame capture fails:
- Log error with timestamp
- Return cached last-good frame (TTL: 1 second max)
- After TTL, transition to ERROR state and stop bot

**Code**:
```python
def capture(self) -> FrameCapture:
    try:
        return self._real_capture()
    except WindowNotFoundError:
        if self._last_good_frame and time.time() - self._last_capture < 1.0:
            return self._last_good_frame
        raise
```

### Input Failures

If input fails:
- Log error with action details
- Retry up to N times with exponential backoff
- If all retries fail, signal to orchestrator

**Code**:
```python
def emit_action(self, action: InputAction) -> bool:
    for attempt in range(3):
        try:
            return self._real_emit(action)
        except Exception as e:
            if attempt < 2:
                time.sleep(0.1 * (2 ** attempt))  # Backoff
            else:
                logger.error(f"Action failed after retries: {e}")
                return False
```

---

## Security & Safety

### Window Focus

- Always verify GW2 window has focus before input
- Prevent accidental input to wrong window
- Timeout and release focus if stuck

### Input Sanitization

- Validate input coordinates are within game viewport
- Rate-limit input commands to prevent game lockup
- Never accept arbitrary keyboard shortcuts

### Capture Privacy

- Frames captured only from game window
- No desktop/taskbar capture
- Metadata logged but frames not persisted

---

## Deployment Checklist

- [ ] Frame capture implementation complete and tested
- [ ] Input automation implementation complete and tested
- [ ] Window focus management working on target platform
- [ ] Error recovery and retry logic functional
- [ ] Performance benchmarks within budget (≤500ms median)
- [ ] Container build includes platform-specific dependencies
- [ ] `.env` configuration properly documented
- [ ] Integration tests passing with real GW2 window
- [ ] 1-hour soak test completed without bridge failures
- [ ] Operator runbook updated with bridge troubleshooting

---

## Next Steps

1. **Implement Phase 1 (Capture)**: Start with your target platform (macOS/Linux/Windows)
2. **Test with Mock GW2**: Use a test window or recorded video frame source
3. **Implement Phase 2 (Input)**: Add input bridge after capture validated
4. **Integration Testing**: Run end-to-end with real GW2 client
5. **Performance Tuning**: Measure and optimize latency
6. **Production Deployment**: Enable `GW2_HOST_BRIDGE_ENABLED=true` and deploy

---

## References

- Bridge Interface Defs: [src/adapters/bridge_interfaces.py](../../src/adapters/bridge_interfaces.py)
- Frame Capture Service: [src/core/capture/frame_capture_service.py](../../src/core/capture/frame_capture_service.py)
- Input Automation Service: [src/core/actions/harvest_executor.py](../../src/core/actions/harvest_executor.py)
- Orchestrator Integration: [src/core/orchestration/farm_cycle_orchestrator.py](../../src/core/orchestration/farm_cycle_orchestrator.py)
- API Startup: [src/api/main.py](../../src/api/main.py)

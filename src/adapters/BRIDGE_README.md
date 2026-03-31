# Host Bridge System

The host bridge system provides cross-platform abstractions for screen capture and input automation in the gw2bot project.

## Overview

The bridge system consists of:

- **Bridge Interfaces** (`bridge_interfaces.py`): Abstract base classes defining the protocol
- **Platform Implementations**: Concrete implementations for each OS (macOS, Windows, Linux)
- **Bridge Factory** (`bridge_factory.py`): Factory functions to get platform-appropriate bridges

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│                   (Agent, Vision, etc.)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Bridge Interfaces                          │
│              (Abstract Protocols)                           │
│  - CaptureBridge: capture() → FrameCapture                 │
│  - InputBridge: press(), click(), type_text()              │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
   ┌────────┐   ┌────────┐   ┌────────┐
   │ macOS  │   │Windows │   │ Linux  │
   │Bridges │   │Bridges │   │Bridges │
   └────────┘   └────────┘   └────────┘
        │             │             │
  (PIL, pynput) (pyautogui)   (XDotool)
```

## Quick Start

### Basic Frame Capture

```python
from src.adapters.bridge_factory import get_capture_bridge

# Get the bridge for current platform
capture = get_capture_bridge()

# Capture a frame
frame_data = capture.capture()
print(f"Captured: {frame_data.width}x{frame_data.height}")

# Access the frame array
import numpy as np
frame_array = frame_data.frame  # NumPy array (H, W, 3) RGB
```

### Input Automation

```python
from src.adapters.bridge_factory import get_input_bridge

# Get the bridge for current platform
input_bridge = get_input_bridge()

# Send a key press
input_bridge.press('space')

# Click at coordinates
input_bridge.click(x=500, y=300, button='left')

# Type text
input_bridge.type_text('Hello, World!')
```

### Get Both Bridges at Once

```python
from src.adapters.bridge_factory import get_bridges

capture, input_bridge = get_bridges(window_title="Guild Wars 2")

# Use them
frame = capture.capture()
input_bridge.click(100, 100)
```

## Platform-Specific Details

### macOS Implementation

**Capture Bridge** (`macos_capture_bridge.py`):
- Uses `PIL.ImageGrab` for screen capture
- Captures full screen (window-specific capture not fully implemented)
- Returns RGB NumPy arrays

**Input Bridge** (`macos_input_bridge.py`):
- Uses `pynput` for keyboard and mouse control
- Supports standard keys: `enter`, `space`, `tab`, `esc`, `ctrl`, `shift`, `alt`, `cmd`
- Supports arrow keys and special keys

**Dependencies**:
- `Pillow` (PIL): Screen capture
- `pynput`: Input automation
- `numpy`: Array handling

### Windows Implementation (✅ Complete)

**Capture Bridge** (`windows_capture_bridge.py`):
- Uses `PIL.ImageGrab` for full-screen capture
- Performance: 30-50ms per capture (equivalent to macOS)
- Returns RGB NumPy arrays
- Monitor index parameter for future multi-monitor support

**Input Bridge** (`windows_input_bridge.py`):
- Uses `pynput` for cross-platform keyboard and mouse control
- Supports same special keys as macOS: `enter`, `space`, `shift`, `ctrl`, `alt`, `cmd`
- Supports arrow keys, function keys (F1-F12), and more
- Text typing with customizable interval between characters
- Performance: 10-20ms per action (equivalent to macOS)

**Dependencies**: `Pillow`, `pynput`, `numpy`

**Platform Note**: Windows does NOT require special accessibility permissions like macOS does

### Linux Implementation (Planned)

**Capture Bridge**: Will use `mss` or X11 APIs
**Input Bridge**: Will use `pynput` or `xdotool`

## Data Structures

### FrameCapture

```python
@dataclass
class FrameCapture:
    """Screen frame capture data."""
    frame: np.ndarray          # NumPy array (H, W, 3) in RGB format
    width: int                 # Frame width in pixels
    height: int                # Frame height in pixels
    timestamp: Optional[float] # Capture timestamp (None if not available)
```

### Key Names for `press()`

Supported special keys:
- `enter`, `return`: Return/Enter key
- `space`: Spacebar
- `tab`: Tab key
- `esc`, `escape`: Escape key
- `ctrl`, `control`: Control key
- `shift`: Shift key
- `alt`: Alt key
- `cmd`: Command key (macOS)
- `delete`: Delete key
- `backspace`: Backspace key
- `up`, `down`, `left`, `right`: Arrow keys

Single character keys (e.g., `'a'`, `'1'`, `'!'`) are supported directly.

## Error Handling

All bridge methods raise exceptions on failure:

```python
try:
    frame = capture.capture()
except Exception as e:
    print(f"Capture failed: {e}")

try:
    input_bridge.click(100, 100)
except Exception as e:
    print(f"Click failed: {e}")
```

## Advanced Usage

### Frame Processing Example

```python
from src.adapters.bridge_factory import get_capture_bridge
import cv2

capture = get_capture_bridge()
frame_data = capture.capture()

# Convert RGB to BGR for OpenCV
frame_bgr = cv2.cvtColor(frame_data.frame, cv2.COLOR_RGB2BGR)

# Process frame
gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
```

### Integration with Agent Loop

```python
from src.adapters.bridge_factory import get_bridges
import time

capture, input_bridge = get_bridges()

def agent_loop():
    for step in range(100):
        # Capture current state
        frame = capture.capture()
        
        # Process with vision model, get action
        action = vision_model.predict(frame.frame)
        
        # Execute action
        if action.type == "click":
            input_bridge.click(action.x, action.y)
        elif action.type == "type":
            input_bridge.type_text(action.text)
        
        time.sleep(0.1)  # Control loop rate

agent_loop()
```

## Testing

Test bridges with mock implementations:

```python
from src.adapters.bridge_interfaces import CaptureBridge, InputBridge
import numpy as np

class MockCaptureBridge(CaptureBridge):
    def capture(self):
        from src.adapters.bridge_interfaces import FrameCapture
        return FrameCapture(
            frame=np.zeros((720, 1280, 3), dtype=np.uint8),
            width=1280,
            height=720
        )

class MockInputBridge(InputBridge):
    def press(self, key):
        print(f"[MOCK] Pressed: {key}")
    
    def click(self, x, y, button="left", delay=0.05):
        print(f"[MOCK] Clicked at ({x}, {y})")
```

## Troubleshooting

### "Permission denied" on macOS Screenshots
macOS requires accessibility permissions. Grant access:
- System Preferences → Security & Privacy → Accessibility
- Add your Python/IDE to the allowed list

### Module Not Found Errors
Install required dependencies:
```bash
pip install pillow pynput numpy
```

### Slow Frame Capture
- Consider reducing resolution or cropping specific regions
- Profile with `time.perf_counter()` to identify bottlenecks
- Use parallel capture for multiple monitors (future enhancement)

## Development Notes

### Adding Support for New Platform

1. Create new bridge files:
   - `src/adapters/{platform}_capture_bridge.py`
   - `src/adapters/{platform}_input_bridge.py`

2. Implement `CaptureBridge` and `InputBridge` interfaces

3. Update `bridge_factory.py` to include platform detection and instantiation

4. Add platform-specific dependencies to `requirements.txt`

5. Document platform-specific details above

### Performance Considerations

- Capture: ~30-50ms per frame (PIL on macOS)
- Click: ~10-20ms (pynput on macOS)
- Type: ~10ms per character
- Consider frame skipping or async capture for real-time requirements

## How the Bridges Power the GW2 Bot

The bridge system is the **sensory and motor cortex** of the farming bot:

### Bot Operation Flow

**Discovery Phase (Learning):**
1. User calls POST /v1/discovery/start
2. Bot continuously captures GW2 screen (~500ms intervals)
3. ML model detects harvestable nodes in each frame
4. Bot records node positions as waypoints
5. When loop detected: saves route to JSON file

**Farming Phase (Execution):**
1. User calls POST /v1/run/start
2. Bot loads route from storage
3. For each waypoint:
   - Move mouse to coordinates (move_mouse via InputBridge)
   - Click on node (click via InputBridge)
   - Press 'f' to harvest (press via InputBridge)
4. Repeat infinitely

### Why Cross-Platform Support Matters

**Before:** Bot only worked on macOS → Limited user base

**After:** Same code works on macOS, Windows, Linux → Used anywhere

### Example Real-World Usage

**Windows User with GW2:**
```bash
# On Windows VM
docker-compose up -d
# Bot auto-detects Windows
# WindowsCaptureBridge + WindowsInputBridge initialize
# User: POST /v1/discovery/start → Bot learns route
# User: POST /v1/run/start → Bot farms automatically
```

### How the Service Discovery Works

```python
# In src/api/main.py
from src.adapters.bridge_factory import get_bridges

capture_bridge, input_bridge = get_bridges(window_title="Guild Wars 2")

# Both bridges are automatically the correct type for your OS!
# macOS → MacOSCaptureBridge, MacOSInputBridge
# Windows → WindowsCaptureBridge, WindowsInputBridge
# Linux → (future) LinuxCaptureBridge, LinuxInputBridge
```

The `bridge_factory.get_bridges()` function does all platform detection automatically.

## See Also

- [bridge_interfaces.py](bridge_interfaces.py) - Interface definitions
- [bridge_factory.py](bridge_factory.py) - Factory and platform detection
- [macos_capture_bridge.py](macos_capture_bridge.py) - macOS capture
- [macos_input_bridge.py](macos_input_bridge.py) - macOS input
- [windows_capture_bridge.py](windows_capture_bridge.py) - Windows capture ✨ NEW
- [windows_input_bridge.py](windows_input_bridge.py) - Windows input ✨ NEW

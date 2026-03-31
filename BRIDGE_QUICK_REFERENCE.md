# Bridge System - Quick Reference Card

## Installation
```bash
# Install dependencies
pip install pillow pynput numpy

# macOS: Grant accessibility permissions
# System Prefs → Security & Privacy → Accessibility → Add Python/IDE
```

## Import & Initialize

### Get Individual Bridges
```python
from src.adapters.bridge_factory import get_capture_bridge, get_input_bridge

capture = get_capture_bridge()
input_bridge = get_input_bridge()
```

### Get Both Bridges at Once
```python
from src.adapters.bridge_factory import get_bridges

capture, input_bridge = get_bridges()
```

### With Window Title (macOS: fallback to full screen)
```python
capture = get_capture_bridge(window_title="Guild Wars 2")
input_bridge = get_input_bridge(window_title="Guild Wars 2")
```

## Frame Capture API

### Basic Capture
```python
frame_data = capture.capture()
# Returns: FrameCapture(frame=np.ndarray, width=int, height=int, timestamp=float)
```

### Access Frame Data
```python
frame_data = capture.capture()

# Get dimensions
width = frame_data.width      # pixels
height = frame_data.height    # pixels

# Access NumPy array (RGB format)
rgb_array = frame_data.frame  # shape (height, width, 3)

# Get timestamp (if available)
timestamp = frame_data.timestamp  # Unix timestamp or None
```

### Frame Processing Examples
```python
import cv2

# Convert RGB to BGR for OpenCV
frame = capture.capture()
bgr = cv2.cvtColor(frame.frame, cv2.COLOR_RGB2BGR)

# Convert to grayscale
gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

# Detect edges
edges = cv2.Canny(gray, 100, 200)

# Find contours
contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
```

## Input Automation API

### Keyboard

#### Press Special Keys
```python
input_bridge.press('enter')      # Return/Enter
input_bridge.press('space')      # Spacebar
input_bridge.press('tab')        # Tab
input_bridge.press('esc')        # Escape
input_bridge.press('ctrl')       # Control
input_bridge.press('shift')      # Shift
input_bridge.press('alt')        # Alt
input_bridge.press('cmd')        # Command (macOS)
input_bridge.press('delete')     # Delete
input_bridge.press('backspace')  # Backspace
input_bridge.press('up')         # Up arrow
input_bridge.press('down')       # Down arrow
input_bridge.press('left')       # Left arrow
input_bridge.press('right')      # Right arrow
```

#### Press Character Keys
```python
input_bridge.press('a')    # Letter 'a'
input_bridge.press('1')    # Number '1'
input_bridge.press('!')    # Special character
```

#### Type Text
```python
input_bridge.type_text("Hello, World!")

# With custom interval (default: 0.05 seconds)
input_bridge.type_text("Fast typing", interval=0.01)
input_bridge.type_text("Slow typing", interval=0.1)
```

### Mouse

#### Click
```python
# Left click (default)
input_bridge.click(100, 200)
input_bridge.click(100, 200, button='left')

# Right click
input_bridge.click(100, 200, button='right')

# Middle click
input_bridge.click(100, 200, button='middle')

# With delay (default: 0.05s)
input_bridge.click(100, 200, delay=0.1)
```

#### Move Mouse
```python
input_bridge.move_mouse(500, 300)
```

## Common Patterns

### Agent Loop
```python
from src.adapters.bridge_factory import get_bridges
import time

capture, input_bridge = get_bridges()

for step in range(100):
    frame = capture.capture()
    
    # Process frame with vision model
    action = vision_model.predict(frame.frame)
    
    # Execute action
    if action.type == "click":
        input_bridge.click(action.x, action.y)
    elif action.type == "press":
        input_bridge.press(action.key)
    elif action.type == "type":
        input_bridge.type_text(action.text)
    
    time.sleep(0.1)  # ~10 FPS
```

### Wait for Action to Complete
```python
# Click and wait for UI to respond
input_bridge.click(100, 100)
time.sleep(0.5)  # Wait for UI

# Check if action succeeded
frame = capture.capture()
# ... validate result ...
```

### Sequence of Actions
```python
# Fill form
input_bridge.click(100, 100)  # Focus input
time.sleep(0.1)
input_bridge.type_text("user@example.com")
time.sleep(0.1)

input_bridge.press('tab')      # Move to next field
time.sleep(0.1)
input_bridge.type_text("password123")
time.sleep(0.1)

input_bridge.press('enter')    # Submit
```

### Multi-Step Navigation
```python
actions = [
    ("click", 100, 100),      # Click button
    ("pause", 0.5),           # Wait for UI
    ("key", "right"),         # Press arrow right
    ("key", "enter"),         # Press enter
    ("type", "Search term"),  # Type text
]

for action in actions:
    if action[0] == "click":
        input_bridge.click(action[1], action[2])
    elif action[0] == "key":
        input_bridge.press(action[1])
    elif action[0] == "type":
        input_bridge.type_text(action[1])
    elif action[0] == "pause":
        time.sleep(action[1])
```

## Performance Optimization

### Measure Frame Capture Performance
```python
import time

capture = get_capture_bridge()

# Measure single capture
start = time.perf_counter()
frame = capture.capture()
elapsed = time.perf_counter() - start
print(f"Capture time: {elapsed*1000:.1f}ms")

# Measure average over 10 captures
start = time.perf_counter()
for _ in range(10):
    frame = capture.capture()
elapsed = time.perf_counter() - start
print(f"Average: {elapsed*1000/10:.1f}ms per frame")
```

### Reduce Capture Frequency
```python
# Capture at 5 FPS instead of 30 FPS
capture_interval = 0.2  # seconds
last_capture = 0

while True:
    current_time = time.time()
    if current_time - last_capture > capture_interval:
        frame = capture.capture()
        last_capture = current_time
    
    time.sleep(0.01)  # Prevent busy loop
```

### Crop Region of Interest
```python
# PIL ImageGrab supports bbox cropping (if needed in future)
# For now, post-process the capture
frame = capture.capture()

# Extract region (top 100x100 pixels)
region = frame.frame[0:100, 0:100]
```

## Error Handling

### Capture Errors
```python
try:
    frame = capture.capture()
except PermissionError:
    print("Grant accessibility permissions (macOS)")
except Exception as e:
    print(f"Capture failed: {e}")
```

### Input Errors
```python
try:
    input_bridge.click(100, 100)
except Exception as e:
    print(f"Click failed: {e}")

try:
    input_bridge.press('enter')
except Exception as e:
    print(f"Key press failed: {e}")
```

## Testing

### Run Examples
```bash
python src/adapters/bridge_examples.py
```

### Run Tests
```bash
# All tests
pytest tests/test_bridge_system.py -v

# Specific test
pytest tests/test_bridge_system.py::TestPlatformDetection -v

# With coverage
pytest tests/test_bridge_system.py --cov=src/adapters
```

### Create Mock Bridges for Testing
```python
from src.adapters.bridge_interfaces import CaptureBridge, InputBridge, FrameCapture
import numpy as np

class MockCaptureBridge(CaptureBridge):
    def capture(self):
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
    
    def type_text(self, text, interval=0.05):
        print(f"[MOCK] Typed: {text}")
```

## Logging & Debugging

### Enable Debug Logging
```python
import logging

logging.basicConfig(level=logging.DEBUG)
capture = get_capture_bridge()
frame = capture.capture()  # Will print debug info
```

### Check Platform Detection
```python
from src.adapters.bridge_factory import get_platform

print(f"Platform: {get_platform()}")  # 'macos', 'windows', 'linux', or 'unknown'
```

## Documentation Links

- **Main Guide**: [src/adapters/BRIDGE_README.md](src/adapters/BRIDGE_README.md)
- **Configuration**: [src/adapters/BRIDGE_CONFIG.md](src/adapters/BRIDGE_CONFIG.md)
- **Examples**: [src/adapters/bridge_examples.py](src/adapters/bridge_examples.py)
- **Implementation Summary**: [BRIDGE_IMPLEMENTATION.md](BRIDGE_IMPLEMENTATION.md)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Permission denied" on macOS | Grant accessibility permissions in System Prefs |
| "Module not found" errors | `pip install pillow pynput numpy` |
| Black/blank screenshots | Ensure window is focused; check permissions |
| Input not working | Add delays between commands; ensure window has focus |
| Slow performance | Check capture time with `perf_counter`; consider ROI |

---

**Last Updated**: April 1, 2026  
**Version**: 1.0 (macOS implementation)

# Bridge System Configuration

## Installation

### macOS

Install required dependencies:

```bash
# Core dependencies
pip install pillow pynput numpy

# Optional: For advanced usage
pip install opencv-python  # Image processing
pip install pygetwindow    # Window management (fallback)
```

### Windows (Planned)

```bash
pip install pyautogui pillow pynput numpy
```

### Linux (Planned)

```bash
pip install pynput mss numpy
# or for X11-based systems:
pip install python-xlib xdotool
```

## Environment Variables

No environment variables are required. The bridge system auto-detects the platform.

## Permissions

### macOS

For screen capture to work, grant accessibility permissions:

1. Go to **System Preferences → Security & Privacy → Accessibility**
2. Click the lock icon to unlock
3. Add Python and your IDE (e.g., VS Code, PyCharm) to the list
4. Restart the IDE or Python process

If you see "Permission denied" errors, this is the likely cause.

## Requirements

### Python Version

- **Minimum**: Python 3.8
- **Recommended**: Python 3.10+

### Dependencies by Platform and Feature

| Dependency | Platform | Purpose | Optional |
|-----------|----------|---------|----------|
| `pillow` | macOS | Screen capture | No |
| `pynput` | macOS | Keyboard/mouse control | No |
| `numpy` | All | Array handling | No |
| `pyautogui` | Windows | Screen capture & input | Planned |
| `mss` | Linux | Screen capture | Planned |
| `xdotool` | Linux | Input automation | Planned |
| `opencv-python` | All | Image processing | Yes |
| `pygetwindow` | macOS/Windows | Window management | Yes |

## Performance Constraints

### Typical Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Frame capture | 30-50ms | PIL on macOS, full screen |
| Mouse click | 10-20ms | pynput |
| Key press | 5-10ms | pynput |
| Type character | 10-20ms | ~50 characters/second |

### Optimization Tips

1. **Frame capture**: Consider region-of-interest (ROI) cropping
2. **Input**: Batch multiple commands when possible
3. **Loop rate**: 10-30 FPS typical for agent loops
4. **Memory**: Reuse NumPy arrays to reduce allocations

## Troubleshooting

### "Permission denied" on macOS

```
OSError: [Errno 13] Permission denied
```

**Solution**: Grant accessibility permissions (see macOS section above)

### "Module not found" Errors

```
ModuleNotFoundError: No module named 'PIL'
```

**Solution**: Install dependencies
```bash
pip install pillow pynput numpy
```

### Slow Performance

1. Check if capture is the bottleneck:
   ```python
   import time
   from src.adapters.bridge_factory import get_capture_bridge
   
   capture = get_capture_bridge()
   start = time.perf_counter()
   for _ in range(10):
       frame = capture.capture()
   elapsed = time.perf_counter() - start
   print(f"Avg time per frame: {elapsed/10*1000:.1f}ms")
   ```

2. Profile with `cProfile`:
   ```bash
   python -m cProfile -s cumtime script.py
   ```

3. Consider:
   - Reducing frame resolution
   - Using region-of-interest captures
   - Running agent in separate thread
   - Pre-allocating NumPy arrays

### Screen Capture Returns Black/Blank

- Ensure the application window is in focus
- Check that the window isn't minimized
- On multi-monitor setups, verify `monitor_index` parameter
- macOS: Check accessibility permissions again

### Input Commands Don't Work

1. Ensure the target application is focused
2. Add delays between commands:
   ```python
   import time
   input_bridge.click(100, 100)
   time.sleep(0.1)  # Wait for UI to respond
   input_bridge.press('enter')
   ```

3. Try moving mouse before clicking:
   ```python
   input_bridge.move_mouse(100, 100)
   time.sleep(0.1)
   input_bridge.click(100, 100)
   ```

## Development Setup

### Running Tests

```bash
# Run all tests
python -m pytest tests/test_bridge_system.py -v

# Run specific test
python -m pytest tests/test_bridge_system.py::TestPlatformDetection -v

# With coverage
python -m pytest tests/test_bridge_system.py --cov=src/adapters --cov-report=html
```

### Running Examples

```bash
# Run all examples
python src/adapters/bridge_examples.py

# Or import in REPL
from src.adapters.bridge_examples import example_1_basic_capture
example_1_basic_capture()
```

### Development Tips

1. Use mock bridges for testing:
   ```python
   class MockCaptureBridge(CaptureBridge):
       def capture(self):
           return FrameCapture(
               frame=np.zeros((720, 1280, 3), dtype=np.uint8),
               width=1280,
               height=720
           )
   ```

2. Add logging for debugging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. Profile frame capture:
   ```python
   import cProfile
   import pstats
   from io import StringIO
   
   pr = cProfile.Profile()
   pr.enable()
   # ... capture code ...
   pr.disable()
   s = StringIO()
   ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
   ps.print_stats()
   print(s.getvalue())
   ```

## CI/CD Configuration

### GitHub Actions Example

```yaml
- name: Install bridge dependencies
  run: |
    pip install pillow pynput numpy pytest pytest-cov

- name: Run bridge tests
  run: |
    pytest tests/test_bridge_system.py -v --cov=src/adapters
```

Note: Screen capture tests may not run in headless CI environments.

## See Also

- [BRIDGE_README.md](BRIDGE_README.md) - Main documentation
- [bridge_factory.py](bridge_factory.py) - Factory functions
- [bridge_interfaces.py](bridge_interfaces.py) - Interface definitions
- [bridge_examples.py](bridge_examples.py) - Code examples

# Bridge Integration Guide

## Overview

The bot is **already designed to use bridges**! The services expect bridge instances:

- `FrameCaptureService(bridge: CaptureBridge)` - Needs capture bridge
- `HarvestExecutor(bridge: InputBridge)` - Needs input bridge

This guide shows how to wire them together in the app factory.

## Step 1: Update App Factory (src/api/main.py)

Add bridge initialization to `create_app()`:

```python
from src.adapters.bridge_factory import get_bridges
from src.core.capture.frame_capture_service import FrameCaptureService
from src.core.actions.harvest_executor import HarvestExecutor

def create_app() -> FastAPI:
    """Create the API app used by local runtime control endpoints."""

    settings = get_settings()
    configure_logging()

    app = FastAPI(title="GW2 Bot Control API", version="0.1.0")

    # ✅ NEW: Initialize host bridges
    capture_bridge, input_bridge = get_bridges(window_title="Guild Wars 2")
    
    # ✅ NEW: Create services with bridges
    frame_capture_service = FrameCaptureService(capture_bridge)
    harvest_executor = HarvestExecutor(input_bridge)

    storage = Storage(settings.gw2_data_dir)
    route_builder = RouteBuilder(storage)
    discovery_orchestrator = DiscoveryOrchestrator(route_builder)
    farm_cycle_orchestrator = FarmCycleOrchestrator(storage, discovery_orchestrator)
    event_writer = EventWriter(storage)
    cycle_summary_service = CycleSummaryService(storage)
    control_commands = ControlCommands(farm_cycle_orchestrator)

    # ✅ NEW: Store bridges in app state
    app.state.capture_bridge = capture_bridge
    app.state.input_bridge = input_bridge
    app.state.frame_capture_service = frame_capture_service
    app.state.harvest_executor = harvest_executor

    # ... rest of the existing code ...
```

## Step 2: Verify Integration

Run the app to ensure bridges are initialized:

```bash
cd /Users/filipdadgar/dev/gw2bot
docker-compose up -d
curl http://127.0.0.1:8000/health
# Should show: {"status":"ok","host_bridge":"enabled"}
```

## Step 3: Permissions Setup

**macOS ONLY - Required:**
Before running the bot, grant accessibility permissions:

```
System Preferences 
  → Security & Privacy 
  → Accessibility
  → Add Python and your IDE to the allowed list
```

**Windows - Not Required:**
Windows does NOT require special permissions for screen capture or input automation via pynput.

**Linux - Not Required:**
Linux does NOT require special permissions (future implementation).

## Testing Integration

### Test Frame Capture

```python
# In a test or endpoint
from src.adapters.bridge_factory import get_capture_bridge

capture = get_capture_bridge()
frame = capture.capture()

assert frame.width > 0
assert frame.height > 0
assert frame.frame.shape[2] == 3  # RGB
```

### Test Input Automation

```python
from src.adapters.bridge_factory import get_input_bridge

input_bridge = get_input_bridge()
input_bridge.click(100, 100)  # Should click at coordinates
input_bridge.press('space')    # Should send spacebar
```

### Test Full Integration

```python
from src.api.main import create_app

app = create_app()

# Verify bridges are created
assert app.state.capture_bridge is not None
assert app.state.input_bridge is not None
assert app.state.frame_capture_service is not None
assert app.state.harvest_executor is not None
```

## Configuration

### Environment Variables (Future)

```bash
# .env file
GW2_WINDOW_TITLE="Guild Wars 2"
GW2_HOST_BRIDGE_ENABLED=true
GW2_CAPTURE_MONITOR_INDEX=0
```

### Settings

Update [src/config/settings.py](src/config/settings.py) if needed:

```python
@dataclass
class Settings:
    gw2_host_bridge_enabled: bool = True
    gw2_window_title: str = "Guild Wars 2"
    gw2_capture_monitor_index: int = 0
    # ... existing settings ...
```

## Performance Tuning

### Capture Optimization

```python
from src.adapters.bridge_factory import get_capture_bridge

capture = get_capture_bridge()

# Time a few captures to establish baseline
import time
start = time.time()
for _ in range(10):
    frame = capture.capture()
elapsed = time.time() - start
print(f"Average: {elapsed/10*1000:.1f}ms per frame")
```

### Input Optimization

```python
from src.adapters.bridge_factory import get_input_bridge

input_bridge = get_input_bridge()

# Add timing delays between actions
input_bridge.click(100, 100)
time.sleep(0.1)  # Wait for UI response
input_bridge.press('enter')
```

## Troubleshooting

### "Permission denied" on macOS

**Error**: `OSError: [Errno 13] Permission denied`

**Solution**: Grant accessibility permissions (System Prefs → Security & Privacy → Accessibility)

### "Module not found: PIL"

**Error**: `ModuleNotFoundError: No module named 'PIL'`

**Solution**: Ensure dependencies are installed
```bash
pip install pillow pynput numpy
# or
cd /Users/filipdadgar/dev/gw2bot && pip install -e .
```

### Slow Frame Capture

**Problem**: Captures taking >100ms

**Debug**:
```python
import time
capture = get_capture_bridge()

# Measure individual components
start = time.time()
frame = capture.capture()
elapsed = time.time() - start
print(f"Capture time: {elapsed*1000:.1f}ms")
```

**Solutions**:
- Ensure no other processes are capturing screen
- Check if bot is running in background
- Profile with: `python -m cProfile -s cumtime script.py`

### Input Not Working

**Problem**: Clicks/keyboard don't register

**Debug**:
- Ensure target window (GW2) is focused
- Add delays between commands
- Check logs with: `logging.basicConfig(level=logging.DEBUG)`

## Related Documentation

- [BRIDGE_QUICK_REFERENCE.md](../BRIDGE_QUICK_REFERENCE.md) - API cheatsheet
- [src/adapters/BRIDGE_README.md](../src/adapters/BRIDGE_README.md) - Full reference
- [src/adapters/BRIDGE_CONFIG.md](../src/adapters/BRIDGE_CONFIG.md) - Setup guide
- [BRIDGE_IMPLEMENTATION.md](../BRIDGE_IMPLEMENTATION.md) - Implementation details

## Next Steps

1. ✅ Review this integration guide
2. ✅ Update [src/api/main.py](src/api/main.py) with bridge initialization
3. ✅ Grant macOS accessibility permissions
4. ✅ Run tests to verify integration
5. ✅ Test with live GW2 client
6. ✅ Deploy!

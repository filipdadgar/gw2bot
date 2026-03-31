# How the GW2 Bot Uses the Host Bridges

## Complete Operating Flowchart

This document explains **exactly how** the bot detects GW2, what to farm, and executes farming automation using the host bridge system.

---

## Part 1: Bot Detection & State Management

### 1.1 Does GW2 Exist?

The bot verifies GW2 is running through the bridge system:

```
┌─────────────────────────────┐
│   FastAPI App Startup       │
│   (src/api/main.py)         │
└──────────────┬──────────────┘
               │
     ┌─────────▼──────────┐
     │  get_bridges()     │
     │ (bridge_factory)   │
     └─────────┬──────────┘
               │
      ┌────────▼────────┐
      │ Platform Check  │
      │ platform.system()
      └────────┬────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
 Darwin    Windows      Linux
    │          │          │
┌───▼──┐  ┌───▼───┐   (future)
│macOS │  │Windows│
│Bridge│  │Bridge │
└───┬──┘  └───┬───┘
    │         │
    └────┬────┘
         │
    ┌────▼────────────┐
    │ Try to capture  │
    │ bridge.capture()│
    └────┬────────────┘
         │
    ┌────▼──────────┐
    │ Success?      │
    └────┬─────┬────┘
    YES  │     │ NO
         │     │
      ✅ GW2  ❌ GW2
       IS     NOT
      RUNNING RUNNING
```

**Code location**: `src/api/main.py` lines 32-45
```python
try:
    capture_bridge, input_bridge = get_bridges(window_title="Guild Wars 2")
    logger.info("✅ Host bridges initialized successfully")
    bridge_enabled = True  # ← GW2 is running
except Exception as e:
    logger.warning(f"⚠️ Host bridge initialization failed: {e}")
    bridge_enabled = False  # ← GW2 NOT running
```

If `bridge_enabled = False`, the bot logs a warning and runs in **simulation mode** (no real I/O).

---

## Part 2: What to Farm - Discovery Phase

### 2.1 User Initiates Discovery

User calls the API:
```bash
POST /v1/discovery/start
{
  "max_duration_seconds": 600,
  "min_loop_confidence": 0.7
}
```

**Code**: `src/api/routes/discovery.py`
```python
@router.post("/start")
def start_discovery(payload: StartDiscoveryRequest, request: Request):
    orchestrator = request.app.state.discovery_orchestrator
    return orchestrator.start(
        max_duration_seconds=payload.max_duration_seconds,
        min_loop_confidence=payload.min_loop_confidence,
    )
```

### 2.2 Discovery Loop (What Gets Recorded)

The discovery orchestrator continuously:

```
LOOP (until route loops detected):
  ├─ Capture frame
  │  └─ FrameCaptureService.capture_frame()
  │     └─ CaptureBridge.capture()  ← Gets RGB screenshot
  │
  ├─ Detect nodes in frame
  │  └─ NodeDetector.detect(frame)
  │     ├─ Run ML model (ultralytics YOLO)
  │     └─ Returns: [
  │          Detection(node_type="ore", confidence=0.95, x=1023, y=456),
  │          Detection(node_type="wood", confidence=0.92, x=1045, y=502),
  │          Detection(node_type="plant", confidence=0.88, x=1089, y=378),
  │        ]
  │
  ├─ Record waypoints
  │  └─ route.append({
  │       "x": detection.x,
  │       "y": detection.y,
  │       "node_type": detection.node_type
  │     })
  │
  └─ Check for loop
     └─ If position matches start position with confidence > 0.7:
        └─ Save route to JSON file
```

**Code locations**:
- `src/core/detection/node_detector.py` - ML detection
- `src/core/discovery/route_builder.py` - Route building
- `src/core/orchestration/discovery_orchestrator.py` - Discovery state

**Resulting file** (saved to disk):
```json
{
  "discovery_id": "discovery-a1b2c3d4",
  "route_id": "route-xyz789",
  "waypoints": [
    {"x": 1023, "y": 456, "node_type": "ore"},
    {"x": 1045, "y": 502, "node_type": "wood"},
    {"x": 1089, "y": 378, "node_type": "plant"},
    ...
  ],
  "loop_detected": true,
  "confidence": 0.85
}
```

### 2.3 What "min_loop_confidence" Does

Controls how confident the bot must be that it's back at the starting point:

```python
min_loop_confidence = 0.7  # 70% sure we looped

if loop_detected_confidence >= 0.7:
    # Save route - we're confident this is a repeating path
    finalize_route()
else:
    # Keep discovering - not yet sure if it loops
    continue_discovery()
```

Higher value = more cautious (needs to see much similarity to start)
Lower value = quicker to accept loop (greedy)

---

## Part 3: Farming Execution

### 3.1 User Starts Farm Run

User calls:
```bash
POST /v1/run/start
{
  "route_id": null,  # Auto-discover if null
  "auto_discover_if_missing": true,
  "loop_enabled": true
}
```

**Code**: `src/api/routes/run.py` + `src/core/orchestration/farm_cycle_orchestrator.py`

### 3.2 Farming Loop - The Core Action

For each waypoint in the learned route:

```
┌────────────────────────────────────────┐
│ FOR EACH WAYPOINT                      │
│ (waypoint = {x, y, node_type})         │
└────────┬─────────────────────────────┬─┘
         │                             │
     ┌───▼──────────────┐         ┌────▼──┐
     │ Move Mouse       │         │ Check │
     │ move_mouse(x, y) │         │ if OK │
     │                 │         └────────┘
     │ InputBridge →   │
     │ pynput moves    │
     │ cursor          │
     └───┬──────────────┘
         │
     ┌───▼───────────────┐
     │ Click Node        │
     │ click(x, y)       │
     │                   │
     │ InputBridge →    │
     │ pynput clicks    │
     │ left button      │
     └───┬───────────────┘
         │
     ┌───▼─────────────────┐
     │ Press Harvest Key   │
     │ press('f')          │
     │                     │
     │ InputBridge →      │
     │ pynput sends 'f'   │
     │ GW2 harvests node  │
     └───┬─────────────────┘
         │
     ┌───▼────────────┐
     │ Wait ~500ms    │
     │ (animation)    │
     └───┬────────────┘
         │
     ┌───▼────────────────┐
     │ Next Waypoint      │
     │ (or restart loop)  │
     └────────────────────┘
```

**Harvest Executor Code** (`src/core/actions/harvest_executor.py`):
```python
class HarvestExecutor:
    def __init__(self, bridge: InputBridge):
        self._bridge = bridge
    
    def execute(self, x: int, y: int, key: str = "f", max_retries: int = 2):
        for retry in range(max_retries + 1):
            try:
                self._bridge.click(x, y)         # Move & click
                self._bridge.press(key)          # Press 'f'
                return HarvestResult(success=True)
            except Exception:
                if retry == max_retries:
                    return HarvestResult(success=False)
```

### 3.3 How State Machine Tracks Everything

**State Transitions** (`src/core/orchestration/farm_state_machine.py`):

```
IDLE ──→ RUNNING ──→ PAUSED
         ↑    ↓       ↓
         └────┼───────┘
              │
              ↓
          STOPPING
              ↓
          STOPPED/IDLE
```

**Persisted in**: `app.state.farm_cycle_orchestrator._snapshot`

```python
@dataclass
class RunSnapshot:
    cycle_id: str              # Unique farm run ID
    route_id: str              # Which route being farmed
    status: str                # Current state (RUNNING, PAUSED, etc.)
    current_waypoint_index: int  # Progress through route
    started_at_utc: str        # When farm started
    last_error: str | None     # Error message if failed
```

---

## Part 4: Real-World Examples

### Example 1: macOS User - Node on Screen

**What happens:**

```
User system: macOS (Darwin)
↓
platform.system() = "Darwin"
↓
Bridge factory chooses: MacOSCaptureBridge
↓
PIL.ImageGrab.grab() on macOS  
↓
Gets screenshot ✅
↓
Bot detects "ore" node at x=1023, y=456
↓
Later: execute HarvestExecutor
  → click(1023, 456)  [pynput on macOS]
  → press('f')
  → GW2 harvests ore node ✅
```

### Example 2: Windows User - Farming Automation

**Scenario**: User has Windows VM with GW2, bot in Docker

```
User system: Windows
↓
platform.system() = "Windows"
↓
Bridge factory chooses: WindowsCaptureBridge
↓
PIL.ImageGrab.grab() on Windows
↓
Gets screenshot ✅
↓
Discovery learns route:
  [waypoint 1: ore @ x=800, y=600],
  [waypoint 2: wood @ x=850, y=620],
  [waypoint 3: plant @ x=900, y=580]
↓
Farm run starts:
  iterate route:
    → click(800, 600) [pynput on Windows]
    → press('f')
    → wait
    → click(850, 620)
    → press('f')
    → wait
    → click(900, 580)
    → press('f')
    → wait
    → repeat infinitely ✅
```

---

## Part 5: API Endpoints (User Interface)

Endpoints exposed for controlling the bot:

### Discovery
```bash
POST /v1/discovery/start
  ↓ Starts learning farming route
  
GET /v1/discovery/status
  ↓ Returns current discovery progress
  
POST /v1/discovery/stop
  ↓ Stops discovery, saves route
```

### Farming
```bash
POST /v1/run/start
  ↓ Starts automatic farming
  
GET /v1/run/status
  ↓ Current farming progress
  
POST /v1/run/pause
  ↓ Pause harvesting (keep state)
  
POST /v1/run/resume
  ↓ Resume from pause
  
POST /v1/run/stop
  ↓ Stop farming gracefully
```

### Health
```bash
GET /health
  ↓ {"status": "ok", "host_bridge": "enabled" or "disabled"}
```

---

## Part 6: How Windows & macOS Differ (Same Code!)

| Aspect | macOS | Windows | Impact |
|--------|-------|---------|--------|
| Frame Capture | PIL.ImageGrab | PIL.ImageGrab | ✅ Identical |
| Input Lib | pynput | pynput | ✅ Identical |
| Permissions | Accessibility Settings | None | ⚠️ Runtime setup varies |
| Performance | 30-50ms capture | 30-50ms capture | ✅ Same |
| Platform Code | `macos_*_bridge.py` | `windows_*_bridge.py` | ✅ Same logic |

**Key**: `bridge_factory.get_bridges()` auto-selects based on platform. Service code needs NO changes.

---

## Part 7: Decision Tree: How Bot Decides Path

```
START
  │
  ├─ Discovery phase active?
  │   │
  │   ├─ YES → Continuous frame capture + node detection
  │   │        Record waypoints until loop detected
  │   │        Save route JSON
  │   │
  │   └─ NO → Farm phase
  │           Load route from storage
  │           Execute harvest at each waypoint
  │
  │
  └─ Node detection confident enough?
      │
      ├─ YES (confidence > threshold)
      │   └─ Record as target
      │
      └─ NO
          └─ Skip this frame
```

---

## Summary

**The bot:**

1. **Detects GW2** → Bridge initialization success/failure
2. **Learns what to farm** → ML node detection + route recording 
3. **Knows what confidence level** → `min_loop_confidence` parameter
4. **Executes farming** → Click + press actions via input bridge
5. **Tracks state** → State machine + persistent snapshots
6. **Works anywhere** → Bridge factory handles OS differences

**All controlled via REST API** that users call to control the farm run.

---

## Files Involved

**Detection/State**:
- `src/core/detection/node_detector.py` - ML detection
- `src/core/orchestration/discovery_orchestrator.py` - Discovery logic
- `src/core/orchestration/farm_cycle_orchestrator.py` - Farm state
- `src/core/orchestration/farm_state_machine.py` - FSM

**Execution**:
- `src/core/capture/frame_capture_service.py` - Frame capture wrapper
- `src/core/actions/harvest_executor.py` - Click + press execution
- `src/core/discovery/route_builder.py` - Route construction

**Bridges** (OS adapter):
- `src/adapters/bridge_interfaces.py` - Contract
- `src/adapters/bridge_factory.py` - Platform detection + factory
- `src/adapters/macos_capture_bridge.py` - macOS frame capture
- `src/adapters/macos_input_bridge.py` - macOS input control
- `src/adapters/windows_capture_bridge.py` - Windows frame capture ✨ NEW
- `src/adapters/windows_input_bridge.py` - Windows input control ✨ NEW

**API**:
- `src/api/main.py` - App factory + bridge initialization
- `src/api/routes/discovery.py` - Discovery endpoints
- `src/api/routes/run.py` - Farm run endpoints

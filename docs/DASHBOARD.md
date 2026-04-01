# GW2 Bot Web Dashboard

A browser-based control interface for the GW2 Bot. Open it in a background tab — it never steals focus from GW2.

**URL**: `http://localhost:8000`  
**Auto-refresh**: every 2 seconds

---

## Cards

### Run Status
| Field | Description |
|---|---|
| Status | `RUNNING` / `PAUSED` / `STOPPED` / `IDLE` |
| Cycle ID | Unique ID for the current farming run |
| Route | Route file being followed |
| Waypoint | Step counter for the current route |
| **Manual Override** | **ACTIVE** (amber, pulsing) when you touched the keyboard/mouse in the last 3 s — bot input is suppressed |
| **Gather Lock** | Remaining ms of post-harvest movement suppression |

**Buttons**: Start / Pause (toggles to Resume) / Stop

---

### Player Position *(requires GW2 running with MumbleLink)*
| Field | Description |
|---|---|
| MumbleLink | `Connected` (green) or `Offline` (red) |
| Mount | Current mount name, e.g. `🐾 Griffon`, or `🚶 On foot` |
| Map ID | GW2 map ID for the current zone |
| World X / Z | Avatar world-space coordinates (metres) |
| Continent X / Y | Minimap/cartography coordinates |

MumbleLink reads GW2's built-in shared memory — no addon required. It updates every bot loop iteration (~150 ms).

---

### Route Recording
Use this to build a real farming route from your manual play session.

**Workflow:**
1. Click **⏺ Start** — begins recording
2. Mount up (`X`) and fly to each resource node
3. Press **`F`** on each node — each harvest records a waypoint
4. Watch the **Waypoints** counter increase
5. When you've completed the loop, click **💾 Save Route**

| Field | Description |
|---|---|
| Status | `RECORDING` (amber, pulsing) or `Idle` |
| Waypoints | Number of positions recorded so far |
| Saved Routes | Total routes on disk |

**Buttons**: Start / Save Route / Discard

> Waypoints are only added when you're at least 15 world units from the previous one, so hovering over one node doesn't create duplicates. Routes are locked to the first map you're on — if you teleport, the new positions are ignored.

---

### Policy Model
| Field | Description |
|---|---|
| Latest Model | Model ID of the most recently trained artifact |
| Samples | Number of policy signals the model was trained on |
| Actions Learned | Number of distinct action types in the model |
| Trained | Timestamp of last training run |

**Button**: Train Now — triggers an immediate retrain from all accumulated telemetry.

Auto-retrain runs every 5 minutes while the bot is active (`GW2_TRAINING_AUTO_RETRAIN_ENABLED=true`).

---

### Host Bridge
| Field | Description |
|---|---|
| Bridge Status | `ENABLED` / `DISABLED` |
| Capture Enabled | Whether screen capture is active |
| Input Execution | Whether keyboard input is being sent to GW2 |
| Frame Resolution | Captured screen resolution |

---

### Recent Actions Log
Each row is one bot loop iteration (every ~150 ms). Columns:

| Field | Description |
|---|---|
| Time | Timestamp of the step |
| Action | `navigate`, `harvest`, or `interact` |
| `[gather_lock]` tag | Input was suppressed — post-harvest lock active |
| `[manual_input]` tag | Input was suppressed — you were touching the keyboard |
| `🙋 manual` tag | Manual override window was active during this step |
| Reward | Policy reward proxy for this step |
| Step | Step counter |
| Prompt | Whether the gather prompt was visible on screen |
| Bias | Steering direction: `-1` left, `0` straight, `+1` right |
| Mount | `remount` when the bot triggered a remount after harvest |

---

### Settings
Display-only toggles and confidence slider. To persistently change settings, edit `.env` and restart.

---

## API Endpoints Used

### Run control
- `GET /v1/run/status`
- `POST /v1/run/start` / `/pause` / `/resume` / `/stop`

### Policy
- `POST /v1/training/policy/train`
- `GET /v1/training/policy/versions`

### Telemetry
- `GET /v1/telemetry/recent-signals?limit=10`

### Position & recording *(new)*
- `GET /v1/discovery/position` — live MumbleLink snapshot
- `POST /v1/discovery/record/start` — begin route recording
- `POST /v1/discovery/record/stop` — save recorded route
- `POST /v1/discovery/record/discard` — discard without saving
- `GET /v1/discovery/record/status` — recording state + waypoint count
- `GET /v1/discovery/routes` — list all saved routes

### Health
- `GET /health`

---

## Settings Reference

To change bot behaviour permanently, edit `.env` and restart:

```bash
# Loop speed (lower = smoother movement)
GW2_RUNTIME_SIGNAL_INTERVAL_MS=150

# Suppression windows
GW2_RUNTIME_GATHER_LOCK_SECONDS=3.0
GW2_RUNTIME_GATHER_PROMPT_LATCH_SECONDS=3.0
GW2_RUNTIME_MANUAL_PAUSE_SECONDS=3.0

# MumbleLink
GW2_MUMBLE_LINK_ENABLED=true

# Policy
GW2_RUNTIME_POLICY_ENABLED=true
GW2_RUNTIME_POLICY_MIN_CONFIDENCE=0.7
GW2_RUNTIME_INPUT_ENABLED=true
GW2_RUNTIME_MOUNT_CYCLE_ENABLED=true

# Training
GW2_TRAINING_AUTO_RETRAIN_ENABLED=true
GW2_TRAINING_RETRAIN_INTERVAL_SECONDS=300
GW2_DEMO_AUTO_CAPTURE_ENABLED=true
```

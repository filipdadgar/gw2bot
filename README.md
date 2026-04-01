# GW2 Farming Bot — Project Summary & Current State

**Date**: 1 April 2026  
**Status**: Active development — Windows native, real GW2 integration in progress  
**Phase**: MumbleLink position tracking live; route recording and learning pipeline functional

---

## Mission

A self-learning GW2 resource farming bot that:

- Mounts up (`X`), flies around the map
- Detects resource nodes and flies down to them
- Presses `F` to harvest
- Learns the route from your manual play via demonstration recording
- Retrains its policy continuously to improve behaviour over time

---

## What's Working Now

### ✅ Movement & Navigation
- Runtime loop runs at **150 ms intervals** (was 1 s) — smooth, continuous movement
- `W` key held for **400 ms** per step — fluid forward movement while flying/running
- **Real steering** via MumbleLink cross-product: bot calculates left/right from the avatar's actual facing vector vs. waypoint direction (replaces pixel-delta guesswork)
- Auto-advances route target waypoint when within 40 world units
- Remount (`X`) triggered automatically after each harvest

### ✅ Manual Harvesting Protection
- `ManualInputListener` fires `notify_manual_input()` on every key/click
- Bot suppresses all input for **3 seconds** after each manual key (resets per keystroke)
- Dashboard shows **Manual Override: ACTIVE** (amber, pulsing) while suppressed
- Gather lock suppresses movement for **3 s** after bot-triggered harvests

### ✅ Real Position Tracking (MumbleLink)
- `MumbleLinkReader` reads GW2's built-in shared memory API — no addons, no permissions
- Provides: world-space X/Y/Z, avatar facing vector, continent coordinates, map ID, mount index
- Mount state (on foot / Jackal / Griffon / Springer / Skimmer / Raptor / Skyscale / etc.) exposed in state features and dashboard
- Falls back gracefully if GW2 is not running

### ✅ Route Recording from Manual Play
- **How**: Click "⏺ Start" in dashboard → fly your route → press `F` on each node → click "💾 Save Route"
- Each `F` keypress records current MumbleLink position as a waypoint (min 15 world-unit spacing)
- Saves real world coordinates — bot uses these for actual navigation, not placeholder `(100,100)`
- Routes are locked to the first map seen so teleports don't corrupt them
- Old placeholder routes should be deleted (see Data Reset below)

### ✅ Learning Pipeline (Fixed)
- **Keypresses are now captured**: `DemonstrationRecorder` auto-starts a session so no explicit API call is needed
- **State keys now match**: `normalize_state_key` buckets floats to 1 decimal place and excludes metadata fields (`gather_lock_remaining_ms`, `frame_width`, etc.) — states from different frames can now match in the policy table
- **Meaningful rewards**: harvest=1.0, interact=0.8, navigate=0.2 (was `contrast+0.2` noise)
- **Richer state features**: `is_mounted`, `mount_index`, `map_id`, `pos_x`, `pos_z`, `waypoint_dist`, `manual_input_active`, `gather_lock_remaining_ms`
- Auto-retrain every 300 s while running

### ✅ Web Dashboard (`http://localhost:8000`)
- **Run Status**: status badge, cycle ID, route, waypoint, Manual Override indicator, Gather Lock timer
- **Player Position**: MumbleLink online/offline, mount name, map ID, world X/Z, continent X/Y
- **Route Recording**: Start / Save / Discard buttons, live waypoint counter, saved route count
- **Policy Model**: latest model ID, sample count, trained timestamp, Train Now button
- **Host Bridge**: bridge enabled/disabled, capture status, frame resolution
- **Recent Actions**: per-step action, reward, prompt visibility, nav bias, mount events, suppression reason tags

---

## What's NOT Implemented (Stubs / Planned)

| Component | Status | Notes |
|---|---|---|
| `DiscoveryOrchestrator.start()` | ⚠️ Stub | Hardcodes fake scores; use Route Recording instead |
| `NodeDetector` | ⚠️ Stub | Predictor hook is `None`; no computer vision for nodes yet |
| `MinimapExtractor` | ⚠️ Stub | Data model exists but never called from the main loop |
| Linux host bridge | ❌ Not started | macOS and Windows implemented |

The **discovery auto-start** (`auto_discover_if_missing=True`) now reuses the most recent saved route instead of generating a new identical placeholder each startup.

---

## Data Reset (Important)

If you have existing data from before 1 April 2026, it was recorded with broken state keys and placeholder routes. Clear it:

```bash
# From the gw2bot directory
rm data/telemetry/policy-signals.jsonl   # broken state key format
rm data/models/policy-*.json             # trained on broken data
rm data/routes/route-*.json              # all identical (100,100)→(220,220)
```

Keep `data/telemetry/discovery-sessions.jsonl` — that's just an audit log.

---

## Getting Started (Windows Native)

See [Windows Native Setup Guide](docs/operations/WINDOWS_NATIVE_SETUP.md) for full installation.

### Quick Start

```bash
# Start the API
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Open dashboard
http://localhost:8000
```

### First-Time Route Recording Workflow

1. Start GW2 and load into the map you want to farm
2. Open `http://localhost:8000` in a browser
3. Check **Player Position** card — MumbleLink should show "Connected"
4. Click **⏺ Start** in the Route Recording card
5. Mount up (`X`), fly to each resource node, press `F` to harvest
6. Watch the **Waypoints** counter increase with each harvest
7. When you've covered the full loop, click **💾 Save Route**
8. The bot will now use those real coordinates for navigation

### After Recording a Route

The bot auto-starts on API launch (`GW2_AUTOSTART_RUN_ENABLED=true`). Let it run alongside your play session. It will:

- Navigate using the real waypoints you recorded
- Steer based on your avatar's actual facing direction (MumbleLink)
- Suppress its own input for 3 s whenever you touch the keyboard
- Record your keypresses as training data automatically
- Retrain the policy every 5 minutes

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Control API                         │
│  /run/*, /discovery/*, /training/*, /telemetry/*                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                  Orchestration Layer                             │
│  • FarmCycleOrchestrator  — 150 ms loop, MumbleLink steering    │
│  • DiscoveryOrchestrator  — (stub; use Route Recording)         │
│  • ControlCommands        — pause / resume / stop               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│               Core Service Modules                               │
│                                                                   │
│  Capture          Detection         Navigation                   │
│  frame_cap_svc    node_detector*    waypoint_navigator           │
│  interact_detect  minimap_ext*      route_recorder ✅ NEW        │
│                                                                   │
│  Training                           Telemetry                   │
│  demo_recorder ✅ fixed             event_writer                 │
│  manual_input_listener ✅ fixed     cycle_summary_svc            │
│  policy_trainer ✅ fixed            policy_signal_emitter        │
│  policy_registry                                                 │
│                                                                   │
│  * stub — no real inference wired                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                   Host Bridge Layer                              │
│                                                                   │
│  WindowsCaptureBridge   WindowsInputBridge   MumbleLinkReader   │
│  (screen capture)       (keyboard/mouse)     ✅ NEW — position  │
│  macOS impl available   macOS impl available  Windows only       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│              GW2 Client (Windows)                                │
│  • Screen capture via GDI                                        │
│  • Input via pynput / SendInput                                  │
│  • Position via MumbleLink shared memory (built-in GW2 API)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Environment Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `GW2_RUNTIME_SIGNAL_INTERVAL_MS` | `150` | Bot loop interval in ms |
| `GW2_RUNTIME_GATHER_LOCK_SECONDS` | `3.0` | Movement suppression after bot harvest |
| `GW2_RUNTIME_GATHER_PROMPT_LATCH_SECONDS` | `3.0` | Sticky harvest intent window |
| `GW2_RUNTIME_MANUAL_PAUSE_SECONDS` | `3.0` | Suppression window after manual input |
| `GW2_MUMBLE_LINK_ENABLED` | `true` | Enable MumbleLink position reading |
| `GW2_RUNTIME_POLICY_ENABLED` | `true` | Use trained policy for action selection |
| `GW2_RUNTIME_INPUT_ENABLED` | `true` | Send actual keyboard input |
| `GW2_RUNTIME_MOUNT_CYCLE_ENABLED` | `true` | Auto-remount after harvest |
| `GW2_RUNTIME_WAYPOINT_STEERING_ENABLED` | `true` | Use waypoints for steering bias |
| `GW2_RUNTIME_POLICY_MIN_CONFIDENCE` | `0.7` | Minimum policy confidence to act |
| `GW2_TRAINING_AUTO_RETRAIN_ENABLED` | `true` | Retrain policy on schedule |
| `GW2_TRAINING_RETRAIN_INTERVAL_SECONDS` | `300` | Retrain interval (5 min) |
| `GW2_AUTOSTART_RUN_ENABLED` | `true` | Auto-start bot on API startup |
| `GW2_DEMO_AUTO_CAPTURE_ENABLED` | `true` | Always capture manual keypresses |

---

## Key Files Reference

| Purpose | File |
|---|---|
| **Bot main loop** | [src/core/orchestration/farm_cycle_orchestrator.py](src/core/orchestration/farm_cycle_orchestrator.py) |
| **MumbleLink reader** | [src/adapters/mumble_link_reader.py](src/adapters/mumble_link_reader.py) |
| **Route recorder** | [src/core/navigation/route_recorder.py](src/core/navigation/route_recorder.py) |
| **Gather prompt detection** | [src/core/capture/interaction_prompt_detector.py](src/core/capture/interaction_prompt_detector.py) |
| **Policy state key** | [src/core/training/policy_signal_dataset.py](src/core/training/policy_signal_dataset.py) |
| **Manual input listener** | [src/core/training/manual_input_listener.py](src/core/training/manual_input_listener.py) |
| **Discovery & recording API** | [src/api/routes/discovery.py](src/api/routes/discovery.py) |
| **App wiring** | [src/api/main.py](src/api/main.py) |
| **Dashboard** | [src/api/static/dashboard.html](src/api/static/dashboard.html) |
| **Settings** | [src/config/settings.py](src/config/settings.py) |
| **Windows input bridge** | [src/adapters/windows_input_bridge.py](src/adapters/windows_input_bridge.py) |
| **Operator runbook** | [docs/operations/gw2bot-runbook.md](docs/operations/gw2bot-runbook.md) |
| **Dashboard guide** | [docs/DASHBOARD.md](docs/DASHBOARD.md) |

# Quickstart: GW2 Farming Bot

**Updated**: 1 April 2026  
**Platform**: Windows native (Python + GW2 on same machine)

---

## Control Interfaces

| Interface | URL | Use case |
|---|---|---|
| **Web Dashboard** | `http://localhost:8000` | Recommended — no focus stealing, live status |
| **REST API** | `http://localhost:8000/docs` | Scripting, automation |

---

## 1. Start the Bot

```bash
# From the gw2bot directory with venv active
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`. The bot auto-starts a run if a saved route exists.

---

## 2. First Time: Record a Real Route

> Old data warning: if you have existing routes/models from before 1 April 2026, delete them first — they contain placeholder coordinates and broken training data:
> ```bash
> rm data/routes/route-*.json
> rm data/telemetry/policy-signals.jsonl
> rm data/models/policy-*.json
> ```

**Via dashboard:**

1. Load GW2 into your farming map
2. Check **Player Position** card — should show **MumbleLink: Connected**
3. Click **⏺ Start** in the Route Recording card
4. Mount (`X`), fly to each resource node, press `F` to harvest each one
5. Waypoints counter increments with each `F` press
6. Click **💾 Save Route** when you've completed the loop

**Via API:**
```bash
curl -X POST http://localhost:8000/v1/discovery/record/start
# ... play in GW2, press F on nodes ...
curl http://localhost:8000/v1/discovery/record/status    # check waypoint count
curl -X POST http://localhost:8000/v1/discovery/record/stop   # save
```

Restart the bot after saving — it will now follow your recorded route.

---

## 3. Monitor Live Position

Check MumbleLink is reading GW2 correctly:

```bash
curl http://localhost:8000/v1/discovery/position
```

```json
{
  "available": true,
  "avatar_x": -3421.5,
  "avatar_z": 8234.1,
  "map_id": 1206,
  "is_mounted": true,
  "mount_name": "Griffon"
}
```

If `available: false` — GW2 is not running or still on character selection screen.

---

## 4. Let It Learn From Your Play

Manual keypresses are captured automatically (`GW2_DEMO_AUTO_CAPTURE_ENABLED=true`). Just play normally:

- Every `F` key = harvest signal with reward 1.0
- Every `W/A/S/D` key = navigate signal with reward 0.2
- Bot suppresses its own input for 3 s after each of your keypresses (**Manual Override** badge goes amber)

Watch the policy-signals file grow:
```bash
# Count signals recorded
wc -l data/telemetry/policy-signals.jsonl
```

---

## 5. Run Control

```bash
# Status
curl http://localhost:8000/v1/run/status

# Pause / Resume / Stop
curl -X POST http://localhost:8000/v1/run/pause
curl -X POST http://localhost:8000/v1/run/resume
curl -X POST http://localhost:8000/v1/run/stop

# Start with a specific route
curl -X POST http://localhost:8000/v1/run/start \
  -H "Content-Type: application/json" \
  -d '{"route_id":"route-abc12345"}'
```

---

## 6. Policy Training

Training happens automatically every 5 minutes. To trigger manually:

```bash
curl -X POST http://localhost:8000/v1/training/policy/train
```

Or click **🎓 Train Now** in the dashboard.

Check what the model has learned:
```bash
curl http://localhost:8000/v1/training/policy/versions
```

---

## 7. What the Bot Does (Loop Summary)

Every ~150 ms the bot:

1. Captures the GW2 screen frame
2. Reads MumbleLink (position, mount state, map ID)
3. Detects if the gather prompt is visible on screen
4. Checks if you've touched the keyboard in the last 3 s → if yes, suppresses its own input
5. Selects action: `harvest` (prompt visible) or `navigate` (policy/fallback)
6. If navigating: presses `W` for 400 ms, steers left/right toward next waypoint using cross-product of facing vector × waypoint direction
7. If harvesting: taps `F`, sets gather lock (3 s), flags remount pending
8. On next navigate after harvest: taps `X` to remount
9. Emits telemetry signal for training

---

## 8. Key Settings (`.env`)

```bash
GW2_RUNTIME_SIGNAL_INTERVAL_MS=150          # Loop speed
GW2_RUNTIME_GATHER_LOCK_SECONDS=3.0         # Post-harvest movement pause
GW2_RUNTIME_MANUAL_PAUSE_SECONDS=3.0        # Hands-off window after your keypresses
GW2_MUMBLE_LINK_ENABLED=true                # Real position tracking
GW2_RUNTIME_POLICY_ENABLED=true             # Use learned policy
GW2_RUNTIME_INPUT_ENABLED=true              # Send actual keys to GW2
GW2_TRAINING_AUTO_RETRAIN_ENABLED=true      # Retrain every 5 min
GW2_DEMO_AUTO_CAPTURE_ENABLED=true          # Always record your keypresses
GW2_AUTOSTART_RUN_ENABLED=true              # Start bot on API launch
```

---

## 9. Troubleshooting Quick Reference

| Symptom | Fix |
|---|---|
| MumbleLink Offline | GW2 must be running and in-map (not character select) |
| Bot doesn't move | Check `GW2_RUNTIME_INPUT_ENABLED=true` |
| Bot interrupts harvesting | Check Manual Override badge — should turn amber on keypress |
| Policy only ever navigates | Clear old data (see top of this doc), retrain |
| Routes are all identical | Delete old routes, record a real one with Route Recording |
| Waypoints not recording | Check MumbleLink is Connected before pressing F |

Full troubleshooting: [docs/operations/gw2bot-runbook.md](../../docs/operations/gw2bot-runbook.md)

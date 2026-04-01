# GW2 Bot Operator Runbook

**Updated**: 1 April 2026  
**Platform**: Windows native (Python direct, no Docker required)

---

## Prerequisites

- Windows 10/11
- Python 3.11+
- Guild Wars 2 installed and running
- Bot dependencies installed: `pip install -r requirements.txt`

---

## Starting the Bot

```bash
# From the gw2bot directory
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` for the dashboard.

With `GW2_AUTOSTART_RUN_ENABLED=true` (default), the bot starts a farming run automatically on launch. If a saved route exists it reuses the most recent one; if none exist it creates a placeholder (record a real route first — see below).

---

## First-Time Setup: Recording a Route

The bot needs real GW2 world coordinates to navigate. The old "auto-discovery" generated identical placeholder routes — those should be deleted.

**Delete old placeholder data:**
```bash
rm data/routes/route-*.json
rm data/telemetry/policy-signals.jsonl
rm data/models/policy-*.json
```

**Record your first real route:**

1. Load into GW2 on the map you want to farm
2. Open `http://localhost:8000` — verify **MumbleLink: Connected** in the Player Position card
3. Click **⏺ Start** in the Route Recording card
4. Mount (`X`), fly to each resource node, press `F` on each one
5. Watch the **Waypoints** counter — each `F` adds one
6. After completing the loop, click **💾 Save Route**
7. Restart the bot — it will now use your recorded route

---

## Operational Scenarios

### Scenario 1: Bot Running Alongside Manual Play

This is the recommended mode. The bot watches you play, learns from your inputs, and optionally takes over when you're not actively harvesting.

1. Start GW2, load into your farming map
2. Start the bot: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`
3. Open `http://localhost:8000`
4. The bot starts automatically and begins capturing your keypresses as training data
5. When you press any key, the **Manual Override** badge turns amber — bot input is suppressed for 3 s
6. The bot builds up training data from your harvests automatically

### Scenario 2: Fully Autonomous Run

After recording a route and accumulating some training data:

1. Make sure `GW2_RUNTIME_POLICY_ENABLED=true` and `GW2_RUNTIME_INPUT_ENABLED=true` in `.env`
2. Start the bot
3. It will navigate the recorded route, harvest nodes when the gather prompt is detected, and remount automatically
4. Monitor the Recent Actions log on the dashboard — look for `harvest` actions

### Scenario 3: Building Up Training Data

1. Enable demo capture: `GW2_DEMO_AUTO_CAPTURE_ENABLED=true` (default)
2. Play normally — every keypress is automatically saved as a policy signal
3. After a session, the policy auto-retrains every 5 minutes
4. Or trigger it manually: click **🎓 Train Now** on the dashboard

---

## Pause / Resume / Stop

Via dashboard buttons, or API:

```bash
curl -X POST http://127.0.0.1:8000/v1/run/pause
curl -X POST http://127.0.0.1:8000/v1/run/resume
curl -X POST http://127.0.0.1:8000/v1/run/stop
```

When paused, the bot stops sending input but continues capturing frames and telemetry.

---

## Route Management

List saved routes:
```bash
curl http://127.0.0.1:8000/v1/discovery/routes
```

Start with a specific route (skips auto-select):
```bash
curl -X POST http://127.0.0.1:8000/v1/run/start \
  -H "Content-Type: application/json" \
  -d '{"route_id":"route-abc12345"}'
```

Route recording API:
```bash
curl -X POST http://127.0.0.1:8000/v1/discovery/record/start
# ... press F on nodes in GW2 ...
curl -X POST http://127.0.0.1:8000/v1/discovery/record/stop   # saves
curl -X POST http://127.0.0.1:8000/v1/discovery/record/discard # throws away
curl http://127.0.0.1:8000/v1/discovery/record/status          # waypoint count
```

---

## Policy Training

Manual trigger:
```bash
curl -X POST http://127.0.0.1:8000/v1/training/policy/train
```

List versions:
```bash
curl http://127.0.0.1:8000/v1/training/policy/versions
```

Auto-retrain is enabled by default (every 5 min). To change the interval:
```
GW2_TRAINING_RETRAIN_INTERVAL_SECONDS=300
```

---

## MumbleLink / Position Tracking

The bot reads GW2's built-in MumbleLink shared memory for real player position, facing direction, and mount state. No addon or extra permissions required.

Check live position:
```bash
curl http://127.0.0.1:8000/v1/discovery/position
```

Example response:
```json
{
  "available": true,
  "avatar_x": -3421.5,
  "avatar_y": 512.0,
  "avatar_z": 8234.1,
  "continent_x": 11234.0,
  "continent_y": 29481.0,
  "map_id": 1206,
  "is_mounted": true,
  "mount_name": "Griffon",
  "tick": 4821934
}
```

If `available: false`, GW2 is not running or not yet loaded into a map.

---

## Troubleshooting

### Bot doesn't move
- Check `GW2_RUNTIME_INPUT_ENABLED=true` in `.env`
- Verify bridge enabled: `GET /health`
- Check if Manual Override is stuck active in dashboard (bot sees your keypresses)

### MumbleLink shows Offline
- GW2 must be running and loaded into a map (character selection screen gives tick=0)
- Check `GW2_MUMBLE_LINK_ENABLED=true` in `.env`
- Only one MumbleLink connection per process — if another tool uses it, reads may be stale

### Bot not learning from my keypresses
- Verify `GW2_DEMO_AUTO_CAPTURE_ENABLED=true` in `.env`
- Check `data/telemetry/policy-signals.jsonl` — it should grow while you play
- If file is empty: the `ManualInputListener` may have failed to start (check logs for `manual_input_listener_unavailable`)

### Route navigation feels wrong / bot circles
- Old placeholder routes (all identical `(100,100)→(220,220)`) need to be deleted
- Record a real route using the Route Recording workflow
- Delete old routes: `rm data/routes/route-*.json`

### Policy always says "navigate", never harvests
- Gather prompt detection may not be seeing the prompt — check `gather_prompt_visible` in Recent Actions log
- If using old training data (before 1 April 2026), clear and retrain:
  ```bash
  rm data/telemetry/policy-signals.jsonl
  rm data/models/policy-*.json
  ```
- The gather prompt detector (`interaction_prompt_detector.py`) looks for GW2's orange+dark gather UI in the lower-center screen region (60–78% vertically, 39–66% horizontally)

### Manual harvesting gets interrupted by bot
- Bot suppresses input for 3 s after each keypress (`GW2_RUNTIME_MANUAL_PAUSE_SECONDS=3.0`)
- Watch the **Manual Override** badge — it should turn amber when you're pressing keys
- If it's not turning amber: `ManualInputListener` may not be running (check logs)
- Increase suppression window if needed: `GW2_RUNTIME_MANUAL_PAUSE_SECONDS=5.0`

---

## Data Persistence

```
data/
  routes/
    route-*.json              # Recorded farming routes (real coords after 1 Apr 2026)
  telemetry/
    policy-signals.jsonl      # All policy signals (bot + manual demo)
    discovery-sessions.jsonl  # Discovery audit log (safe to keep)
  models/
    policy-latest.json        # Most recent trained policy
    policy-*.json             # Versioned policy artifacts
```

These are excluded from git (`.gitignore`).

---

## Environment Variables Quick Reference

```bash
# Movement
GW2_RUNTIME_SIGNAL_INTERVAL_MS=150        # Bot loop speed (ms)

# Suppression
GW2_RUNTIME_GATHER_LOCK_SECONDS=3.0       # Post-harvest movement lock
GW2_RUNTIME_GATHER_PROMPT_LATCH_SECONDS=3.0  # Sticky harvest intent
GW2_RUNTIME_MANUAL_PAUSE_SECONDS=3.0      # Manual input suppression window

# Position
GW2_MUMBLE_LINK_ENABLED=true              # Real GW2 position via shared memory

# Bot behaviour
GW2_RUNTIME_POLICY_ENABLED=true           # Use trained policy
GW2_RUNTIME_INPUT_ENABLED=true            # Send actual keyboard input
GW2_RUNTIME_MOUNT_CYCLE_ENABLED=true      # Auto-remount after harvest
GW2_RUNTIME_WAYPOINT_STEERING_ENABLED=true # Steer toward route waypoints
GW2_RUNTIME_POLICY_MIN_CONFIDENCE=0.7     # Policy confidence gate

# Training
GW2_TRAINING_AUTO_RETRAIN_ENABLED=true    # Background auto-retrain
GW2_TRAINING_RETRAIN_INTERVAL_SECONDS=300 # Retrain interval
GW2_DEMO_AUTO_CAPTURE_ENABLED=true        # Always capture manual keypresses

# Startup
GW2_AUTOSTART_RUN_ENABLED=true            # Auto-start on API launch
```

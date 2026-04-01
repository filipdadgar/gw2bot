# Quickstart: GW2 Farming Bot (Discovery-First)

**Latest**: Discovery-first MVP with auto route discovery, pause/resume control, and telemetry.

## Control Interfaces

The bot provides **two control interfaces**:

| Interface | Description | Use Case |
|-----------|-------------|----------|
| **Web Dashboard** | Browser-based UI at `http://localhost:8000` | Recommended for Windows users; doesn't steal focus from game |
| **Terminal/API** | REST API via `curl` commands | Headless/scripted control; programmatic integration |

Both interfaces work simultaneously and provide the same capabilities (start/pause/resume/stop, model info, real-time status).

---

## 1. Prerequisites

- Docker and Docker Compose
- Guild Wars 2 client running locally (not in container)
- Host bridge setup for frame capture and input automation

## 2. Build and Start (Common to Both Interfaces)

```bash
# Build image
docker build -t gw2bot:latest .

# Start with Docker Compose (handles bridge and volume setup)
docker-compose up -d

# Verify API is running
curl http://127.0.0.1:8000/v1/run/status
```

Response (idle state):
```json
{
  "cycle_id": null,
  "route_id": null,
  "status": "idle",
  "current_waypoint_index": 0,
  "started_at_utc": null,
  "last_error": null
}
```

## 3. Using the Web Dashboard (Recommended for Windows)

Open your browser and navigate to:

```
http://localhost:8000
```

Or from another machine:

```
http://<your-machine-ip>:8000
```

The dashboard displays:
- ✅ Real-time run status (running/paused/stopped)
- ✅ Start/Pause/Resume/Stop buttons
- ✅ Policy model info (latest ID, samples, training time)
- ✅ Bridge health status and frame resolution
- ✅ Recent actions log with timestamps
- ✅ Settings display

For more details, see [DASHBOARD.md](../../docs/DASHBOARD.md).

## 4. Using Terminal/API Commands (Alternative)

---

## 2A. Scenario Playbooks (Step-by-Step)

Use the playbook that matches your current stage.

### Scenario 1: First-Time Start (No Data Yet)

1. Start GW2 on the host and keep the game window visible.
2. Start the bot stack:

```bash
docker-compose up -d
```

3. Check current run state:

```bash
curl http://127.0.0.1:8000/v1/run/status
```

4. If status is not `running`, start a run (discovery-first):

```bash
curl -X POST http://127.0.0.1:8000/v1/run/start \
  -H "Content-Type: application/json" \
  -d '{"auto_discover_if_missing":true,"loop_enabled":true}'
```

5. Confirm route discovery happened:

```bash
curl http://127.0.0.1:8000/v1/routes
```

6. Check logs while first loop runs:

```bash
docker-compose logs -f
```

### Scenario 2: Data Has Been Gathered (Train/Validate Model State)

1. Trigger policy training from collected signals:

```bash
curl -X POST http://127.0.0.1:8000/v1/training/policy/train
```

2. Verify policy versions and latest model id:

```bash
curl http://127.0.0.1:8000/v1/training/policy/versions
```

3. Query one recommendation to sanity-check model serving:

```bash
curl -X POST http://127.0.0.1:8000/v1/training/policy/recommend \
  -H "Content-Type: application/json" \
  -d '{"state_features":{"distance":0.22,"confidence":0.91,"rarity":0.8}}'
```

4. Check active run state:

```bash
curl http://127.0.0.1:8000/v1/run/status
```

### Scenario 3: Auto Play by Bot (Mission Mode)

Mission defaults in `.env` already enable:
1. Run autostart
2. Runtime policy actions
3. Runtime input execution through host bridge
4. Continuous in-app retraining
5. Mount-cycle remount behavior and waypoint steering bias
6. Post-gather lock window to avoid movement interrupting harvest

Step-by-step:

1. Ensure Compose stack is running:

```bash
docker-compose up -d
```

2. Verify bot is running automatically:

```bash
curl http://127.0.0.1:8000/v1/run/status
```

Expected: `status` is `running` after startup stabilization.

3. Verify training artifacts exist and update over time:

```bash
curl http://127.0.0.1:8000/v1/training/policy/versions
```

4. Observe runtime behavior and retraining loop:

```bash
docker-compose logs -f
```

6. Validate in-game action execution is active by checking runtime policy signals:

```bash
tail -n 5 data/telemetry/policy-signals.jsonl
```

Expected: `state_features.bridge_enabled=1.0` and non-zero frame dimensions while the
active cycle progresses.

Optional validation for deterministic gathering:
- When close to a resource node and the in-game gather prompt is visible,
  `state_features.gather_prompt_visible` should appear as `1.0` in recent signals.
- For those steps, runtime action should resolve to `harvest`.

Optional validation for mount-cycle pathing behavior:
- During travel, `state_features.nav_direction_bias` should periodically show
  `-1`, `0`, or `1` based on route waypoint deltas.
- After gather actions, a subsequent navigate step should include
  `state_features.mount_action=remount` before travel continues.

Optional validation for gather lock behavior:
- After gather interactions, `state_features.gather_lock_remaining_ms` should be
  non-zero for a short window.
- While lock is active, movement input may be suppressed with
  `state_features.input_suppressed_reason=gather_lock`.

5. Operator control calls (if needed):

```bash
curl -X POST http://127.0.0.1:8000/v1/run/pause
curl -X POST http://127.0.0.1:8000/v1/run/resume
curl -X POST http://127.0.0.1:8000/v1/run/stop
```

Note: If host capture/input is unavailable, mission mode still runs with fallback signal generation, but full real-game automation quality depends on host bridge health.

## 3. Start Farming (Discovery-First)

The bot auto-discovers a viable route on first run:

```bash
curl -X POST http://127.0.0.1:8000/v1/run/start \
  -H "Content-Type: application/json" \
  -d '{"auto_discover_if_missing":true,"loop_enabled":true}'
```

Response (202 Accepted):
```json
{
  "cycle_id": "cycle-abc123",
  "route_id": "route-xyz789",
  "status": "running",
  "current_waypoint_index": 0,
  "started_at_utc": "2026-03-31T10:30:00+00:00",
  "last_error": null
}
```

## 4. Monitor Status

```bash
curl http://127.0.0.1:8000/v1/run/status
```

Current waypoint, cycle progress, and any errors are shown.

## 5. Control Operations

### Pause
```bash
curl -X POST http://127.0.0.1:8000/v1/run/pause
# Status transitions to "paused" without resetting state
```

### Resume
```bash
curl -X POST http://127.0.0.1:8000/v1/run/resume
# Status returns to "running" from paused position
```

### Stop
```bash
curl -X POST http://127.0.0.1:8000/v1/run/stop
# Status transitions to "stopping" then "idle"; writes final telemetry
```

## 6. Retrieve Telemetry

After cycle completion, view detailed summary:

```bash
curl http://127.0.0.1:8000/v1/telemetry/cycles/cycle-abc123/summary
```

Response includes waypoint completion rate, harvest success rate, and failures.

## 7. Validate Success Criteria

All acceptance criteria must pass before release:

```bash
# Run full test suite
pytest tests/ -v

# Run performance benchmarks
pytest tests/integration/test_capture_decision_latency.py -v
pytest tests/integration/test_discovery_success_rate.py -v
pytest tests/integration/test_harvest_success_rate.py -v
pytest tests/integration/test_waypoint_completion_rate.py -v
pytest tests/integration/test_cooldown_restart_latency.py -v
pytest tests/integration/test_host_bridge_soak.py -v
```

## 8. Reuse Discovered Routes

List available routes:
```bash
curl http://127.0.0.1:8000/v1/routes
```

Start with a specific route (skip discovery):
```bash
curl -X POST http://127.0.0.1:8000/v1/run/start \
  -H "Content-Type: application/json" \
  -d '{"route_id":"route-xyz789"}'
```

## 9. Optional Features

### Enable Minimap Detection
```bash
export GW2_MINIMAP_DETECTION_ENABLED=true
docker-compose restart
```

### Enable Dynamic Prioritization
```bash
export GW2_DYNAMIC_PRIORITIZATION_ENABLED=true
export GW2_PRIORITIZATION_DISTANCE_WEIGHT=0.3
export GW2_PRIORITIZATION_CONFIDENCE_WEIGHT=0.4
export GW2_PRIORITIZATION_RARITY_WEIGHT=0.3
docker-compose restart
```

## 10. Troubleshooting

See [Operator Runbook](../docs/operations/gw2bot-runbook.md) for detailed troubleshooting.

**Quick checks**:
- API responsive: `curl http://127.0.0.1:8000/v1/run/status`
- Containers running: `docker-compose ps`
- Logs: `docker-compose logs -f`

## 11. Train and Query Policy

After at least one cycle, train a policy artifact from emitted policy signals:

```bash
curl -X POST http://127.0.0.1:8000/v1/training/policy/train
```

Example response:
```json
{
  "model_id": "policy-4f29df7f",
  "sample_count": 240,
  "action_count": 3,
  "default_action": "navigate",
  "artifact_path": "data/models/policy-latest.json",
  "trained_at_utc": "2026-03-31T11:20:00+00:00"
}
```

Query recommendation from the latest trained policy:

```bash
curl -X POST http://127.0.0.1:8000/v1/training/policy/recommend \
  -H "Content-Type: application/json" \
  -d '{"state_features":{"distance":0.22,"confidence":0.91,"rarity":0.8}}'
```

Example response:
```json
{
  "action": "harvest",
  "confidence": 0.76,
  "model_id": "policy-4f29df7f"
}
```

List trained model versions:

```bash
curl http://127.0.0.1:8000/v1/training/policy/versions
```

Run scheduled retraining as a command:

```bash
gw2bot-retrain-scheduler --data-dir data --interval-seconds 1800
```

Run one-shot retrain and exit:

```bash
gw2bot-retrain-scheduler --data-dir data --once
```

Enable in-app automatic retraining in the API process:

```bash
export GW2_TRAINING_AUTO_RETRAIN_ENABLED=true
export GW2_TRAINING_RETRAIN_INTERVAL_SECONDS=1800
docker-compose restart
```

Enable policy-guided runtime actions from trained artifacts:

```bash
export GW2_RUNTIME_POLICY_ENABLED=true
export GW2_RUNTIME_POLICY_MIN_CONFIDENCE=0.7
export GW2_RUNTIME_SIGNAL_INTERVAL_MS=500
docker-compose restart
```


## Mission Mode (Zero-Touch)

With mission defaults in `.env` on a supported host bridge setup (including Windows),
`docker-compose up -d` will:

1. Auto-start a run
2. Continuously emit policy signals while running
3. Retrain policy artifacts on a repeating interval
4. Apply learned policy actions at runtime (confidence-gated)

Record manual demonstration steps and train on them:

```bash
# Start demo session
curl -X POST http://127.0.0.1:8000/v1/training/demonstrations/start

# Record one action (repeat while you play)
curl -X POST http://127.0.0.1:8000/v1/training/demonstrations/record \
  -H "Content-Type: application/json" \
  -d '{"action_taken":"harvest","reward_proxy":1.0,"terminal":false}'

# Stop demo session
curl -X POST http://127.0.0.1:8000/v1/training/demonstrations/stop

# Train new policy including demonstrations
curl -X POST http://127.0.0.1:8000/v1/training/policy/train
```

Enable automatic host input capture for demonstration sessions:

```bash
export GW2_DEMO_AUTO_CAPTURE_ENABLED=true
docker-compose restart
```

## 12. Next Steps

- Review [Operator Runbook](../docs/operations/gw2bot-runbook.md) for production operations
- Explore [Data Model](data-model.md) for full schema reference
- Check [Research Document](research.md) for architectural decisions

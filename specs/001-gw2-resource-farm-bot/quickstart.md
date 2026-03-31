# Quickstart: GW2 Farming Bot (Discovery-First)

**Latest**: Discovery-first MVP with auto route discovery, pause/resume control, and telemetry.

## 1. Prerequisites

- Docker and Docker Compose
- Guild Wars 2 client running locally (not in container)
- Host bridge setup for frame capture and input automation

## 2. Build and Start

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

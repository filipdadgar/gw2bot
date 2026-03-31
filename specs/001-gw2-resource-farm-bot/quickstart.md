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

## 11. Next Steps

- Review [Operator Runbook](../docs/operations/gw2bot-runbook.md) for production operations
- Explore [Data Model](data-model.md) for full schema reference
- Check [Research Document](research.md) for architectural decisions

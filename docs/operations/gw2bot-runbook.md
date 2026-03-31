# GW2 Bot Operator Runbook: Discovery-First Docker Workflow

## Overview

This runbook covers operating the GW2 Resource Farming Bot in production using the discovery-first architecture under Docker.

## Prerequisites

- Docker and Docker Compose installed
- Local Guild Wars 2 game client running on the same machine
- Python 3.11+ (for host bridge setup)

## Quick Start

### 1. Build and Start Containers

```bash
docker-compose -f docker-compose.yml up -d
```

This starts:
- **gw2bot-api**: FastAPI control service on port 8000
- **gw2bot-bridge**: Host bridge service for frame capture and input automation

Verify containers are running:

```bash
docker-compose ps
```

### 2. Verify Host Bridge Connection

```bash
curl http://127.0.0.1:8000/v1/run/status
```

Expected response (idle state):

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

## Operational Workflows

### Workflow: Start Discovery and Farming Loop

Discovery-first means the bot finds a viable route automatically on first run.

```bash
# Start farming (will auto-discover if no route exists)
curl -X POST http://127.0.0.1:8000/v1/run/start \
  -H "Content-Type: application/json" \
  -d '{"auto_discover_if_missing": true}'
```

Expected response (202 Accepted):

```json
{
  "cycle_id": "cycle-abc12345",
  "route_id": "route-xyz78901",
  "status": "running",
  "current_waypoint_index": 0,
  "started_at_utc": "2026-03-31T10:30:00+00:00",
  "last_error": null
}
```

### Workflow: Monitor Active Run

Check current farming status:

```bash
curl http://127.0.0.1:8000/v1/run/status
```

### Workflow: Pause Farming

Temporarily halt without resetting state:

```bash
curl -X POST http://127.0.0.1:8000/v1/run/pause
```

Resume when ready:

```bash
curl -X POST http://127.0.0.1:8000/v1/run/resume
```

### Workflow: Stop and Exit

Stop current farming run safely:

```bash
curl -X POST http://127.0.0.1:8000/v1/run/stop
```

### Workflow: View Cycle Telemetry

Retrieve summary after cycle completion:

```bash
curl http://127.0.0.1:8000/v1/telemetry/cycles/{cycleId}/summary
```

## Troubleshooting

### Issue: Container fails to start

**Symptoms**: `docker-compose up` exits with error

**Check**:
- Verify Docker daemon is running: `docker ps`
- Review logs: `docker-compose logs gw2bot-api`
- Ensure no port conflicts on 8000

### Issue: Host bridge disconnects

**Symptoms**: API returns 500 errors; `last_error: "bridge_unavailable"`

**Recovery**:
- The bot will attempt reconnect within 3 seconds
- Monitor via `curl http://127.0.0.1:8000/v1/run/status`
- Restart containers if persistent: `docker-compose restart`

### Issue: Discovery fails (status: "failed")

**Symptoms**: Run start returns error status

**Workaround**:
- Retry start: the discovery engine may need multiple attempts
- Verify game window is active and visible on host
- Check game is not in loading screen or dialog

### Issue: Performance is slow (latency > 900ms)

**Causes**:
- High CPU usage on host machine
- Network interference or Docker resource constraints
- Game rendering at very high resolution

**Mitigation**:
- Reduce Docker resource contention: stop other containers
- Lower game resolution or graphics settings
- Monitor latency benchmark via test suite

## Performance Expectations

### Acceptance Criteria

- **Discovery**: New routes discovered ≥90% of attempts, within 10 minutes
- **Waypoint Completion**: ≥95% of planned waypoints reached per cycle
- **Harvest Success**: ≥85% of detected nodes harvested per cycle
- **Latency**: Capture-to-decision ≤500ms median, ≤900ms p95
- **Cooldown Restart**: ≤5 seconds in ≥95% of cycles
- **Bridge Resilience**: No unrecoverable failures in 2-hour soak test

## Data Persistence

### Route Storage

Discovered routes are stored in Docker volume `gw2bot_data`:

```
data/routes/
  ├── route-abc12345.json
  ├── route-def67890.json
  └── ...
```

Inspect stored routes (from container):

```bash
docker exec gw2bot-api ls -la /app/data/routes/
```

### Telemetry and Logs

Event logs and cycle summaries stored in:

```
data/telemetry/
  ├── discovery-sessions.jsonl
  ├── event-log-*.jsonl
  └── cycle-summaries*.jsonl
```

## Monitoring and Metrics

Real-time metrics available from API:

- `GET /v1/run/status` — current cycle state
- `GET /v1/telemetry/cycles/{cycleId}/summary` — completed cycle stats

Telemetry stored in JSONL format for post-session analysis.

## Advanced Configuration

Override environment variables via `.env`:

```
GW2_CAPTURE_SOURCE=host
GW2_INPUT_SOURCE=host
GW2_MINIMAP_DETECTION_ENABLED=true
GW2_DYNAMIC_PRIORITIZATION_ENABLED=true
GW2_DATA_DIR=/app/data
GW2_API_HOST=0.0.0.0
GW2_API_PORT=8000
```

Restart containers to apply changes:

```bash
docker-compose restart
```

## Getting Help

For issues or questions:

1. Check logs: `docker-compose logs -f`
2. Review spec and research documents: `specs/001-gw2-resource-farm-bot/`
3. Run test suite to validate setup: `pytest tests/ -v`

# Implementation Plan: Modular GW2 Resource Farming Bot

**Branch**: `main` | **Date**: 2026-03-30 | **Spec**: `/specs/001-gw2-resource-farm-bot/spec.md`
**Input**: Feature specification from `/specs/001-gw2-resource-farm-bot/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a modular Python bot that automates Guild Wars 2 resource farming through
screen capture, node detection, dynamic route discovery, action automation, and
cooldown loop execution. Run the bot runtime inside Docker for dependency
isolation while interacting with the local game client on the same host through
approved host capture/input bridges. Use a layered architecture with separate
runtime modules for perception, planning, control, and telemetry, expose runtime
control through a FastAPI service, and include offline policy training plus
inference serving using stable state/action/reward signal contracts.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: OpenCV, Ultralytics YOLOv8, NumPy, PyAutoGUI or pynput, FastAPI
**Storage**: Docker-mounted local files for discovered route graphs, structured telemetry logs, and trained policy artifacts; optional Redis for runtime state caching
**Testing**: pytest, pytest-mock, contract checks for FastAPI OpenAPI schema, integration simulations for loop control
**Target Platform**: Docker container on macOS host with Guild Wars 2 client in host foreground window
**Project Type**: single-project containerized automation service (runtime engine + control API)
**Performance Goals**: median capture-to-decision <= 500 ms; p95 <= 900 ms; route loop restart latency <= 5 s after cooldown; route discovery success >= 90% within 10 minutes
**Constraints**: deterministic safety stop on operator command <= 250 ms; no uncontrolled input spam; resilient to intermittent detection misses; host-bridge disconnect recovery <= 3 s
**Scale/Scope**: one active game client per runtime instance; routes discovered in-session and persisted incrementally; sessions up to 8 hours continuous operation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Code Quality Gate**: PASS
  - Enforce `ruff check`, `ruff format --check`, and `mypy` on modified modules.
  - Keep strict module boundaries: `capture`, `detection`, `navigation`, `actions`, `orchestration`, `telemetry`, `api`.
  - Require PR review confirmation for boundary adherence and duplication control.
- **Testing Gate**: PASS
  - Unit coverage: frame preprocessing, detection post-processing, route discovery scoring, route state transitions, cooldown scheduler, telemetry serialization.
  - Integration coverage: end-to-end farm loop with mocked host-bridge frame/input adapters; pause/resume/stop behavior.
  - Regression policy: each bug fix includes a reproducing failing test first.
- **UX Consistency Gate**: PASS
  - Runtime control states standardized to `idle`, `running`, `paused`, `stopping`, `error` across API and logs.
  - Error payloads and operator messages use consistent reason codes and remediation hints.
- **Performance Gate**: PASS
  - Capture-to-decision and loop throughput budgets defined in Technical Context and spec success criteria.
  - Validation via benchmark harness and Docker host-bridge soak test before release.

### Post-Design Constitution Re-Check

- **Code Quality Gate**: PASS (data model and contracts enforce modular boundaries)
- **Testing Gate**: PASS (quickstart and plan define mandatory unit/integration/regression suites)
- **UX Consistency Gate**: PASS (control API contract defines canonical status and error schema)
- **Performance Gate**: PASS (research decisions include model fallback path, route discovery fallback, and telemetry for latency auditing)

## Project Structure

### Documentation (this feature)

```text
specs/001-gw2-resource-farm-bot/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
src/
├── api/
├── core/
│   ├── capture/
│   ├── detection/
│   ├── discovery/
│   ├── navigation/
│   ├── actions/
│   ├── orchestration/
│   └── training/
├── telemetry/
├── config/
└── adapters/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Use a single-project Python architecture with clear
domain module separation and a local control API layer. This matches current
scope (single runtime instance) while keeping extension points for future RL
policy modules under `src/core/orchestration` and `src/adapters`. Docker
artifacts (`Dockerfile`, `docker-compose.yml`) will define isolated runtime and
host access bindings for capture/input channels.

## Control Interfaces

The system provides **two complementary control interfaces** built on the same FastAPI backend:

1. **Web Dashboard (UI)**
   - Browser-based interface at `http://localhost:8000` or network accessible
   - Real-time status display updating every 2 seconds
   - Supports run lifecycle (start/pause/resume/stop)
   - Shows policy model info, bridge health, recent actions
   - **Advantage**: No focus stealing from game window; intuitive UI; network access
   - **Use case**: Recommended for Windows operators managing the bot during gameplay

2. **REST API (Terminal/Programmatic)**
   - JSON REST endpoints for all operations
   - `curl` command examples provided in quickstart
   - OpenAPI schema available for integration
   - **Advantage**: Scriptable, headless operation, system integration
   - **Use case**: Headless servers, automated testing, programmatic automation

Both interfaces operate simultaneously on the same backend and share all state/status/control semantics.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations identified.


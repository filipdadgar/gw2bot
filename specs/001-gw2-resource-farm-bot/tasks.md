# Tasks: Modular GW2 Resource Farming Bot

**Input**: Design documents from `/specs/001-gw2-resource-farm-bot/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/control-api.openapi.yaml, quickstart.md

**Tests**: Test tasks are REQUIRED. Every user story includes unit, integration, and contract validation.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and containerized runtime baseline

- [X] T001 Create Python package skeleton in src/__init__.py
- [X] T002 Initialize project dependencies and tooling in pyproject.toml
- [X] T003 [P] Add container image build definition in Dockerfile
- [X] T004 [P] Add local orchestration and host bridge mapping in docker-compose.yml
- [X] T005 [P] Configure linting and formatting defaults in .ruff.toml
- [X] T006 [P] Define runtime environment variables in .env.example

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core runtime architecture required before user stories

**CRITICAL**: No user story implementation starts until this phase is complete

- [X] T007 Define global runtime configuration schema in src/config/settings.py
- [X] T008 [P] Implement shared logging bootstrap in src/telemetry/logger.py
- [X] T009 [P] Define orchestration state enums and shared types in src/core/orchestration/state_types.py
- [X] T010 [P] Define host bridge capture/input interfaces in src/adapters/bridge_interfaces.py
- [X] T011 Implement persistence primitives for routes and telemetry in src/core/persistence/storage.py
- [X] T012 [P] Initialize FastAPI application factory in src/api/main.py
- [X] T013 Implement base farm state-machine shell in src/core/orchestration/farm_state_machine.py

**Checkpoint**: Foundation complete, story work can begin

---

## Phase 3: User Story 1 - Discover and Run Automated Farm Loop (Priority: P1) MVP

**Goal**: Discover a viable route loop from an empty inventory and execute autonomous farm cycles with cooldown restarts

**Independent Test**: Start from no stored routes, complete discovery, persist route, execute one full cycle and automatic restart

### Tests for User Story 1 (REQUIRED)

- [X] T014 [P] [US1] Add contract tests for discovery endpoints in tests/contract/test_discovery_api.py
- [X] T015 [P] [US1] Add contract tests for run start/status endpoints in tests/contract/test_run_start_status_api.py
- [X] T016 [P] [US1] Add integration test for discovery-to-farm loop execution in tests/integration/test_discover_and_run_cycle.py
- [X] T017 [P] [US1] Add unit tests for discovery loop-confidence scoring in tests/unit/test_route_discovery_scoring.py
- [X] T018 [P] [US1] Add unit tests for policy signal emission rules in tests/unit/test_policy_signal_emission.py

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement host-bridge frame capture service in src/core/capture/frame_capture_service.py
- [X] T020 [P] [US1] Implement YOLO-based node detector service in src/core/detection/node_detector.py
- [X] T021 [P] [US1] Implement route discovery models in src/core/discovery/discovery_models.py
- [X] T022 [P] [US1] Implement route graph builder and persistence adapter in src/core/discovery/route_builder.py
- [X] T023 [P] [US1] Implement waypoint navigator for discovered routes in src/core/navigation/waypoint_navigator.py
- [X] T024 [P] [US1] Implement harvest action executor with retry policy in src/core/actions/harvest_executor.py
- [X] T025 [US1] Implement discovery orchestration transitions in src/core/orchestration/discovery_orchestrator.py
- [X] T026 [US1] Implement farm cycle orchestration with cooldown loop in src/core/orchestration/farm_cycle_orchestrator.py
- [X] T027 [US1] Implement policy signal emitter in src/core/orchestration/policy_signal_emitter.py
- [X] T028 [US1] Implement policy signal persistence store in src/core/persistence/policy_signal_store.py
- [X] T029 [US1] Add discovery start/status/stop routes in src/api/routes/discovery.py
- [X] T030 [US1] Add run start/status routes with auto-discover fallback in src/api/routes/run.py

**Checkpoint**: US1 is independently functional and testable

---

## Phase 4: User Story 2 - Monitor and Control Runs (Priority: P2)

**Goal**: Provide safe runtime controls and telemetry visibility for active cycles

**Independent Test**: Run a cycle, validate pause/resume/stop semantics and complete telemetry summaries

### Tests for User Story 2 (REQUIRED)

- [X] T031 [P] [US2] Add contract tests for pause/resume/stop endpoints in tests/contract/test_run_control_api.py
- [X] T032 [P] [US2] Add contract tests for cycle telemetry summary endpoint in tests/contract/test_cycle_summary_api.py
- [X] T033 [P] [US2] Add integration test for pause/resume lifecycle flow in tests/integration/test_pause_resume_lifecycle.py
- [X] T034 [P] [US2] Add integration test for stop safety latency in tests/integration/test_stop_safety_timing.py
- [X] T035 [P] [US2] Add unit tests for cycle summary aggregation in tests/unit/test_cycle_summary_aggregation.py

### Implementation for User Story 2

- [X] T036 [P] [US2] Implement telemetry event writer with rotation in src/telemetry/event_writer.py
- [X] T037 [P] [US2] Implement telemetry cycle summary service in src/telemetry/cycle_summary_service.py
- [X] T038 [US2] Implement pause/resume/stop command handlers in src/core/orchestration/control_commands.py
- [X] T039 [US2] Add run control API routes in src/api/routes/run_control.py
- [X] T040 [US2] Add telemetry summary API route in src/api/routes/telemetry.py

**Checkpoint**: US2 is independently functional and testable

---

## Phase 5: User Story 3 - Extend Detection and Prioritization (Priority: P3)

**Goal**: Add optional minimap-assisted detection and dynamic prioritization policies

**Independent Test**: Enable optional features and verify candidate selection order changes according to policy

### Tests for User Story 3 (REQUIRED)

- [X] T041 [P] [US3] Add unit tests for minimap candidate extraction in tests/unit/test_minimap_candidate_extractor.py
- [X] T042 [P] [US3] Add unit tests for prioritization policy scoring in tests/unit/test_priority_policy_scoring.py
- [X] T043 [P] [US3] Add integration test for minimap-assisted targeting in tests/integration/test_minimap_targeting_flow.py
- [X] T044 [P] [US3] Add integration test for dynamic prioritization behavior in tests/integration/test_dynamic_prioritization_flow.py

### Implementation for User Story 3

- [X] T045 [P] [US3] Implement minimap signal extractor in src/core/detection/minimap_extractor.py
- [X] T046 [P] [US3] Implement detection candidate fusion pipeline in src/core/detection/candidate_fusion.py
- [X] T047 [P] [US3] Implement pluggable prioritization policy engine in src/core/navigation/prioritization_policy.py
- [X] T048 [US3] Integrate prioritization into target selector in src/core/orchestration/target_selector.py
- [X] T049 [US3] Add runtime feature toggles for optional enhancements in src/config/feature_flags.py

**Checkpoint**: US3 optional features are independently functional and testable

---

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Final hardening, UX validation, performance benchmarking, and release readiness

- [X] T050 [P] Add host-bridge resilience soak test in tests/integration/test_host_bridge_soak.py
- [X] T051 [P] Add capture-to-decision latency benchmark in tests/integration/test_capture_decision_latency.py
- [X] T052 [P] Add discovery success-rate benchmark in tests/integration/test_discovery_success_rate.py
- [X] T053 [P] Add waypoint completion-rate benchmark in tests/integration/test_waypoint_completion_rate.py
- [X] T054 [P] Add harvest success-rate benchmark in tests/integration/test_harvest_success_rate.py
- [X] T055 [P] Add cooldown restart-latency benchmark in tests/integration/test_cooldown_restart_latency.py
- [X] T056 [P] Add regression test for discovery fallback behavior in tests/integration/test_discovery_failure_fallback.py
- [X] T057 [P] Add UX consistency validation for statuses and error payloads in tests/integration/test_operator_ux_consistency.py
- [X] T058 Update operator runbook for discovery-first Docker workflow in docs/operations/gw2bot-runbook.md
- [X] T059 Align quickstart examples with final API behavior in specs/001-gw2-resource-farm-bot/quickstart.md
- [X] T060 Run full quality gates and publish validation summary in specs/001-gw2-resource-farm-bot/validation-report.md

---

## Phase 7: User Story 4 - Train and Serve Learned Policy (Priority: P2)

**Goal**: Train a persisted policy artifact from collected signals and expose runtime recommendation.

**Independent Test**: Collect policy signals, train model artifact, and request recommendations from API.

### Tests for User Story 4 (REQUIRED)

- [X] T061 [P] [US4] Add contract tests for training endpoints in tests/contract/test_training_api.py
- [X] T062 [P] [US4] Add integration test for end-to-end training workflow in tests/integration/test_policy_training_workflow.py
- [X] T063 [P] [US4] Add unit tests for policy signal dataset parsing in tests/unit/test_policy_signal_dataset.py
- [X] T064 [P] [US4] Add unit tests for policy trainer aggregation and inference in tests/unit/test_policy_trainer.py

### Implementation for User Story 4

- [X] T065 [P] [US4] Implement policy signal dataset loader in src/core/training/policy_signal_dataset.py
- [X] T066 [P] [US4] Implement policy artifact trainer and serializer in src/core/training/policy_trainer.py
- [X] T067 [P] [US4] Implement policy model registry for latest artifact loading in src/core/training/policy_registry.py
- [X] T068 [US4] Integrate policy signal emission and persistence into run loop in src/core/orchestration/farm_cycle_orchestrator.py
- [X] T069 [US4] Add training API routes for train and recommend in src/api/routes/training.py
- [X] T070 [US4] Wire training services into app factory in src/api/main.py
- [X] T071 [US4] Update quickstart and README with training workflow usage
- [X] T072 [US4] Update validation report for completed training phase
- [X] T073 [US4] Add policy version history endpoint and registry support
- [X] T074 [US4] Add scheduled retraining command entry point
- [X] T075 [US4] Add manual demonstration capture APIs and persistence wiring
- [X] T076 [US4] Add contract tests for demonstration recording workflow
- [X] T077 [US4] Add mission-mode autostart defaults for continuous training and finetuning on Docker hosts
- [X] T078 [US4] Wire runtime action execution from policy-selected actions to host input bridge in src/core/orchestration/farm_cycle_orchestrator.py
- [X] T079 [US4] Add runtime input execution configuration and endpoint wiring in src/config/settings.py, src/api/main.py, and src/api/routes/run.py
- [X] T080 [US4] Add unit tests for runtime action execution behavior in tests/unit/test_runtime_action_execution.py
- [X] T081 [US4] Update Windows native setup and operator docs for runtime input validation flow in docs/operations/WINDOWS_NATIVE_SETUP.md and docs/operations/gw2bot-runbook.md
- [X] T082 [US4] Update spec quickstart and validation artifacts for runtime input execution readiness

---

## Phase 6: Polish (Web Dashboard Interface)

**Goal**: Provide web-based dashboard for bot control without focus stealing from game client

**Independent Test**: Dashboard accessible via HTTP, displays real-time status, supports run controls, updates without focus loss

### Tests for Web Dashboard

- [X] T083 [P] Add contract tests for dashboard telemetry endpoints in tests/contract/test_dashboard_api.py

### Implementation for Web Dashboard

- [X] T084 [P] Implement dashboard HTML/CSS/JS UI with real-time updates in src/api/static/dashboard.html
- [X] T085 [P] Implement dashboard telemetry API endpoint in src/api/routes/dashboard.py
- [X] T086 Wire dashboard routes into API factory and serve at / and /dashboard endpoints in src/api/main.py
- [X] T087 Add dashboard documentation and update quickstart with web UI option in docs/DASHBOARD.md and specs/001-gw2-resource-farm-bot/quickstart.md

---

## Dependencies and Execution Order

### Phase Dependencies

- Setup (Phase 1): no dependencies
- Foundational (Phase 2): depends on Setup and blocks all user stories
- User Story phases (Phase 3 to Phase 5): depend on Foundational
- Polish (Phase 6): depends on completion of selected user stories

### User Story Dependencies

- US1 (P1): starts after Foundational and provides MVP
- US2 (P2): starts after Foundational and relies on US1 lifecycle semantics
- US3 (P3): starts after Foundational and relies on shared detection/navigation stack

### Within Each User Story

- Tests are written first and verified failing before implementation
- Core components are implemented before orchestration and API wiring
- Story validation completes before advancing priority

---

## Parallel Execution Examples

### User Story 1

```bash
Task: "Add contract tests for discovery endpoints in tests/contract/test_discovery_api.py"
Task: "Add contract tests for run start/status endpoints in tests/contract/test_run_start_status_api.py"
Task: "Add integration test for discovery-to-farm loop execution in tests/integration/test_discover_and_run_cycle.py"
Task: "Add unit tests for discovery loop-confidence scoring in tests/unit/test_route_discovery_scoring.py"
Task: "Implement host-bridge frame capture service in src/core/capture/frame_capture_service.py"
Task: "Implement YOLO-based node detector service in src/core/detection/node_detector.py"
Task: "Implement route discovery models in src/core/discovery/discovery_models.py"
Task: "Implement waypoint navigator for discovered routes in src/core/navigation/waypoint_navigator.py"
```

### User Story 2

```bash
Task: "Implement telemetry event writer with rotation in src/telemetry/event_writer.py"
Task: "Implement telemetry cycle summary service in src/telemetry/cycle_summary_service.py"
Task: "Add integration test for pause/resume lifecycle flow in tests/integration/test_pause_resume_lifecycle.py"
Task: "Add integration test for stop safety latency in tests/integration/test_stop_safety_timing.py"
```

### User Story 3

```bash
Task: "Implement minimap signal extractor in src/core/detection/minimap_extractor.py"
Task: "Implement detection candidate fusion pipeline in src/core/detection/candidate_fusion.py"
Task: "Implement pluggable prioritization policy engine in src/core/navigation/prioritization_policy.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational phases
2. Deliver US1 discovery-first autonomous loop
3. Validate US1 independently before adding additional stories

### Incremental Delivery

1. Ship US1 (core autonomous farming)
2. Ship US2 (control and observability)
3. Ship US3 (optional efficiency enhancements)
4. Complete polish benchmarks and quality gates

### Parallel Team Strategy

1. Team completes Setup and Foundational phases together
2. Developer A drives US1 orchestration and API endpoints
3. Developer B drives US2 telemetry and control APIs
4. Developer C drives US3 detection and prioritization enhancements

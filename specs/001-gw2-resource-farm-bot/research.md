# Phase 0 Research: Modular GW2 Resource Farming Bot

## Decision 1: Primary vision pipeline uses YOLOv8 with OpenCV preprocessing
- Decision: Use OpenCV for frame capture preprocessing and Ultralytics YOLOv8 for node detection.
- Rationale: YOLOv8 provides practical inference speed and robust ecosystem support, while OpenCV enables deterministic preprocessing and coordinate normalization.
- Alternatives considered:
  - Pure OpenCV template matching only: rejected due to fragility under varying lighting/occlusion.
  - Classical feature matching (SIFT/ORB): rejected as less reliable for heterogeneous node visuals.

## Decision 2: Discovery-first route-state machine for navigation and harvesting
- Decision: Implement an explicit finite-state loop with discovery phase: discover_path -> validate_loop -> acquire_frame -> detect_nodes -> select_target -> navigate -> harvest -> evaluate_cooldown -> next_waypoint.
- Rationale: A discovery-first state machine supports empty initial route inventories and preserves deterministic control transitions for pause/resume/stop.
- Alternatives considered:
  - Behavior tree first: rejected for MVP complexity overhead.
  - Fully learned navigation policy now: rejected because RL is future phase and lacks stable baseline data yet.

## Decision 3: Host-bridge input automation adapters over PyAutoGUI/pynput
- Decision: Define an input adapter interface and provide concrete adapters for PyAutoGUI and pynput behind a host-bridge boundary used by Docker runtime.
- Rationale: Adapter abstraction decouples orchestration logic from host access implementation and supports Docker isolation without changing core logic.
- Alternatives considered:
  - Hardcode one library globally: rejected due to lower portability and harder future migration.
  - Direct OS APIs now: rejected for increased platform-specific complexity in MVP.

## Decision 4: FastAPI control plane for runtime control and telemetry access
- Decision: Use FastAPI for local control endpoints (start/pause/resume/stop/status/config update) and telemetry summaries.
- Rationale: FastAPI provides clear contracts, request validation, and easy OpenAPI generation for contract testing.
- Alternatives considered:
  - CLI-only control: rejected due to weaker runtime observability and external tool integration.
  - WebSocket-only control: rejected for unnecessary complexity in MVP.

## Decision 5: Local structured telemetry first, optional Redis cache
- Decision: Persist JSONL telemetry locally for auditability; optionally cache hot runtime state in Redis.
- Rationale: Local files are simple and reliable for single-instance runs, while Redis stays optional for low-latency status reads and future scaling.
- Alternatives considered:
  - Redis mandatory: rejected due to operational overhead for MVP.
  - No persistent telemetry: rejected because it breaks diagnostics and post-run analysis requirements.

## Decision 6: RL-readiness via normalized policy signal schema
- Decision: Emit normalized policy signals (state vector metadata, action chosen, reward proxy, terminal flag) during each loop step.
- Rationale: Collecting stable offline trajectories now lowers integration risk for later Gymnasium and Stable-Baselines3 phases.
- Alternatives considered:
  - Add RL integration immediately: rejected due to scope expansion and uncertain reward design.
  - Ignore RL interfaces now: rejected because later retrofitting would force breaking internal contracts.

## Decision 7: Performance strategy includes detection confidence threshold and fallback mode
- Decision: Enforce configurable confidence thresholds and fallback to route progression when detections fail beyond retry budget.
- Rationale: Balances harvest success with run continuity, preserving cycle throughput under noisy perception conditions.
- Alternatives considered:
  - Block until confident detection: rejected due to route stalls and throughput degradation.
  - Always proceed without retries: rejected due to avoidable missed harvests.

## Decision 8: Testing strategy prioritizes deterministic simulation harnesses
- Decision: Build deterministic test fixtures for frame sequences and mock input/game-state adapters to test loops without live game dependency.
- Rationale: Enables repeatable CI validation for safety and orchestration logic.
- Alternatives considered:
  - Live-client-only testing: rejected due to flakiness and automation constraints.
  - Unit tests only: rejected because loop orchestration requires integration-level validation.

## Decision 9: Docker-first runtime deployment with host access bridge
- Decision: Package runtime in Docker and expose host frame capture/input channels through explicit bridge adapters and container runtime configuration.
- Rationale: Docker improves reproducibility and dependency isolation while preserving same-machine game interaction.
- Alternatives considered:
  - Native host-only execution: rejected due to environment drift risk.
  - VM-based isolation: rejected due to latency overhead and host interaction complexity.

## Decision 10: Route discovery and persistence strategy
- Decision: Build route discovery by tracking movement segments, node encounters, and loop closure confidence; persist successful loops as reusable route graphs.
- Rationale: Removes dependency on manually predefined routes and supports adaptive farming in unfamiliar maps.
- Alternatives considered:
  - Require manual route files: rejected by feature requirement.
  - Pure random walk each cycle: rejected due to unstable throughput and inconsistent cooldown loops.

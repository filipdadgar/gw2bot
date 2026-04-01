# Feature Specification: Modular GW2 Resource Farming Bot

**Branch**: `main`  
**Created**: 2026-03-30  
**Status**: Draft  
**Input**: User description: "Build a modular bot that can automatically farm resource nodes in Guild Wars 2 using screen-based detection, route navigation, and input automation. The system should be extensible to support reinforcement learning in later phases."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Discover and Run Automated Farm Loop (Priority: P1)

As an operator, I can start a farm run where the bot discovers a viable farming
path in-session, then detects nodes, navigates to them, harvests, and continues
looping so farming can run with minimal manual input.

**Why this priority**: This is the core product value and defines the minimum
usable feature.

**Independent Test**: Can be fully tested by starting from a fresh map context,
allowing route discovery to complete, and verifying node detection, navigation,
harvesting, and loop restart behavior.

**Acceptance Scenarios**:

1. **Given** an active game window and no stored route, **When** the operator
  starts automation, **Then** the bot discovers a reusable path and transitions
  into farming loop execution.
2. **Given** route completion, **When** cooldown wait criteria are met,
  **Then** the bot starts the next farming cycle automatically.

---

### User Story 2 - Monitor and Control Runs (Priority: P2)

As an operator, I can monitor each farm cycle through logs and telemetry and
pause, resume, or stop safely when conditions change.

**Why this priority**: Reliable unattended use depends on visibility and safe
operator control.

**Independent Test**: Can be fully tested by running a cycle and verifying that
telemetry captures major events and controls work without losing run state.

**Acceptance Scenarios**:

1. **Given** an active farming cycle, **When** the operator triggers pause,
  **Then** automation halts movement and actions while preserving current state.
2. **Given** a paused cycle, **When** the operator resumes, **Then** the bot
  continues from the preserved route state without restarting the run.
3. **Given** an active farming cycle, **When** the operator triggers stop,
  **Then** the bot exits automation safely and writes final cycle telemetry.

---

### User Story 3 - Extend Detection and Prioritization (Priority: P3)

As an advanced operator, I can enable optional minimap node detection and dynamic
node prioritization to improve farming efficiency in crowded or variable routes.

**Why this priority**: This improves efficiency but is not required for MVP
automation.

**Independent Test**: Can be tested by enabling optional features and confirming
node targeting order changes according to configured prioritization rules.

**Acceptance Scenarios**:

1. **Given** optional minimap detection is enabled, **When** an off-screen node
  is visible in minimap context, **Then** the bot can include it in target
  selection when it is reachable by route rules.
2. **Given** dynamic prioritization is enabled, **When** multiple candidate
  nodes are available, **Then** the bot selects the highest-priority candidate
  according to configured policy.

---

### User Story 4 - Train and Serve Learned Policy (Priority: P2)

As an operator, I can train a policy artifact from collected run signals and use
it for runtime action recommendations so model-guided prioritization can be
validated in production-like runs.

**Why this priority**: The project already emits policy signals; without a
training and inference path those signals cannot improve behavior.

**Independent Test**: Generate policy signals from one or more runs, trigger
training, and verify a model artifact is produced and can return deterministic
recommendations for valid state input.

**Acceptance Scenarios**:

1. **Given** collected policy signals are present, **When** training is
  requested, **Then** the system creates a persisted policy artifact with
  metadata about samples and actions.
2. **Given** a trained policy exists, **When** a state feature payload is
  submitted for recommendation, **Then** the system returns an action and
  confidence score without requiring retraining.
3. **Given** no trained policy exists, **When** recommendation is requested,
  **Then** the system responds with a clear, stable error code.

---

### Edge Cases

- What happens when no harvestable nodes are detected for an entire route loop?
- What happens when route discovery cannot produce a stable loop candidate?
- How does the bot behave when the game window loses focus or is minimized?
- How does the bot recover when movement is blocked or path progress stalls?
- What happens when a node is detected but harvesting fails repeatedly?
- How does the system handle unexpected game-state interruptions (combat,
  loading screens, or temporary UI overlays)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture the game view at configurable intervals during
  active farming cycles.
- **FR-002**: System MUST detect harvestable resource nodes from captured screen
  data.
- **FR-003**: System MUST discover route-based navigation paths dynamically
  during runtime and persist discovered waypoints for reuse.
- **FR-004**: System MUST execute harvesting actions automatically when node
  interaction conditions are met.
- **FR-005**: System MUST run a cooldown loop that repeats route farming after
  configurable wait criteria are satisfied.
- **FR-006**: System MUST record structured logs and telemetry for route
  progress, detections, action outcomes, failures, and cycle summaries.
- **FR-007**: System MUST allow the operator to start, pause, resume, and stop
  automation safely at runtime.
- **FR-008**: System MUST provide modular component boundaries for capture,
  detection, navigation, action execution, and telemetry so each can be replaced
  independently.
- **FR-009**: System MUST continue operation with recovery behavior when
  detections fail intermittently, including fallback continuation of route flow.
- **FR-010**: System SHOULD support minimap-based node detection as an optional
  enhancement.
- **FR-011**: System SHOULD support dynamic node prioritization as an optional
  enhancement.
- **FR-012**: System MUST expose run-state and action outcome signals in a
  consistent format suitable for future reinforcement-learning driven policies,
  and support training in this phase.
- **FR-013**: System MUST run inside Docker to isolate dependencies while
  interacting with the local game client through explicitly configured
  host-bridge capture and input channels on the same machine.
- **FR-014**: System MUST persist policy training records and artifacts in the
  configured data directory with reproducible metadata (sample count, action
  vocabulary, training timestamp).
- **FR-015**: System MUST provide an API endpoint to trigger offline policy
  training from collected policy signals.
- **FR-016**: System MUST provide an API endpoint to request action
  recommendation from the latest trained policy.
- **FR-017**: System MUST emit policy signals during active cycles so training
  data collection happens without manual post-processing.
- **FR-018**: System MUST support a zero-touch mission mode on supported host
  platforms (including Windows) where, after container startup with mission
  defaults, the bot auto-starts a run and performs continuous policy retraining
  and runtime policy application without manual training API calls.
- **FR-019**: System MUST support runtime action execution through the configured
  host input bridge when enabled, mapping policy-selected actions to bounded
  keyboard or mouse inputs suitable for in-game automation.
- **FR-020**: System MUST provide a web-based dashboard UI for bot control and
  monitoring that operates without stealing focus from the game client,
  supporting run lifecycle control (start/pause/resume/stop), real-time status
  updates, policy model information, bridge health monitoring, and recent action
  logs accessible via HTTP browser interface on the same machine or network.
- **FR-021**: System MUST detect the in-game gather/interact prompt visibility
  from captured frames and deterministically prioritize harvest interaction
  actions when prompt visibility is high, so gather key execution is reliable at
  close range.

### Constitution Alignment Requirements *(mandatory)*

- **CAR-001 (Code Quality)**: All modules MUST define clear contracts, avoid
  duplicated logic, and pass configured linting and static checks for touched
  files before merge.
- **CAR-002 (Testing Standard)**: Automated tests MUST cover capture,
  detection, navigation, harvesting control flow, and telemetry emission;
  defects MUST add regression tests.
- **CAR-003 (UX Consistency)**: Operator-facing controls, status labels, and
  failure messages MUST remain consistent across run lifecycle states.
- **CAR-004 (Performance)**: Feature delivery MUST include measurable budgets
  for capture-to-decision timing and cycle throughput, validated during
  acceptance testing.

### Key Entities *(include if feature involves data)*

- **FarmRoute**: Defines route identity, waypoint sequence, loop mode, and
  cooldown policy, generated from discovery or loaded from prior sessions.
- **RouteDiscoverySession**: Represents one path exploration attempt, including
  sampled movement segments, node encounters, and resulting loop candidate score.
- **Waypoint**: Represents a navigable step with position cues and traversal
  tolerances.
- **NodeObservation**: Represents a detected harvest candidate with type,
  confidence, location context, and timestamp.
- **HarvestAttempt**: Represents one attempt to gather a node, including
  preconditions, action sequence, outcome, and retry count.
- **FarmCycle**: Represents one complete route pass and cooldown phase with
  start/end times, harvested count, failures, and completion status.
- **TelemetryEvent**: Represents structured runtime events for diagnostics,
  monitoring, and post-run analysis.
- **PolicySignal**: Represents normalized state/action/outcome data exported for
  future reinforcement learning integration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can configure and start a complete farm loop in under 5
  minutes without editing source code.
- **SC-002**: In controlled runs without pre-existing route files, the bot
  discovers a usable loop and starts farming within 10 minutes in at least 90%
  of attempts.
- **SC-003**: In controlled test runs, the bot successfully completes at least
  95% of planned waypoints per cycle.
- **SC-004**: In controlled test runs, at least 85% of detected reachable nodes
  are harvested successfully within the same cycle.
- **SC-005**: 100% of farm cycles produce a complete telemetry summary including
  route duration, detections, harvest attempts, and failure counts.
- **SC-006**: 100% of releases for this feature complete with zero unresolved
  lint/static-analysis violations in modified files.
- **SC-007**: 100% of required automated tests for this feature pass in
  continuous integration before merge.
- **SC-008**: Median capture-to-decision latency remains at or below 500 ms and
  p95 remains at or below 900 ms in the reference test environment.
- **SC-009**: Cooldown-to-restart latency remains at or below 5 seconds in at
  least 95% of completed cycles.
- **SC-010**: The Dockerized runtime can capture game frames and issue input
  commands through host bridge channels with no unrecoverable bridge failures
  during a 2-hour soak test and recovers transient bridge disconnects within 3
  seconds.
- **SC-011**: Training endpoint produces a policy artifact from collected
  signals in under 30 seconds for a 10,000-sample dataset on reference hardware.
- **SC-012**: Recommendation endpoint returns a valid action in under 100 ms for
  at least 95% of requests in local integration tests.
- **SC-013**: In mission mode on a Windows host, starting Docker Compose with a
  running game client begins autonomous signal collection and periodic policy
  retraining within 5 minutes with no manual training endpoint invocation.
- **SC-014**: When runtime input execution is enabled and host bridge is
  healthy, the bot emits non-noop in-game input actions during active cycles
  and records corresponding runtime policy signals for those steps.
- **SC-015**: Web dashboard is accessible on localhost and network via HTTP,
  displays real-time run status and recent actions updating every 2 seconds,
  supports run lifecycle control with immediate visual feedback, and does not
  cause game window focus loss when operated.
- **SC-016**: During active runtime with healthy host bridge, when the gather
  prompt is visible in frame capture, action selection deterministically resolves
  to harvest for that step and telemetry records prompt visibility state.

## Assumptions

- Initial release targets single-machine operation with one active game client
  session.
- The game client remains on the Docker host, and the bot container uses shared
  host-access mechanisms for capture and input automation.
- Initial route inventory is empty; routes are discovered by the bot during
  runtime and persisted after successful cycles.
- Optional minimap detection and dynamic prioritization are in scope as
  enhancements and may be delivered after MVP route-loop automation.
- Offline policy training and recommendation are in scope for this release
  using collected policy signals and persisted model artifacts.
- Logging and telemetry retention follows existing project defaults unless
  overridden by future operational requirements.

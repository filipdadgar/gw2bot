# Data Model: Modular GW2 Resource Farming Bot

## Entity: FarmRoute
- Purpose: Defines a reusable farming path and loop policy discovered by the bot or refined from prior runs.
- Fields:
  - route_id (string, required, unique)
  - name (string, required, 1-80 chars)
  - waypoints (array[WaypointRef], required, min 2)
  - cooldown_seconds (integer, required, min 0)
  - enabled (boolean, required, default true)
  - source (enum, required)  # discovered | imported | hybrid
  - metadata (object, optional)
- Relationships:
  - FarmRoute 1..* Waypoint
  - FarmRoute 1..* FarmCycle
- Validation Rules:
  - waypoint order must be contiguous and unique per route.
  - discovered routes must have loop_confidence >= configured acceptance threshold.
  - cooldown must satisfy operational minimum/maximum configuration bounds.

## Entity: RouteDiscoverySession
- Purpose: Captures one route exploration and loop validation attempt.
- Fields:
  - discovery_id (string, required, unique)
  - state (enum, required)  # running | completed | failed | aborted
  - started_at_utc (string, required, ISO-8601)
  - ended_at_utc (string, optional, ISO-8601)
  - sampled_segments (array[object], required)
  - encountered_nodes (integer, required, min 0)
  - loop_confidence (float, required, range 0.0..1.0)
  - generated_route_id (string, optional, foreign key)
  - failure_reason (string, optional)
- Relationships:
  - RouteDiscoverySession 0..1 FarmRoute
- Validation Rules:
  - completed sessions require generated_route_id and loop_confidence above threshold.
  - failed/aborted sessions require failure_reason.

## Entity: Waypoint
- Purpose: Represents one route traversal target.
- Fields:
  - waypoint_id (string, required, unique within route)
  - route_id (string, required, foreign key)
  - order_index (integer, required, min 0)
  - screen_anchor (object, required)  # calibrated screen-relative anchor
  - tolerance_px (integer, required, min 1)
  - expected_node_types (array[string], optional)
- Relationships:
  - Waypoint *..1 FarmRoute
  - Waypoint 1..* NodeObservation
- Validation Rules:
  - order_index must form strict ascending sequence.
  - tolerance_px must be within configured movement precision range.

## Entity: NodeObservation
- Purpose: Captures one perception result for a candidate harvest node.
- Fields:
  - observation_id (string, required)
  - cycle_id (string, required, foreign key)
  - waypoint_id (string, optional, foreign key)
  - node_type (string, required)
  - confidence (float, required, range 0.0..1.0)
  - bbox (object, required)  # x, y, width, height in frame coordinates
  - minimap_hint (object, optional)
  - timestamp_utc (string, required, ISO-8601)
- Relationships:
  - NodeObservation *..1 Waypoint
  - NodeObservation *..1 FarmCycle
  - NodeObservation 1..* HarvestAttempt
- Validation Rules:
  - confidence below configured threshold is non-actionable.
  - bbox must lie within current capture frame bounds.

## Entity: HarvestAttempt
- Purpose: Tracks a discrete attempt to interact with one node.
- Fields:
  - attempt_id (string, required)
  - observation_id (string, required, foreign key)
  - cycle_id (string, required, foreign key)
  - action_sequence (array[string], required)  # move/interact/wait tokens
  - result (enum, required)  # success | failed_precondition | timeout | interrupted
  - retry_count (integer, required, min 0)
  - duration_ms (integer, required, min 0)
  - failure_reason (string, optional)
- Relationships:
  - HarvestAttempt *..1 NodeObservation
  - HarvestAttempt *..1 FarmCycle
- Validation Rules:
  - result=success requires failure_reason empty.
  - retries cannot exceed configured max retry budget.

## Entity: FarmCycle
- Purpose: Represents one complete route execution and cooldown period.
- Fields:
  - cycle_id (string, required, unique)
  - route_id (string, required, foreign key)
  - discovery_id (string, optional, foreign key)
  - state (enum, required)  # running | paused | completed | stopped | error
  - started_at_utc (string, required, ISO-8601)
  - ended_at_utc (string, optional, ISO-8601)
  - waypoints_completed (integer, required, min 0)
  - harvest_success_count (integer, required, min 0)
  - harvest_failure_count (integer, required, min 0)
  - cooldown_applied_seconds (integer, required, min 0)
- Relationships:
  - FarmCycle *..1 FarmRoute
  - FarmCycle *..1 RouteDiscoverySession (optional)
  - FarmCycle 1..* NodeObservation
  - FarmCycle 1..* HarvestAttempt
  - FarmCycle 1..* TelemetryEvent
- State Transitions:
  - running -> paused
  - paused -> running
  - running -> completed
  - running -> stopped
  - running -> error
  - paused -> stopped

## Entity: TelemetryEvent
- Purpose: Provides structured operational and diagnostics events.
- Fields:
  - event_id (string, required)
  - cycle_id (string, optional, foreign key)
  - level (enum, required)  # debug | info | warning | error
  - category (enum, required)  # capture | detection | navigation | action | control | performance
  - message (string, required)
  - payload (object, optional)
  - emitted_at_utc (string, required, ISO-8601)
- Relationships:
  - TelemetryEvent *..1 FarmCycle (optional for lifecycle/global events)
- Validation Rules:
  - error events must include payload.reason_code.
  - performance events must include at least one latency or throughput metric.

## Entity: PolicySignal
- Purpose: Standardized data record for future RL training/inference phases.
- Fields:
  - signal_id (string, required)
  - cycle_id (string, required, foreign key)
  - step_index (integer, required, min 0)
  - observation_ref (string, optional, foreign key)
  - state_features (object, required)
  - action_taken (string, required)
  - reward_proxy (float, required)
  - terminal (boolean, required)
  - generated_at_utc (string, required, ISO-8601)
- Relationships:
  - PolicySignal *..1 FarmCycle
  - PolicySignal *..1 NodeObservation (optional)
- Validation Rules:
  - terminal=true requires cycle state completed/stopped/error at or after same step.
  - action_taken must come from the controlled action vocabulary.

## Entity: PolicyArtifact
- Purpose: Versioned policy model metadata and persisted recommendation table.
- Fields:
  - model_id (string, required, unique)
  - artifact_path (string, required)
  - source_signal_path (string, required)
  - sample_count (integer, required, min 1)
  - action_count (integer, required, min 1)
  - default_action (string, required)
  - trained_at_utc (string, required, ISO-8601)
  - metadata (object, optional)
- Relationships:
  - PolicyArtifact 1..* PolicySignal (training input)
- Validation Rules:
  - artifact_path must exist after successful training.
  - default_action must be in the action vocabulary exported with the model.

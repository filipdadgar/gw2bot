"""Farm-cycle orchestration for run start/status and cooldown restart flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
import threading
import time
from typing import Any
from uuid import uuid4

from src.core.capture.interaction_prompt_detector import detect_gather_prompt_visible
from src.core.orchestration.policy_signal_emitter import PolicySignalEmitter
from src.core.persistence.policy_signal_store import PolicySignalStore
from src.core.orchestration.state_types import RunState
from src.core.persistence.storage import Storage

logger = logging.getLogger(__name__)


@dataclass
class RunSnapshot:
    cycle_id: str | None
    route_id: str | None
    status: str
    current_waypoint_index: int
    started_at_utc: str | None
    last_error: str | None = None
    cooldown_applied_seconds: int = 0


class FarmCycleOrchestrator:
    """Controls farm run lifecycle and restart behavior."""

    def __init__(self, storage: Storage, discovery_orchestrator) -> None:  # discovery typed loosely to avoid cyclic imports
        self._storage = storage
        self._discovery = discovery_orchestrator
        self._signal_emitter = PolicySignalEmitter()
        self._signal_store = PolicySignalStore(storage)
        self._runtime_thread: threading.Thread | None = None
        self._runtime_stop_event = threading.Event()
        self._runtime_waypoints: list[dict[str, int]] = []
        self._runtime_remount_pending = False
        self._runtime_mount_cycle_enabled = True
        self._runtime_waypoint_steering_enabled = True
        self._runtime_gather_lock_seconds = 1.6
        self._runtime_gather_lock_until = 0.0
        self._snapshot = RunSnapshot(
            cycle_id=None,
            route_id=None,
            status=RunState.IDLE.value,
            current_waypoint_index=0,
            started_at_utc=None,
            last_error=None,
        )

    def start(
        self,
        route_id: str | None,
        auto_discover_if_missing: bool = True,
        loop_enabled: bool = True,
        cooldown_override_seconds: int | None = None,
    ) -> RunSnapshot:
        _ = loop_enabled
        _ = cooldown_override_seconds

        resolved_route_id = route_id
        if resolved_route_id is None and auto_discover_if_missing:
            discovery = self._discovery.start()
            resolved_route_id = discovery.get("generated_route_id")  # type: ignore[assignment]

        if resolved_route_id is None:
            self._snapshot = RunSnapshot(
                cycle_id=None,
                route_id=None,
                status=RunState.ERROR.value,
                current_waypoint_index=0,
                started_at_utc=None,
                last_error="route_unavailable",
            )
            return self._snapshot

        route_file = Path(self._storage.routes_dir) / f"{resolved_route_id}.json"
        if not route_file.exists():
            self._snapshot = RunSnapshot(
                cycle_id=None,
                route_id=resolved_route_id,
                status=RunState.ERROR.value,
                current_waypoint_index=0,
                started_at_utc=None,
                last_error="route_not_found",
            )
            return self._snapshot

        self._runtime_waypoints = self._load_route_waypoints(route_file)
        self._runtime_remount_pending = False
        self._runtime_gather_lock_until = 0.0

        self._snapshot = RunSnapshot(
            cycle_id=f"cycle-{uuid4().hex[:8]}",
            route_id=resolved_route_id,
            status=RunState.RUNNING.value,
            current_waypoint_index=0,
            started_at_utc=datetime.now(UTC).isoformat(),
            last_error=None,
            cooldown_applied_seconds=0,
        )

        return self._snapshot

    def emit_runtime_policy_signal(
        self,
        state_features: dict[str, object],
        action_taken: str,
        reward_proxy: float,
        terminal: bool = False,
        observation_ref: str | None = None,
    ) -> None:
        """Emit a runtime signal for the active cycle, if one exists."""

        cycle_id = self._snapshot.cycle_id
        if cycle_id is None:
            return

        signal = self._signal_emitter.emit(
            cycle_id=cycle_id,
            step_index=self._snapshot.current_waypoint_index,
            state_features=state_features,
            action_taken=action_taken,
            reward_proxy=reward_proxy,
            terminal=terminal,
            observation_ref=observation_ref,
        )
        self._signal_store.persist(signal)

    def seed_policy_signals(self) -> None:
        """Emit deterministic fallback signals when runtime perception is unavailable."""

        self._emit_bootstrap_policy_signals(cycle_id=self._snapshot.cycle_id)

    def start_runtime_loop(
        self,
        capture_bridge: Any,
        input_bridge: Any,
        policy_registry: Any,
        policy_enabled: bool,
        input_enabled: bool,
        policy_min_confidence: float,
        interval_seconds: float,
        mount_cycle_enabled: bool = True,
        waypoint_steering_enabled: bool = True,
        gather_lock_seconds: float = 1.6,
    ) -> None:
        """Start a background loop that emits policy signals while run is active."""

        if self._runtime_thread is not None and self._runtime_thread.is_alive():
            return

        self._runtime_mount_cycle_enabled = bool(mount_cycle_enabled)
        self._runtime_waypoint_steering_enabled = bool(waypoint_steering_enabled)
        self._runtime_gather_lock_seconds = max(0.0, float(gather_lock_seconds))
        self._runtime_gather_lock_until = 0.0
        self._runtime_stop_event.clear()

        def _worker() -> None:
            while not self._runtime_stop_event.is_set():
                status = self._snapshot.status

                if status == RunState.STOPPING.value:
                    self.emit_runtime_policy_signal(
                        state_features={"reason": "operator_stop", "bridge_enabled": 1.0 if capture_bridge else 0.0},
                        action_taken="stop",
                        reward_proxy=0.0,
                        terminal=True,
                    )
                    self._snapshot.status = RunState.IDLE.value
                    break

                if status == RunState.PAUSED.value:
                    time.sleep(interval_seconds)
                    continue

                if status != RunState.RUNNING.value:
                    break

                try:
                    state_features: dict[str, object]
                    if capture_bridge is not None:
                        frame_capture = capture_bridge.capture()
                        frame = frame_capture.frame
                        brightness = float(frame.mean() / 255.0)
                        contrast = float(frame.std() / 255.0)
                        gather_prompt_visible = 1.0 if detect_gather_prompt_visible(frame) else 0.0
                        state_features = {
                            "brightness": round(brightness, 4),
                            "contrast": round(contrast, 4),
                            "frame_width": frame_capture.width,
                            "frame_height": frame_capture.height,
                            "bridge_enabled": 1.0,
                            "gather_prompt_visible": gather_prompt_visible,
                        }
                    else:
                        state_features = {
                            "brightness": 0.5,
                            "contrast": 0.25,
                            "frame_width": 0,
                            "frame_height": 0,
                            "bridge_enabled": 0.0,
                            "gather_prompt_visible": 0.0,
                        }

                    nav_direction_bias = self._compute_route_direction_bias(
                        step_index=self._snapshot.current_waypoint_index
                    )
                    now_monotonic = time.monotonic()
                    lock_active = self._is_gather_lock_active(now=now_monotonic)
                    state_features["nav_direction_bias"] = float(nav_direction_bias)
                    state_features["remount_pending"] = 1.0 if self._runtime_remount_pending else 0.0
                    state_features["gather_lock_remaining_ms"] = self._gather_lock_remaining_ms(now=now_monotonic)

                    action_taken = self._select_action(
                        state_features=state_features,
                        policy_registry=policy_registry,
                        policy_enabled=policy_enabled,
                        policy_min_confidence=policy_min_confidence,
                    )

                    if input_enabled and input_bridge is not None:
                        if (
                            self._runtime_mount_cycle_enabled
                            and action_taken == "navigate"
                            and self._runtime_remount_pending
                            and not lock_active
                        ):
                            self._tap_key(input_bridge=input_bridge, key="x", hold_seconds=0.06)
                            self._runtime_remount_pending = False
                            state_features["mount_action"] = "remount"

                        if lock_active and action_taken == "navigate":
                            state_features["input_suppressed_reason"] = "gather_lock"
                        else:
                            self._execute_runtime_action(
                                action_taken=action_taken,
                                input_bridge=input_bridge,
                                step_index=self._snapshot.current_waypoint_index,
                                direction_bias=nav_direction_bias,
                            )

                        if self._runtime_mount_cycle_enabled and action_taken in {"harvest", "interact"}:
                            self._runtime_remount_pending = True
                            self._set_gather_lock(now=now_monotonic)

                    reward_proxy = max(0.0, min(1.0, float(state_features.get("contrast", 0.0)) + 0.2))
                    self.emit_runtime_policy_signal(
                        state_features=state_features,
                        action_taken=action_taken,
                        reward_proxy=reward_proxy,
                        terminal=False,
                    )
                    self._snapshot.current_waypoint_index += 1
                except Exception:
                    logger.exception("runtime_loop_iteration_failed")
                    self.seed_policy_signals()

                time.sleep(interval_seconds)

        self._runtime_thread = threading.Thread(target=_worker, name="gw2bot-runtime-loop", daemon=True)
        self._runtime_thread.start()

    @staticmethod
    def _execute_runtime_action(
        action_taken: str,
        input_bridge: Any,
        step_index: int = 0,
        direction_bias: int = 0,
    ) -> None:
        """Map runtime actions to conservative input taps.

        This intentionally avoids long key holds so accidental sustained input is minimized.
        """

        if action_taken == "navigate":
            FarmCycleOrchestrator._execute_navigation_pattern(
                input_bridge=input_bridge,
                step_index=step_index,
                direction_bias=direction_bias,
            )
            return

        action_key_map = {
            "harvest": "f",
            "interact": "f",
        }
        key = action_key_map.get(action_taken)
        if key is None:
            return

        FarmCycleOrchestrator._tap_key(input_bridge=input_bridge, key=key)

    @staticmethod
    def _execute_navigation_pattern(input_bridge: Any, step_index: int, direction_bias: int = 0) -> None:
        """Apply simple steering corrections so navigation is not straight-line only.

        Pattern repeats every 6 runtime steps with occasional A/D taps.
        """

        if direction_bias < 0:
            preferred_turn = "a"
        elif direction_bias > 0:
            preferred_turn = "d"
        else:
            preferred_turn = "a" if (max(0, int(step_index)) % 2 == 0) else "d"

        pattern: tuple[tuple[str, ...], ...] = (
            ("w",),
            ("w", preferred_turn),
            ("w",),
            ("w",),
            ("w", preferred_turn),
            ("w",),
        )

        keys = pattern[max(0, int(step_index)) % len(pattern)]
        for key in keys:
            hold = 0.05 if key in {"a", "d"} else 0.08
            FarmCycleOrchestrator._tap_key(input_bridge=input_bridge, key=key, hold_seconds=hold)

    def _compute_route_direction_bias(self, step_index: int) -> int:
        """Estimate steering direction from persisted waypoint sequence.

        Returns:
        -1 for left bias, +1 for right bias, 0 for neutral.
        """

        if not self._runtime_waypoint_steering_enabled:
            return 0
        if len(self._runtime_waypoints) < 2:
            return 0

        segment = (max(0, int(step_index)) // 6) % len(self._runtime_waypoints)
        p0 = self._runtime_waypoints[segment]
        p1 = self._runtime_waypoints[(segment + 1) % len(self._runtime_waypoints)]
        dx = int(p1.get("x", 0)) - int(p0.get("x", 0))

        if dx <= -8:
            return -1
        if dx >= 8:
            return 1
        return 0

    def _set_gather_lock(self, now: float | None = None) -> None:
        """Start or refresh the post-gather lock window."""

        if self._runtime_gather_lock_seconds <= 0.0:
            self._runtime_gather_lock_until = 0.0
            return
        now_value = time.monotonic() if now is None else float(now)
        self._runtime_gather_lock_until = now_value + self._runtime_gather_lock_seconds

    def _is_gather_lock_active(self, now: float | None = None) -> bool:
        """Return True when movement/remount should be temporarily suppressed."""

        now_value = time.monotonic() if now is None else float(now)
        return now_value < self._runtime_gather_lock_until

    def _gather_lock_remaining_ms(self, now: float | None = None) -> int:
        """Return remaining gather lock time in milliseconds."""

        now_value = time.monotonic() if now is None else float(now)
        remaining = self._runtime_gather_lock_until - now_value
        return max(0, int(remaining * 1000.0))

    @staticmethod
    def _load_route_waypoints(route_file: Path) -> list[dict[str, int]]:
        """Load waypoint list from persisted route file, returning an empty list on failure."""

        try:
            payload = json.loads(route_file.read_text(encoding="utf-8"))
        except Exception:
            return []

        raw_waypoints = payload.get("waypoints")
        if not isinstance(raw_waypoints, list):
            return []

        waypoints: list[dict[str, int]] = []
        for wp in raw_waypoints:
            if not isinstance(wp, dict):
                continue
            waypoints.append(
                {
                    "x": int(wp.get("x", 0)),
                    "y": int(wp.get("y", 0)),
                }
            )
        return waypoints

    @staticmethod
    def _tap_key(input_bridge: Any, key: str, hold_seconds: float = 0.08) -> None:
        """Send a short key tap and release when supported by the bridge."""

        input_bridge.press(key)
        release = getattr(input_bridge, "release", None)
        if callable(release):
            time.sleep(max(0.01, hold_seconds))
            release(key)

    @staticmethod
    def _select_action(
        state_features: dict[str, object],
        policy_registry: Any,
        policy_enabled: bool,
        policy_min_confidence: float,
    ) -> str:
        """Choose action from policy when confident, else fallback heuristic."""

        # Deterministic safety trigger: if the on-screen gather prompt is visible,
        # prioritize harvest so runtime input executes the gather key immediately.
        if float(state_features.get("gather_prompt_visible", 0.0)) >= 0.5:
            return "harvest"

        fallback_action = "navigate"

        if not policy_enabled or not getattr(policy_registry, "has_artifact", lambda: False)():
            return fallback_action

        recommendation = policy_registry.recommend(state_features=state_features)
        action = str(recommendation.get("action", fallback_action))
        confidence = float(recommendation.get("confidence", 0.0))
        if confidence < policy_min_confidence:
            return fallback_action
        if action in {"harvest", "interact"}:
            return fallback_action
        return action

    def _emit_bootstrap_policy_signals(self, cycle_id: str | None) -> None:
        """Emit deterministic training records until full real loop wiring is in place."""

        if cycle_id is None:
            return

        templates = [
            ({"distance": 0.15, "confidence": 0.92, "rarity": 0.9}, "harvest", 1.0, False),
            ({"distance": 0.42, "confidence": 0.64, "rarity": 0.4}, "navigate", 0.3, False),
            ({"distance": 0.08, "confidence": 0.97, "rarity": 0.7}, "interact", 0.8, True),
        ]

        for step_index, (state_features, action_taken, reward_proxy, terminal) in enumerate(templates):
            signal = self._signal_emitter.emit(
                cycle_id=cycle_id,
                step_index=step_index,
                state_features=state_features,
                action_taken=action_taken,
                reward_proxy=reward_proxy,
                terminal=terminal,
                observation_ref=None,
            )
            self._signal_store.persist(signal)

    def status(self) -> RunSnapshot:
        return self._snapshot

    def pause(self) -> bool:
        if self._snapshot.status != RunState.RUNNING.value:
            return False
        self._snapshot.status = RunState.PAUSED.value
        return True

    def resume(self) -> bool:
        if self._snapshot.status != RunState.PAUSED.value:
            return False
        self._snapshot.status = RunState.RUNNING.value
        return True

    def stop(self) -> bool:
        if self._snapshot.status not in {RunState.RUNNING.value, RunState.PAUSED.value}:
            return False
        self._snapshot.status = RunState.STOPPING.value
        return True

    def complete_cycle_and_schedule_restart(self, cooldown_seconds: int = 0) -> RunSnapshot:
        self._snapshot.status = RunState.RUNNING.value
        self._snapshot.cooldown_applied_seconds = cooldown_seconds
        self._snapshot.current_waypoint_index = 0
        return self._snapshot

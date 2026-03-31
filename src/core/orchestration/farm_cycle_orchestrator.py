"""Farm-cycle orchestration for run start/status and cooldown restart flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import threading
import time
from typing import Any
from uuid import uuid4

from src.core.orchestration.policy_signal_emitter import PolicySignalEmitter
from src.core.persistence.policy_signal_store import PolicySignalStore
from src.core.orchestration.state_types import RunState
from src.core.persistence.storage import Storage


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
        policy_registry: Any,
        policy_enabled: bool,
        policy_min_confidence: float,
        interval_seconds: float,
    ) -> None:
        """Start a background loop that emits policy signals while run is active."""

        if self._runtime_thread is not None and self._runtime_thread.is_alive():
            return

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
                        state_features = {
                            "brightness": round(brightness, 4),
                            "contrast": round(contrast, 4),
                            "frame_width": frame_capture.width,
                            "frame_height": frame_capture.height,
                            "bridge_enabled": 1.0,
                        }
                    else:
                        state_features = {
                            "brightness": 0.5,
                            "contrast": 0.25,
                            "frame_width": 0,
                            "frame_height": 0,
                            "bridge_enabled": 0.0,
                        }

                    action_taken = self._select_action(
                        state_features=state_features,
                        policy_registry=policy_registry,
                        policy_enabled=policy_enabled,
                        policy_min_confidence=policy_min_confidence,
                    )

                    reward_proxy = max(0.0, min(1.0, float(state_features.get("contrast", 0.0)) + 0.2))
                    self.emit_runtime_policy_signal(
                        state_features=state_features,
                        action_taken=action_taken,
                        reward_proxy=reward_proxy,
                        terminal=False,
                    )
                    self._snapshot.current_waypoint_index += 1
                except Exception:
                    self.seed_policy_signals()

                time.sleep(interval_seconds)

        self._runtime_thread = threading.Thread(target=_worker, name="gw2bot-runtime-loop", daemon=True)
        self._runtime_thread.start()

    @staticmethod
    def _select_action(
        state_features: dict[str, object],
        policy_registry: Any,
        policy_enabled: bool,
        policy_min_confidence: float,
    ) -> str:
        """Choose action from policy when confident, else fallback heuristic."""

        brightness = float(state_features.get("brightness", 0.0))
        fallback_action = "harvest" if brightness > 0.6 else "navigate"

        if not policy_enabled or not getattr(policy_registry, "has_artifact", lambda: False)():
            return fallback_action

        recommendation = policy_registry.recommend(state_features=state_features)
        action = str(recommendation.get("action", fallback_action))
        confidence = float(recommendation.get("confidence", 0.0))
        if confidence < policy_min_confidence:
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

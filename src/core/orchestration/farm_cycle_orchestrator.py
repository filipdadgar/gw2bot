"""Farm-cycle orchestration for run start/status and cooldown restart flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
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

        self._emit_bootstrap_policy_signals(cycle_id=self._snapshot.cycle_id)
        return self._snapshot

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

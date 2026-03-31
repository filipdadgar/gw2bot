"""Discovery orchestration lifecycle management."""

from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from src.core.discovery.discovery_models import RouteDiscoverySession
from src.core.discovery.route_builder import RouteBuilder
from src.core.orchestration.state_types import DiscoveryState


class DiscoveryOrchestrator:
    """Manages route discovery sessions and their externally visible status."""

    def __init__(self, route_builder: RouteBuilder) -> None:
        self._route_builder = route_builder
        self._current: RouteDiscoverySession | None = None

    def start(self, max_duration_seconds: int = 600, min_loop_confidence: float = 0.7) -> dict[str, object]:
        _ = max_duration_seconds
        session = RouteDiscoverySession(
            discovery_id=f"discovery-{uuid4().hex[:8]}",
            state=DiscoveryState.RUNNING.value,
            sampled_segments=10,
            encountered_nodes=4,
        )
        self._current = self._route_builder.complete_session(
            session=session,
            min_loop_confidence=min_loop_confidence,
        )
        return self.status()

    def status(self) -> dict[str, object]:
        if self._current is None:
            return {
                "discovery_id": None,
                "status": DiscoveryState.IDLE.value,
                "loop_confidence": None,
                "generated_route_id": None,
                "last_error": None,
            }

        payload = asdict(self._current)
        return {
            "discovery_id": payload["discovery_id"],
            "status": payload["state"],
            "loop_confidence": payload["loop_confidence"],
            "generated_route_id": payload["generated_route_id"],
            "last_error": payload["failure_reason"],
        }

    def stop(self) -> dict[str, object]:
        if self._current is None:
            return self.status()
        if self._current.state == DiscoveryState.RUNNING.value:
            self._current.state = DiscoveryState.STOPPING.value
        elif self._current.state == DiscoveryState.COMPLETED.value:
            self._current.state = DiscoveryState.IDLE.value
        return self.status()

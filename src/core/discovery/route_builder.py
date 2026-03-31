"""Route scoring and persistence for discovered farming loops."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from src.core.discovery.discovery_models import RouteDiscoverySession
from src.core.persistence.storage import Storage


class RouteBuilder:
    """Builds and stores routes discovered during exploration."""

    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    def score_loop(self, sampled_segments: int, encountered_nodes: int) -> float:
        """Produce a normalized confidence score for candidate loop quality."""

        raw = (sampled_segments * 0.06) + (encountered_nodes * 0.12)
        return max(0.0, min(1.0, raw))

    def persist_route(self, waypoints: list[dict[str, int]], cooldown_seconds: int = 30) -> str:
        """Persist a discovered route and return its identifier."""

        route_id = f"route-{uuid4().hex[:8]}"
        payload = {
            "route_id": route_id,
            "name": "discovered-route",
            "source": "discovered",
            "cooldown_seconds": cooldown_seconds,
            "waypoints": waypoints,
            "created_at_utc": datetime.now(UTC).isoformat(),
        }
        self._storage.write_json(self._storage.routes_dir / f"{route_id}.json", payload)
        return route_id

    def complete_session(
        self,
        session: RouteDiscoverySession,
        min_loop_confidence: float,
        default_waypoints: list[dict[str, int]] | None = None,
    ) -> RouteDiscoverySession:
        """Finalize discovery and persist a route when confidence is sufficient."""

        session.loop_confidence = self.score_loop(
            sampled_segments=session.sampled_segments,
            encountered_nodes=session.encountered_nodes,
        )
        if session.loop_confidence >= min_loop_confidence:
            waypoints = default_waypoints or [{"x": 100, "y": 100}, {"x": 220, "y": 220}]
            session.generated_route_id = self.persist_route(waypoints=waypoints)
            session.state = "completed"
            session.failure_reason = None
        else:
            session.state = "failed"
            session.failure_reason = "insufficient_loop_confidence"
        session.ended_at_utc = datetime.now(UTC).isoformat()

        audit_path = Path(self._storage.telemetry_dir) / "discovery-sessions.jsonl"
        self._storage.append_jsonl(audit_path, asdict(session))
        return session

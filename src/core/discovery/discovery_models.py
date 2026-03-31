"""Data models for route discovery sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class RouteDiscoverySession:
    """Represents one discovery attempt and its resulting route quality."""

    discovery_id: str
    state: str
    sampled_segments: int = 0
    encountered_nodes: int = 0
    loop_confidence: float = 0.0
    generated_route_id: str | None = None
    failure_reason: str | None = None
    started_at_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    ended_at_utc: str | None = None

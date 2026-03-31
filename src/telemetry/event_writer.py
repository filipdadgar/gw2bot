"""Structured telemetry event writing with simple file rotation."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.core.persistence.storage import Storage


class EventWriter:
    """Writes telemetry events to JSONL and rotates when file grows too large."""

    def __init__(self, storage: Storage, max_bytes: int = 2_000_000) -> None:
        self._storage = storage
        self._max_bytes = max_bytes
        self._target = self._storage.telemetry_dir / "events.jsonl"

    def _rotate_if_needed(self) -> None:
        if self._target.exists() and self._target.stat().st_size >= self._max_bytes:
            rotated = self._storage.telemetry_dir / f"events-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.jsonl"
            self._target.replace(rotated)

    def write_event(
        self,
        cycle_id: str | None,
        category: str,
        payload: dict[str, Any] | None = None,
        level: str = "info",
        message: str = "",
    ) -> Path:
        self._rotate_if_needed()
        event = {
            "event_id": f"evt-{datetime.now(UTC).timestamp()}",
            "cycle_id": cycle_id,
            "category": category,
            "level": level,
            "message": message,
            "payload": payload or {},
            "emitted_at_utc": datetime.now(UTC).isoformat(),
        }
        self._storage.append_jsonl(self._target, event)
        return self._target

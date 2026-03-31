"""Persistence adapter for policy signal records."""

from __future__ import annotations

from pathlib import Path

from src.core.persistence.storage import Storage


class PolicySignalStore:
    """Writes policy signals to JSONL for later offline training usage."""

    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    def persist(self, signal: dict[str, object]) -> Path:
        target = self._storage.telemetry_dir / "policy-signals.jsonl"
        self._storage.append_jsonl(target, signal)
        return target

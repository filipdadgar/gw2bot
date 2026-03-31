"""Telemetry aggregation for cycle summary API responses."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median

from src.core.persistence.storage import Storage


class CycleSummaryService:
    """Builds per-cycle summary metrics from telemetry events."""

    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._events_path = self._storage.telemetry_dir / "events.jsonl"

    def _load_events(self, cycle_id: str) -> list[dict[str, object]]:
        if not self._events_path.exists():
            return []
        events: list[dict[str, object]] = []
        with self._events_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get("cycle_id") == cycle_id:
                    events.append(item)
        return events

    def summarize(self, cycle_id: str, route_id: str | None, duration_seconds: float = 0.0) -> dict[str, object]:
        events = self._load_events(cycle_id)

        detections = sum(1 for e in events if e.get("category") == "detection")
        harvest_success = 0
        harvest_failure = 0
        latencies: list[int] = []

        for event in events:
            if event.get("category") == "action":
                payload = event.get("payload", {})
                if isinstance(payload, dict):
                    result = payload.get("result")
                    if result == "success":
                        harvest_success += 1
                    elif result == "failure":
                        harvest_failure += 1
            if event.get("category") == "performance":
                payload = event.get("payload", {})
                if isinstance(payload, dict) and "capture_to_decision_ms" in payload:
                    latencies.append(int(payload["capture_to_decision_ms"]))

        median_latency = int(median(latencies)) if latencies else 0
        p95_latency = max(latencies) if latencies else 0

        return {
            "cycle_id": cycle_id,
            "route_id": route_id,
            "duration_seconds": duration_seconds,
            "detections": detections,
            "harvest_success_count": harvest_success,
            "harvest_failure_count": harvest_failure,
            "capture_to_decision_median_ms": median_latency,
            "capture_to_decision_p95_ms": p95_latency,
        }

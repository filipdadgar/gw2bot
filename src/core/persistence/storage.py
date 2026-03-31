"""Persistence helpers for route and telemetry artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Storage:
    """File-backed storage rooted at the configured data directory."""

    def __init__(self, data_dir: str) -> None:
        self._base = Path(data_dir)
        self._routes_dir = self._base / "routes"
        self._telemetry_dir = self._base / "telemetry"
        self._models_dir = self._base / "models"
        self._routes_dir.mkdir(parents=True, exist_ok=True)
        self._telemetry_dir.mkdir(parents=True, exist_ok=True)
        self._models_dir.mkdir(parents=True, exist_ok=True)

    @property
    def routes_dir(self) -> Path:
        return self._routes_dir

    @property
    def telemetry_dir(self) -> Path:
        return self._telemetry_dir

    @property
    def models_dir(self) -> Path:
        return self._models_dir

    def write_json(self, target: Path, payload: dict[str, Any]) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def append_jsonl(self, target: Path, payload: dict[str, Any]) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, separators=(",", ":")) + "\n")

"""Policy-signal dataset parsing helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PolicySignalSample:
    """One normalized sample extracted from policy-signals.jsonl."""

    state_key: str
    action_taken: str
    reward_proxy: float


def _normalize_feature_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_feature_value(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [_normalize_feature_value(item) for item in value]
    return value


def normalize_state_key(state_features: dict[str, Any]) -> str:
    """Build a deterministic hashable state key from arbitrary feature payload."""

    normalized = _normalize_feature_value(state_features)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


class PolicySignalDataset:
    """Loads policy signal samples from JSONL files."""

    def __init__(self, signals_path: Path) -> None:
        self._signals_path = signals_path

    @property
    def signals_path(self) -> Path:
        return self._signals_path

    def load_samples(self) -> list[PolicySignalSample]:
        if not self._signals_path.exists():
            return []

        samples: list[PolicySignalSample] = []
        with self._signals_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                state_features = payload.get("state_features")
                action_taken = payload.get("action_taken")
                reward_proxy = payload.get("reward_proxy")
                if not isinstance(state_features, dict) or not isinstance(action_taken, str):
                    continue
                if not isinstance(reward_proxy, (int, float)):
                    continue
                samples.append(
                    PolicySignalSample(
                        state_key=normalize_state_key(state_features),
                        action_taken=action_taken,
                        reward_proxy=float(reward_proxy),
                    )
                )
        return samples

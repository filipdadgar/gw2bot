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


# Features excluded from the state key — they are metadata or change every frame
# and would make every state unique, preventing the policy from ever matching.
_STATE_KEY_EXCLUDE: frozenset[str] = frozenset({
    "bridge_enabled",
    "frame_width",
    "frame_height",
    "gather_lock_remaining_ms",  # changes every ms
    "source",
    "input_suppressed_reason",
    "mount_action",
})


def normalize_state_key(state_features: dict[str, Any]) -> str:
    """Build a deterministic hashable state key from decision-relevant features.

    Continuous floats (brightness, contrast) are bucketed to one decimal place so
    states seen in different frames can actually match each other in the lookup table.
    Metadata fields that change every iteration (frame size, lock timers) are excluded.
    """
    filtered: dict[str, Any] = {}
    for k, v in state_features.items():
        if k in _STATE_KEY_EXCLUDE:
            continue
        # Bucket floats to 1 decimal place — without this, brightness=0.3412 and
        # brightness=0.3413 are treated as completely different states and never match.
        if isinstance(v, float):
            v = round(v, 1)
        filtered[k] = v
    return json.dumps(filtered, sort_keys=True, separators=(",", ":"))


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

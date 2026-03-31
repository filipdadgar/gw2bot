"""Offline trainer for policy-signal based action recommendation."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.core.training.policy_signal_dataset import PolicySignalSample, normalize_state_key


class PolicyTrainer:
    """Trains and serializes a simple reward-aggregated policy table."""

    def train(self, samples: list[PolicySignalSample]) -> dict[str, Any]:
        if not samples:
            raise ValueError("no_policy_samples")

        grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        action_rewards: dict[str, list[float]] = defaultdict(list)

        for sample in samples:
            grouped[sample.state_key][sample.action_taken].append(sample.reward_proxy)
            action_rewards[sample.action_taken].append(sample.reward_proxy)

        action_stats = {
            action: {
                "count": len(rewards),
                "avg_reward": (sum(rewards) / len(rewards)),
            }
            for action, rewards in action_rewards.items()
        }
        default_action = max(action_stats.items(), key=lambda item: item[1]["avg_reward"])[0]

        state_action_values: dict[str, dict[str, dict[str, float | int]]] = {}
        for state_key, action_map in grouped.items():
            state_action_values[state_key] = {
                action: {
                    "count": len(rewards),
                    "avg_reward": (sum(rewards) / len(rewards)),
                }
                for action, rewards in action_map.items()
            }

        return {
            "model_id": f"policy-{uuid4().hex[:8]}",
            "trained_at_utc": datetime.now(UTC).isoformat(),
            "sample_count": len(samples),
            "action_count": len(action_stats),
            "default_action": default_action,
            "action_stats": action_stats,
            "state_action_values": state_action_values,
        }

    def save_artifact(self, artifact: dict[str, Any], target: Path) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
        return target

    def recommend(self, artifact: dict[str, Any], state_features: dict[str, Any]) -> dict[str, Any]:
        state_key = normalize_state_key(state_features)
        table = artifact.get("state_action_values", {})
        default_action = artifact["default_action"]
        model_id = artifact["model_id"]

        action_values = table.get(state_key)
        if not isinstance(action_values, dict) or not action_values:
            return {
                "action": default_action,
                "confidence": 0.5,
                "model_id": model_id,
            }

        best_action = max(action_values.items(), key=lambda item: float(item[1]["avg_reward"]))[0]

        rewards = [float(v["avg_reward"]) for v in action_values.values()]
        max_reward = max(rewards)
        min_reward = min(rewards)
        if max_reward == min_reward:
            confidence = 1.0 / len(rewards)
        else:
            confidence = (float(action_values[best_action]["avg_reward"]) - min_reward) / (max_reward - min_reward)

        return {
            "action": best_action,
            "confidence": round(confidence, 4),
            "model_id": model_id,
        }

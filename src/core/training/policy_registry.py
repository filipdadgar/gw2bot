"""Policy artifact registry and convenience operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.persistence.storage import Storage
from src.core.training.policy_signal_dataset import PolicySignalDataset
from src.core.training.policy_trainer import PolicyTrainer


class PolicyRegistry:
    """Manages training and retrieval of latest policy artifacts."""

    def __init__(self, storage: Storage, trainer: PolicyTrainer | None = None) -> None:
        self._storage = storage
        self._trainer = trainer or PolicyTrainer()
        self._dataset = PolicySignalDataset(self._storage.telemetry_dir / "policy-signals.jsonl")
        self._latest_artifact_path = self._storage.models_dir / "policy-latest.json"

    def train_latest(self) -> dict[str, Any]:
        samples = self._dataset.load_samples()
        artifact = self._trainer.train(samples)
        versioned_path = self._storage.models_dir / f"{artifact['model_id']}.json"
        self._trainer.save_artifact(artifact, versioned_path)
        self._trainer.save_artifact(artifact, self._latest_artifact_path)
        return {
            "model_id": artifact["model_id"],
            "sample_count": artifact["sample_count"],
            "action_count": artifact["action_count"],
            "default_action": artifact["default_action"],
            "artifact_path": str(self._latest_artifact_path),
            "trained_at_utc": artifact["trained_at_utc"],
        }

    def list_versions(self) -> list[dict[str, Any]]:
        versions: list[dict[str, Any]] = []
        for candidate in self._storage.models_dir.glob("policy-*.json"):
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            model_id = payload.get("model_id")
            trained_at = payload.get("trained_at_utc")
            if not isinstance(model_id, str) or not isinstance(trained_at, str):
                continue
            versions.append(
                {
                    "model_id": model_id,
                    "trained_at_utc": trained_at,
                    "sample_count": int(payload.get("sample_count", 0)),
                    "artifact_path": str(candidate),
                }
            )
        versions.sort(key=lambda item: item["trained_at_utc"], reverse=True)
        return versions

    def has_artifact(self) -> bool:
        return self._latest_artifact_path.exists()

    def load_latest(self) -> dict[str, Any]:
        if not self._latest_artifact_path.exists():
            raise FileNotFoundError("policy_artifact_missing")
        return json.loads(self._latest_artifact_path.read_text(encoding="utf-8"))

    def recommend(self, state_features: dict[str, Any]) -> dict[str, Any]:
        artifact = self.load_latest()
        return self._trainer.recommend(artifact=artifact, state_features=state_features)

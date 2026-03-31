from pathlib import Path

from src.core.training.policy_signal_dataset import PolicySignalSample
from src.core.training.policy_trainer import PolicyTrainer


def test_policy_trainer_builds_artifact() -> None:
    trainer = PolicyTrainer()
    samples = [
        PolicySignalSample(state_key='{"distance":0.1}', action_taken="harvest", reward_proxy=1.0),
        PolicySignalSample(state_key='{"distance":0.1}', action_taken="navigate", reward_proxy=0.1),
        PolicySignalSample(state_key='{"distance":0.4}', action_taken="navigate", reward_proxy=0.7),
    ]

    artifact = trainer.train(samples)

    assert artifact["sample_count"] == 3
    assert artifact["action_count"] == 2
    assert artifact["default_action"] in {"harvest", "navigate"}


def test_policy_trainer_recommend_and_save(tmp_path: Path) -> None:
    trainer = PolicyTrainer()
    samples = [
        PolicySignalSample(state_key='{"distance":0.1}', action_taken="harvest", reward_proxy=1.0),
        PolicySignalSample(state_key='{"distance":0.1}', action_taken="navigate", reward_proxy=0.2),
    ]
    artifact = trainer.train(samples)

    target = tmp_path / "policy.json"
    trainer.save_artifact(artifact, target)

    assert target.exists()

    recommendation = trainer.recommend(artifact, {"distance": 0.1})
    assert recommendation["action"] == "harvest"
    assert 0 <= recommendation["confidence"] <= 1

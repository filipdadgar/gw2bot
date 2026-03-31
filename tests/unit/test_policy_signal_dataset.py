from pathlib import Path

from src.core.training.policy_signal_dataset import PolicySignalDataset, normalize_state_key


def test_normalize_state_key_is_order_stable() -> None:
    left = normalize_state_key({"b": 1, "a": {"y": 2, "x": 3}})
    right = normalize_state_key({"a": {"x": 3, "y": 2}, "b": 1})
    assert left == right


def test_dataset_loader_filters_invalid_rows(tmp_path: Path) -> None:
    signals = tmp_path / "policy-signals.jsonl"
    signals.write_text(
        "\n".join(
            [
                '{"state_features":{"distance":0.2},"action_taken":"navigate","reward_proxy":0.3}',
                '{"state_features":"bad","action_taken":"navigate","reward_proxy":0.3}',
                '{"state_features":{"distance":0.1},"action_taken":"harvest","reward_proxy":"oops"}',
            ]
        ),
        encoding="utf-8",
    )

    dataset = PolicySignalDataset(signals)
    samples = dataset.load_samples()

    assert len(samples) == 1
    assert samples[0].action_taken == "navigate"
    assert samples[0].reward_proxy == 0.3

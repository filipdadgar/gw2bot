from pathlib import Path

from src.cli.retrain_scheduler import main


def test_scheduler_once_trains_from_existing_signals(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    telemetry_dir = data_dir / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    signals = telemetry_dir / "policy-signals.jsonl"
    signals.write_text(
        "\n".join(
            [
                '{"state_features":{"distance":0.2},"action_taken":"navigate","reward_proxy":0.2}',
                '{"state_features":{"distance":0.1},"action_taken":"harvest","reward_proxy":1.0}',
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["--data-dir", str(data_dir), "--once"])

    assert exit_code == 0
    assert (data_dir / "models" / "policy-latest.json").exists()

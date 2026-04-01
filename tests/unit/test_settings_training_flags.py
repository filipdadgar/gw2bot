from src.config.settings import get_settings


def test_training_auto_retrain_settings(monkeypatch) -> None:
    monkeypatch.setenv("GW2_TRAINING_AUTO_RETRAIN_ENABLED", "true")
    monkeypatch.setenv("GW2_TRAINING_RETRAIN_INTERVAL_SECONDS", "123")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.gw2_training_auto_retrain_enabled is True
    assert settings.gw2_training_retrain_interval_seconds == 123


def test_runtime_policy_settings(monkeypatch) -> None:
    monkeypatch.setenv("GW2_RUNTIME_POLICY_ENABLED", "true")
    monkeypatch.setenv("GW2_RUNTIME_INPUT_ENABLED", "true")
    monkeypatch.setenv("GW2_RUNTIME_MOUNT_CYCLE_ENABLED", "true")
    monkeypatch.setenv("GW2_RUNTIME_WAYPOINT_STEERING_ENABLED", "true")
    monkeypatch.setenv("GW2_RUNTIME_GATHER_LOCK_SECONDS", "2.0")
    monkeypatch.setenv("GW2_RUNTIME_GATHER_PROMPT_LATCH_SECONDS", "2.5")
    monkeypatch.setenv("GW2_RUNTIME_POLICY_MIN_CONFIDENCE", "0.8")
    monkeypatch.setenv("GW2_RUNTIME_SIGNAL_INTERVAL_MS", "250")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.gw2_runtime_policy_enabled is True
    assert settings.gw2_runtime_input_enabled is True
    assert settings.gw2_runtime_mount_cycle_enabled is True
    assert settings.gw2_runtime_waypoint_steering_enabled is True
    assert settings.gw2_runtime_gather_lock_seconds == 2.0
    assert settings.gw2_runtime_gather_prompt_latch_seconds == 2.5
    assert settings.gw2_runtime_policy_min_confidence == 0.8
    assert settings.gw2_runtime_signal_interval_ms == 250


def test_autostart_run_settings(monkeypatch) -> None:
    monkeypatch.setenv("GW2_AUTOSTART_RUN_ENABLED", "true")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.gw2_autostart_run_enabled is True

from fastapi.testclient import TestClient

from src.config.settings import get_settings
from src.api.main import create_app


def test_training_train_contract(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GW2_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    client.post("/v1/run/start", json={"auto_discover_if_missing": True})

    response = client.post("/v1/training/policy/train")

    assert response.status_code == 200
    body = response.json()
    assert "model_id" in body
    assert body["sample_count"] >= 1


def test_run_start_generates_trainable_signals(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GW2_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    client = TestClient(create_app())

    run_response = client.post("/v1/run/start", json={"auto_discover_if_missing": True})
    assert run_response.status_code == 202

    train_response = client.post("/v1/training/policy/train")
    assert train_response.status_code == 200
    assert train_response.json()["sample_count"] >= 1


def test_run_start_with_runtime_policy_enabled(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GW2_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("GW2_RUNTIME_POLICY_ENABLED", "true")
    monkeypatch.setenv("GW2_RUNTIME_SIGNAL_INTERVAL_MS", "100")
    get_settings.cache_clear()
    client = TestClient(create_app())

    run_response = client.post("/v1/run/start", json={"auto_discover_if_missing": True})
    assert run_response.status_code == 202

    train_response = client.post("/v1/training/policy/train")
    assert train_response.status_code == 200
    assert train_response.json()["sample_count"] >= 1


def test_training_recommend_contract(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GW2_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    client.post("/v1/run/start", json={"auto_discover_if_missing": True})
    client.post("/v1/training/policy/train")

    response = client.post(
        "/v1/training/policy/recommend",
        json={"state_features": {"distance": 0.2, "confidence": 0.8, "rarity": 0.7}},
    )

    assert response.status_code == 200
    body = response.json()
    assert "action" in body
    assert 0 <= body["confidence"] <= 1
    assert "model_id" in body


def test_training_versions_contract(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GW2_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    client.post("/v1/run/start", json={"auto_discover_if_missing": True})
    client.post("/v1/training/policy/train")

    response = client.get("/v1/training/policy/versions")

    assert response.status_code == 200
    body = response.json()
    assert "latest_model_id" in body
    assert isinstance(body["versions"], list)
    assert body["versions"]


def test_demonstration_capture_contract(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GW2_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    client = TestClient(create_app())

    start_response = client.post("/v1/training/demonstrations/start")
    assert start_response.status_code == 200
    session = start_response.json()
    assert session["session_id"].startswith("demo-")
    assert session["active"] is True
    assert session["auto_capture_enabled"] is False

    record_response = client.post(
        "/v1/training/demonstrations/record",
        json={"action_taken": "harvest", "reward_proxy": 1.0},
    )
    assert record_response.status_code == 200
    signal = record_response.json()
    assert signal["action_taken"] == "harvest"
    assert signal["cycle_id"].startswith("demo-")

    stop_response = client.post("/v1/training/demonstrations/stop")
    assert stop_response.status_code == 200
    ended = stop_response.json()
    assert ended["active"] is False
    assert ended["auto_capture_enabled"] is False


def test_demonstration_capture_auto_listener_enabled(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GW2_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("GW2_DEMO_AUTO_CAPTURE_ENABLED", "true")
    get_settings.cache_clear()

    app = create_app()

    class _StubListener:
        def __init__(self) -> None:
            self.started = False
            self.stopped = False

        def start(self) -> bool:
            self.started = True
            return True

        def stop(self) -> None:
            self.stopped = True

    stub_listener = _StubListener()
    app.state.manual_input_listener = stub_listener
    client = TestClient(app)

    start_response = client.post("/v1/training/demonstrations/start")
    assert start_response.status_code == 200
    assert start_response.json()["auto_capture_enabled"] is True
    assert stub_listener.started is True

    stop_response = client.post("/v1/training/demonstrations/stop")
    assert stop_response.status_code == 200
    assert stop_response.json()["auto_capture_enabled"] is False
    assert stub_listener.stopped is True


def test_demonstration_record_requires_active_session(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GW2_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post(
        "/v1/training/demonstrations/record",
        json={"action_taken": "navigate", "reward_proxy": 0.2},
    )

    assert response.status_code == 409

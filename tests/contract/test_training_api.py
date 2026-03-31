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

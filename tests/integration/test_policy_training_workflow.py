from fastapi.testclient import TestClient

from src.config.settings import get_settings
from src.api.main import create_app


def test_policy_training_workflow_end_to_end(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GW2_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    client = TestClient(create_app())

    start = client.post("/v1/run/start", json={"auto_discover_if_missing": True})
    assert start.status_code == 202

    train = client.post("/v1/training/policy/train")
    assert train.status_code == 200
    train_body = train.json()
    assert train_body["sample_count"] >= 1

    recommend = client.post(
        "/v1/training/policy/recommend",
        json={"state_features": {"distance": 0.15, "confidence": 0.9, "rarity": 0.8}},
    )
    assert recommend.status_code == 200
    body = recommend.json()
    assert body["action"]
    assert 0 <= body["confidence"] <= 1

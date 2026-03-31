from fastapi.testclient import TestClient

from src.api.main import create_app


def test_pause_resume_lifecycle_flow() -> None:
    client = TestClient(create_app())

    started = client.post("/v1/run/start", json={"auto_discover_if_missing": True})
    assert started.status_code == 202
    assert started.json()["status"] == "running"

    paused = client.post("/v1/run/pause")
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"

    resumed = client.post("/v1/run/resume")
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "running"

from fastapi.testclient import TestClient

from src.api.main import create_app


def test_pause_resume_stop_contract() -> None:
    client = TestClient(create_app())

    start = client.post("/v1/run/start", json={"auto_discover_if_missing": True})
    assert start.status_code == 202

    pause = client.post("/v1/run/pause")
    assert pause.status_code in {200, 409}
    if pause.status_code == 200:
        assert pause.json()["status"] == "paused"

    resume = client.post("/v1/run/resume")
    assert resume.status_code in {200, 409}
    if resume.status_code == 200:
        assert resume.json()["status"] == "running"

    stop = client.post("/v1/run/stop")
    assert stop.status_code == 200
    assert stop.json()["status"] in {"stopping", "idle"}

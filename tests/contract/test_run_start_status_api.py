from fastapi.testclient import TestClient

from src.api.main import create_app


def test_run_start_contract() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/run/start",
        json={"auto_discover_if_missing": True, "loop_enabled": True},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] in {"running", "paused", "idle", "stopping", "error"}
    assert "current_waypoint_index" in body


def test_run_status_contract() -> None:
    client = TestClient(create_app())

    client.post("/v1/run/start", json={"auto_discover_if_missing": True})
    response = client.get("/v1/run/status")

    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert isinstance(body["current_waypoint_index"], int)

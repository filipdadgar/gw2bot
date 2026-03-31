from fastapi.testclient import TestClient

from src.api.main import create_app


def test_discovery_start_contract() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/discovery/start",
        json={"max_duration_seconds": 120, "min_loop_confidence": 0.75},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] in {"running", "completed", "failed", "idle", "stopping"}
    assert "discovery_id" in body


def test_discovery_status_contract() -> None:
    client = TestClient(create_app())

    start = client.post("/v1/discovery/start", json={})
    assert start.status_code == 202

    response = client.get("/v1/discovery/status")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "generated_route_id" in body


def test_discovery_stop_contract() -> None:
    client = TestClient(create_app())

    client.post("/v1/discovery/start", json={})
    response = client.post("/v1/discovery/stop")

    assert response.status_code == 200
    assert response.json()["status"] in {"stopping", "idle", "failed"}

from fastapi.testclient import TestClient

from src.api.main import create_app


def test_cycle_summary_contract() -> None:
    client = TestClient(create_app())

    start = client.post("/v1/run/start", json={"auto_discover_if_missing": True})
    assert start.status_code == 202
    cycle_id = start.json()["cycle_id"]

    response = client.get(f"/v1/telemetry/cycles/{cycle_id}/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["cycle_id"] == cycle_id
    assert "capture_to_decision_median_ms" in body
    assert "capture_to_decision_p95_ms" in body

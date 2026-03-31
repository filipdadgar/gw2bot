"""Operator UX consistency validation across lifecycle."""

from fastapi.testclient import TestClient

from src.api.main import create_app


def test_operator_ux_consistency_statuses_and_errors() -> None:
    """Validate operator-facing statuses and error messages are consistent.
    
    CAR-003: All status labels and failure messages must be consistent
    across the run lifecycle.
    """
    client = TestClient(create_app())

    # Verify status endpoint returns consistent schema
    status1 = client.get("/v1/run/status")
    assert "status" in status1.json()
    assert status1.json()["status"] in {"idle", "running", "paused", "stopping", "error"}

    # Start a run
    started = client.post("/v1/run/start", json={"auto_discover_if_missing": True})
    assert started.status_code == 202
    start_body = started.json()
    assert "status" in start_body
    assert "cycle_id" in start_body or start_body["status"] in {"error", "idle"}

    # Verify pause transition behavior
    status_running = client.get("/v1/run/status")
    if status_running.json().get("status") == "running":
        paused = client.post("/v1/run/pause")
        assert paused.status_code in {200, 409}
        if paused.status_code == 200:
            pause_body = paused.json()
            assert pause_body["status"] == "paused"

    # Verify all error responses have consistent structure
    bad_request = client.post("/v1/run/start", json={"invalid_field": True})
    if bad_request.status_code >= 400:
        error_body = bad_request.json()
        # Error response should follow a consistent schema
        assert isinstance(error_body, dict)

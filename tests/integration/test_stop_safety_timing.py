from time import perf_counter

from fastapi.testclient import TestClient

from src.api.main import create_app


def test_stop_latency_under_250ms() -> None:
    client = TestClient(create_app())
    client.post("/v1/run/start", json={"auto_discover_if_missing": True})

    start = perf_counter()
    stopped = client.post("/v1/run/stop")
    elapsed = perf_counter() - start

    assert stopped.status_code == 200
    assert stopped.json()["status"] == "stopping"
    assert elapsed <= 0.25

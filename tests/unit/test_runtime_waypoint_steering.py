from pathlib import Path

from src.core.orchestration.farm_cycle_orchestrator import FarmCycleOrchestrator
from src.core.persistence.storage import Storage


class _DiscoveryStub:
    def start(self):
        return {"generated_route_id": "route-test"}


def test_load_route_waypoints_returns_empty_for_invalid_file(tmp_path: Path) -> None:
    route_file = tmp_path / "invalid-route.json"
    route_file.write_text("{not-json", encoding="utf-8")

    waypoints = FarmCycleOrchestrator._load_route_waypoints(route_file)

    assert waypoints == []


def test_compute_route_direction_bias_uses_waypoint_dx(tmp_path: Path) -> None:
    storage = Storage(str(tmp_path))
    orchestrator = FarmCycleOrchestrator(storage=storage, discovery_orchestrator=_DiscoveryStub())
    orchestrator._runtime_waypoint_steering_enabled = True
    orchestrator._runtime_waypoints = [
        {"x": 100, "y": 100},
        {"x": 130, "y": 100},
        {"x": 120, "y": 100},
    ]

    assert orchestrator._compute_route_direction_bias(step_index=0) == 1
    assert orchestrator._compute_route_direction_bias(step_index=6) == -1


def test_compute_route_direction_bias_disabled_returns_neutral(tmp_path: Path) -> None:
    storage = Storage(str(tmp_path))
    orchestrator = FarmCycleOrchestrator(storage=storage, discovery_orchestrator=_DiscoveryStub())
    orchestrator._runtime_waypoint_steering_enabled = False
    orchestrator._runtime_waypoints = [
        {"x": 100, "y": 100},
        {"x": 140, "y": 100},
    ]

    assert orchestrator._compute_route_direction_bias(step_index=0) == 0

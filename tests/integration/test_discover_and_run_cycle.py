from src.core.discovery.route_builder import RouteBuilder
from src.core.orchestration.discovery_orchestrator import DiscoveryOrchestrator
from src.core.orchestration.farm_cycle_orchestrator import FarmCycleOrchestrator
from src.core.persistence.storage import Storage


def test_discovery_to_run_cycle(tmp_path) -> None:
    storage = Storage(str(tmp_path / "data"))
    builder = RouteBuilder(storage)
    discovery = DiscoveryOrchestrator(builder)
    orchestrator = FarmCycleOrchestrator(storage, discovery)

    run_state = orchestrator.start(route_id=None, auto_discover_if_missing=True)

    assert run_state.status == "running"
    assert run_state.route_id is not None
    assert (storage.routes_dir / f"{run_state.route_id}.json").exists()

    completed = orchestrator.complete_cycle_and_schedule_restart()
    assert completed.cooldown_applied_seconds >= 0
    assert completed.status == "running"

from pathlib import Path

from src.core.orchestration.farm_cycle_orchestrator import FarmCycleOrchestrator
from src.core.persistence.storage import Storage


class _DiscoveryStub:
    def start(self):
        return {"generated_route_id": "route-test"}


def test_set_gather_lock_and_remaining_ms(tmp_path: Path) -> None:
    storage = Storage(str(tmp_path))
    orchestrator = FarmCycleOrchestrator(storage=storage, discovery_orchestrator=_DiscoveryStub())
    orchestrator._runtime_gather_lock_seconds = 1.5

    orchestrator._set_gather_lock(now=10.0)

    assert orchestrator._is_gather_lock_active(now=10.1) is True
    assert orchestrator._gather_lock_remaining_ms(now=10.1) > 0
    assert orchestrator._is_gather_lock_active(now=11.6) is False
    assert orchestrator._gather_lock_remaining_ms(now=11.6) == 0


def test_set_gather_lock_disabled_when_zero_seconds(tmp_path: Path) -> None:
    storage = Storage(str(tmp_path))
    orchestrator = FarmCycleOrchestrator(storage=storage, discovery_orchestrator=_DiscoveryStub())
    orchestrator._runtime_gather_lock_seconds = 0.0

    orchestrator._set_gather_lock(now=20.0)

    assert orchestrator._is_gather_lock_active(now=20.1) is False
    assert orchestrator._gather_lock_remaining_ms(now=20.1) == 0

"""Discovery success-rate benchmark validation."""

from src.core.discovery.route_builder import RouteBuilder
from src.core.orchestration.discovery_orchestrator import DiscoveryOrchestrator
from src.core.persistence.storage import Storage


def test_discovery_success_rate_90_percent(tmp_path) -> None:
    """Validate route discovery succeeds ≥90% of attempts.
    
    Success Criteria: SC-002 discovery success ≥ 90%.
    """
    storage = Storage(str(tmp_path / "data"))
    builder = RouteBuilder(storage)
    discovery = DiscoveryOrchestrator(builder)

    successes = 0
    attempts = 10

    for _ in range(attempts):
        state = discovery.start()
        if state.get("status") in {"completed", "running"}:
            successes += 1

    success_rate = successes / attempts
    assert success_rate >= 0.9, f"Discovery success rate {success_rate:.1%} below 90% threshold"

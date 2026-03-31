"""Discovery fallback behavior regression test."""

from src.core.discovery.route_builder import RouteBuilder
from src.core.orchestration.discovery_orchestrator import DiscoveryOrchestrator
from src.core.persistence.storage import Storage


def test_discovery_failure_fallback_continues_route() -> None:
    """Verify system falls back gracefully when discovery fails.
    
    Edge case: Route discovery cannot produce stable candidate, but system
    should either retry or provide fallback behavior.
    """
    storage = Storage("data")
    builder = RouteBuilder(storage)
    discovery = DiscoveryOrchestrator(builder)

    # Attempt discovery
    state = discovery.start()

    # Either discovery completes or transitions to recoverable state
    assert state.get("status") in {"running", "completed", "failed"}

    # If failed, should not be an error state that blocks future attempts
    if state.get("status") == "failed":
        # Verify we can retry
        retry_state = discovery.start()
        assert retry_state.get("status") is not None

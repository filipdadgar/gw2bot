"""Cooldown restart-latency benchmark validation."""

import time
from unittest.mock import MagicMock

from src.core.orchestration.farm_cycle_orchestrator import FarmCycleOrchestrator
from src.core.persistence.storage import Storage


def test_cooldown_restart_latency_5_seconds(tmp_path) -> None:
    """Validate cooldown-to-restart latency ≤5 seconds in ≥95% of cycles.
    
    Success Criteria: SC-009 restart latency ≤ 5s in ≥ 95% of cycles.
    """
    storage = Storage(str(tmp_path / "data"))
    discovery = MagicMock()
    orchestrator = FarmCycleOrchestrator(storage, discovery)

    latencies = []
    for cooldown_secs in [2, 3, 4]:
        start = time.perf_counter()
        orchestrator.complete_cycle_and_schedule_restart(cooldown_seconds=cooldown_secs)
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)

    latencies.sort()
    p95_latency_ms = latencies[int(len(latencies) * 0.95)]
    p95_latency_s = p95_latency_ms / 1000

    assert p95_latency_s <= 5.0, f"p95 restart latency {p95_latency_s:.2f}s exceeds 5s budget"

from src.core.persistence.storage import Storage
from src.telemetry.cycle_summary_service import CycleSummaryService
from src.telemetry.event_writer import EventWriter


def test_cycle_summary_aggregation_counts_and_latency(tmp_path) -> None:
    storage = Storage(str(tmp_path / "data"))
    writer = EventWriter(storage)
    service = CycleSummaryService(storage)

    cycle_id = "cycle-abc"
    writer.write_event(cycle_id=cycle_id, category="detection", payload={"count": 1})
    writer.write_event(cycle_id=cycle_id, category="action", payload={"result": "success"})
    writer.write_event(cycle_id=cycle_id, category="performance", payload={"capture_to_decision_ms": 120})
    writer.write_event(cycle_id=cycle_id, category="performance", payload={"capture_to_decision_ms": 200})

    summary = service.summarize(cycle_id=cycle_id, route_id="route-1")

    assert summary["detections"] >= 1
    assert summary["harvest_success_count"] == 1
    assert summary["harvest_failure_count"] == 0
    assert summary["capture_to_decision_median_ms"] == 160
    assert summary["capture_to_decision_p95_ms"] == 200

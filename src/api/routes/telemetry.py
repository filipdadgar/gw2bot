"""Telemetry summary endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/v1/telemetry", tags=["telemetry"])


@router.get("/cycles/{cycle_id}/summary")
def get_cycle_summary(cycle_id: str, request: Request) -> dict[str, object]:
    snapshot = request.app.state.farm_cycle_orchestrator.status()
    if snapshot.cycle_id != cycle_id:
        raise HTTPException(status_code=404, detail={"code": "cycle_not_found"})

    service = request.app.state.cycle_summary_service
    summary = service.summarize(cycle_id=cycle_id, route_id=snapshot.route_id)
    return summary

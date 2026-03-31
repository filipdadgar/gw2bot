"""Run start and status endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/run", tags=["run"])


class StartRunRequest(BaseModel):
    route_id: str | None = None
    auto_discover_if_missing: bool = True
    loop_enabled: bool = True
    cooldown_override_seconds: int | None = Field(default=None, ge=0)


def _snapshot_to_response(snapshot) -> dict[str, object]:
    return {
        "cycle_id": snapshot.cycle_id,
        "route_id": snapshot.route_id,
        "status": snapshot.status,
        "current_waypoint_index": snapshot.current_waypoint_index,
        "started_at_utc": snapshot.started_at_utc,
        "last_error": snapshot.last_error,
    }


@router.post("/start", status_code=202)
def start_run(payload: StartRunRequest, request: Request) -> dict[str, object]:
    orchestrator = request.app.state.farm_cycle_orchestrator
    snapshot = orchestrator.start(
        route_id=payload.route_id,
        auto_discover_if_missing=payload.auto_discover_if_missing,
        loop_enabled=payload.loop_enabled,
        cooldown_override_seconds=payload.cooldown_override_seconds,
    )
    return _snapshot_to_response(snapshot)


@router.get("/status")
def get_run_status(request: Request) -> dict[str, object]:
    orchestrator = request.app.state.farm_cycle_orchestrator
    return _snapshot_to_response(orchestrator.status())

"""Discovery lifecycle endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/discovery", tags=["discovery"])


class StartDiscoveryRequest(BaseModel):
    max_duration_seconds: int = Field(default=600, ge=30)
    min_loop_confidence: float = Field(default=0.7, ge=0.0, le=1.0)


@router.post("/start", status_code=202)
def start_discovery(payload: StartDiscoveryRequest, request: Request) -> dict[str, object]:
    orchestrator = request.app.state.discovery_orchestrator
    return orchestrator.start(
        max_duration_seconds=payload.max_duration_seconds,
        min_loop_confidence=payload.min_loop_confidence,
    )


@router.get("/status")
def get_discovery_status(request: Request) -> dict[str, object]:
    orchestrator = request.app.state.discovery_orchestrator
    return orchestrator.status()


@router.post("/stop")
def stop_discovery(request: Request) -> dict[str, object]:
    orchestrator = request.app.state.discovery_orchestrator
    return orchestrator.stop()

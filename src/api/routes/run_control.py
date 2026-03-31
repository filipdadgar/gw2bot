"""Run control endpoints: pause, resume, stop."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from src.api.routes.run import _snapshot_to_response

router = APIRouter(prefix="/v1/run", tags=["run-control"])


@router.post("/pause")
def pause_run(request: Request) -> dict[str, object]:
    ok, snapshot = request.app.state.control_commands.pause()
    if not ok:
        raise HTTPException(status_code=409, detail={"code": "invalid_transition"})
    return _snapshot_to_response(snapshot)


@router.post("/resume")
def resume_run(request: Request) -> dict[str, object]:
    ok, snapshot = request.app.state.control_commands.resume()
    if not ok:
        raise HTTPException(status_code=409, detail={"code": "invalid_transition"})
    return _snapshot_to_response(snapshot)


@router.post("/stop")
def stop_run(request: Request) -> dict[str, object]:
    _, snapshot = request.app.state.control_commands.stop()
    return _snapshot_to_response(snapshot)

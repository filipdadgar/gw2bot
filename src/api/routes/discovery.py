"""Discovery lifecycle and route-recording endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/discovery", tags=["discovery"])


class StartDiscoveryRequest(BaseModel):
    max_duration_seconds: int = Field(default=600, ge=30)
    min_loop_confidence: float = Field(default=0.7, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Legacy auto-discovery endpoints (stubbed orchestrator)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Manual route recording — fly the path, press F on each node, save.
# ---------------------------------------------------------------------------

@router.post("/record/start", status_code=202)
def start_route_recording(request: Request) -> dict[str, object]:
    """Begin recording player positions.

    Automatically pauses the bot run so it does not send movement keys while
    you are flying the route manually.  Press F on each resource node to add
    a waypoint.  Call /record/stop to save the route when done.
    """
    recorder = getattr(request.app.state, "route_recorder", None)
    if recorder is None:
        return {"ok": False, "error": "route_recorder_unavailable"}

    # Pause the active run so bot keys don't interfere with manual flying.
    orchestrator = getattr(request.app.state, "farm_cycle_orchestrator", None)
    bot_paused = orchestrator.pause() if orchestrator is not None else False

    recorder.start()
    return {"ok": True, "recording": True, "waypoint_count": 0, "bot_paused": bot_paused}


@router.post("/record/stop")
def stop_route_recording(request: Request) -> dict[str, object]:
    """Stop recording, persist the route, and resume the bot run."""
    recorder = getattr(request.app.state, "route_recorder", None)
    if recorder is None:
        return {"ok": False, "error": "route_recorder_unavailable"}

    route_id = recorder.stop_and_save()

    # Resume the bot regardless of save outcome.
    orchestrator = getattr(request.app.state, "farm_cycle_orchestrator", None)
    if orchestrator is not None:
        orchestrator.resume()

    if route_id is None:
        status = recorder.status()
        return {
            "ok": False,
            "error": "too_few_waypoints",
            "waypoint_count": status.waypoint_count,
        }
    return {"ok": True, "route_id": route_id}


@router.post("/record/discard")
def discard_route_recording(request: Request) -> dict[str, object]:
    """Discard the current recording without saving, and resume the bot run."""
    recorder = getattr(request.app.state, "route_recorder", None)
    if recorder is None:
        return {"ok": False, "error": "route_recorder_unavailable"}

    recorder.discard()

    orchestrator = getattr(request.app.state, "farm_cycle_orchestrator", None)
    if orchestrator is not None:
        orchestrator.resume()

    return {"ok": True, "recording": False}


@router.get("/record/status")
def get_route_recording_status(request: Request) -> dict[str, object]:
    """Return whether recording is active and how many waypoints are saved."""
    recorder = getattr(request.app.state, "route_recorder", None)
    if recorder is None:
        return {"recording": False, "waypoint_count": 0, "map_id": 0, "available": False}
    status = recorder.status()
    return {
        "recording": status.recording,
        "waypoint_count": status.waypoint_count,
        "map_id": status.map_id,
        "available": True,
    }


# ---------------------------------------------------------------------------
# MumbleLink live position
# ---------------------------------------------------------------------------

@router.get("/position")
def get_player_position(request: Request) -> dict[str, object]:
    """Return the current MumbleLink player position snapshot.

    mmap_open: whether the shared memory block was successfully opened.
    available: mmap open AND GW2 is in a playable map (tick > 0).
    If mmap_open=true but available=false, GW2 is on character select or loading.
    """
    reader = getattr(request.app.state, "mumble_reader", None)
    if reader is None:
        return {"available": False, "mmap_open": False, "reason": "mumble_disabled"}

    data = reader.read()  # reader retries open internally if needed

    if not reader.available:
        return {"available": False, "mmap_open": False, "reason": "gw2_not_running"}

    if not data.available:
        return {"available": False, "mmap_open": True, "reason": "not_in_map"}

    return {
        "available": True,
        "mmap_open": True,
        "avatar_x": round(data.avatar_x, 2),
        "avatar_y": round(data.avatar_y, 2),
        "avatar_z": round(data.avatar_z, 2),
        "continent_x": round(data.continent_x, 2),
        "continent_y": round(data.continent_y, 2),
        "map_id": data.map_id,
        "is_mounted": data.is_mounted,
        "mount_name": data.mount_name,
        "tick": data.tick,
    }


# ---------------------------------------------------------------------------
# Route listing
# ---------------------------------------------------------------------------

@router.get("/routes")
def list_routes(request: Request) -> dict[str, object]:
    """List all persisted routes ordered by newest first."""
    storage = request.app.state.storage
    from pathlib import Path
    import json

    routes = []
    for f in sorted(
        Path(storage.routes_dir).glob("route-*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ):
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
            routes.append({
                "route_id": payload.get("route_id"),
                "name": payload.get("name"),
                "source": payload.get("source"),
                "map_id": payload.get("map_id", 0),
                "waypoint_count": len(payload.get("waypoints", [])),
                "created_at_utc": payload.get("created_at_utc"),
            })
        except Exception:
            continue
    return {"routes": routes}

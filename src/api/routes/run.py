"""Run start and status endpoints."""

from __future__ import annotations

import numpy as np
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

    if snapshot.status == "running" and snapshot.cycle_id is not None:
        capture_bridge = getattr(request.app.state, "capture_bridge", None)
        input_bridge = getattr(request.app.state, "input_bridge", None)
        bridge_enabled = bool(getattr(request.app.state, "bridge_enabled", False))
        policy_registry = request.app.state.policy_registry
        settings = request.app.state.settings
        interval_seconds = max(0.05, float(settings.gw2_runtime_signal_interval_ms) / 1000.0)

        orchestrator.start_runtime_loop(
            capture_bridge=capture_bridge if bridge_enabled else None,
            input_bridge=input_bridge if bridge_enabled else None,
            policy_registry=policy_registry,
            policy_enabled=bool(settings.gw2_runtime_policy_enabled),
            input_enabled=bool(settings.gw2_runtime_input_enabled),
            mount_cycle_enabled=bool(settings.gw2_runtime_mount_cycle_enabled),
            waypoint_steering_enabled=bool(settings.gw2_runtime_waypoint_steering_enabled),
            gather_lock_seconds=float(settings.gw2_runtime_gather_lock_seconds),
            gather_prompt_latch_seconds=float(settings.gw2_runtime_gather_prompt_latch_seconds),
            policy_min_confidence=float(settings.gw2_runtime_policy_min_confidence),
            interval_seconds=interval_seconds,
            manual_pause_seconds=float(settings.gw2_runtime_manual_pause_seconds),
            mumble_reader=getattr(request.app.state, "mumble_reader", None),
        )

        if bridge_enabled and capture_bridge is not None:
            try:
                frame_capture = capture_bridge.capture()
                frame = frame_capture.frame
                brightness = float(np.mean(frame) / 255.0)
                contrast = float(np.std(frame) / 255.0)
                state_features = {
                    "brightness": round(brightness, 4),
                    "contrast": round(contrast, 4),
                    "frame_width": frame_capture.width,
                    "frame_height": frame_capture.height,
                    "bridge_enabled": 1.0,
                }
                orchestrator.emit_runtime_policy_signal(
                    state_features=state_features,
                    action_taken="navigate",
                    reward_proxy=0.4,
                    terminal=False,
                )
            except Exception:
                orchestrator.seed_policy_signals()
        else:
            orchestrator.seed_policy_signals()

    return _snapshot_to_response(snapshot)


@router.get("/status")
def get_run_status(request: Request) -> dict[str, object]:
    orchestrator = request.app.state.farm_cycle_orchestrator
    return _snapshot_to_response(orchestrator.status())


@router.get("/config")
def get_run_config(request: Request) -> dict[str, object]:
    """Return current runtime settings from the loaded .env configuration."""
    s = request.app.state.settings
    return {
        "policy_enabled": bool(s.gw2_runtime_policy_enabled),
        "input_enabled": bool(s.gw2_runtime_input_enabled),
        "mount_cycle_enabled": bool(s.gw2_runtime_mount_cycle_enabled),
        "waypoint_steering_enabled": bool(s.gw2_runtime_waypoint_steering_enabled),
        "auto_retrain_enabled": bool(s.gw2_training_auto_retrain_enabled),
        "demo_capture_enabled": bool(s.gw2_demo_auto_capture_enabled),
        "mumble_link_enabled": bool(s.gw2_mumble_link_enabled),
        "gather_lock_seconds": float(s.gw2_runtime_gather_lock_seconds),
        "manual_pause_seconds": float(s.gw2_runtime_manual_pause_seconds),
        "signal_interval_ms": int(s.gw2_runtime_signal_interval_ms),
    }

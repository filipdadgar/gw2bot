"""Policy training and inference endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/v1/training", tags=["training"])


class PolicyRecommendRequest(BaseModel):
    state_features: dict[str, Any]


class DemoRecordRequest(BaseModel):
    action_taken: str
    reward_proxy: float = 0.0
    terminal: bool = False
    state_features: dict[str, Any] | None = None


@router.post("/demonstrations/start")
def start_demonstration(request: Request) -> dict[str, object]:
    recorder = request.app.state.demonstration_recorder
    session = recorder.start()
    auto_capture = False
    if bool(request.app.state.settings.gw2_demo_auto_capture_enabled):
        listener = request.app.state.manual_input_listener
        auto_capture = bool(listener.start())
    return {
        "session_id": session.session_id,
        "step_index": session.step_index,
        "active": session.active,
        "auto_capture_enabled": auto_capture,
    }


@router.post("/demonstrations/record")
def record_demonstration(payload: DemoRecordRequest, request: Request) -> dict[str, object]:
    recorder = request.app.state.demonstration_recorder
    try:
        signal = recorder.record(
            action_taken=payload.action_taken,
            reward_proxy=payload.reward_proxy,
            terminal=payload.terminal,
            state_features=payload.state_features,
        )
    except RuntimeError as exc:
        if str(exc) == "demo_session_not_active":
            raise HTTPException(status_code=409, detail={"code": "demo_session_not_active"}) from exc
        raise
    return signal


@router.post("/demonstrations/stop")
def stop_demonstration(request: Request) -> dict[str, object]:
    recorder = request.app.state.demonstration_recorder
    listener = request.app.state.manual_input_listener
    listener.stop()
    session = recorder.stop()
    if session is None:
        raise HTTPException(status_code=409, detail={"code": "demo_session_not_active"})
    return {
        "session_id": session.session_id,
        "step_index": session.step_index,
        "active": session.active,
        "auto_capture_enabled": False,
    }


@router.get("/policy/versions")
def list_policy_versions(request: Request) -> dict[str, object]:
    registry = request.app.state.policy_registry
    versions = registry.list_versions()
    latest = versions[0]["model_id"] if versions else None
    return {"latest_model_id": latest, "versions": versions}


@router.post("/policy/train")
def train_policy(request: Request) -> dict[str, object]:
    registry = request.app.state.policy_registry
    try:
        return registry.train_latest()
    except ValueError as exc:
        if str(exc) == "no_policy_samples":
            raise HTTPException(status_code=409, detail={"code": "policy_signals_missing"}) from exc
        raise


@router.post("/policy/recommend")
def recommend_policy(payload: PolicyRecommendRequest, request: Request) -> dict[str, object]:
    registry = request.app.state.policy_registry
    try:
        return registry.recommend(state_features=payload.state_features)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "policy_artifact_missing"}) from exc

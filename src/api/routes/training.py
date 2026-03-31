"""Policy training and inference endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/v1/training", tags=["training"])


class PolicyRecommendRequest(BaseModel):
    state_features: dict[str, Any]


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

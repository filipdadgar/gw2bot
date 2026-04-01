"""Dashboard-specific telemetry endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Request

router = APIRouter(prefix="/v1/telemetry", tags=["telemetry"])


@router.get("/recent-signals")
def get_recent_signals(request: Request, limit: int = 10) -> dict[str, object]:
    """Get recent policy signals for dashboard display."""
    storage = request.app.state.storage
    signals_file = Path(storage.base_path) / "telemetry" / "policy-signals.jsonl"
    
    signals = []
    if signals_file.exists():
        try:
            with open(signals_file, "r") as f:
                lines = f.readlines()
                # Get the last `limit` lines
                for line in lines[-limit:]:
                    try:
                        signal = json.loads(line)
                        signals.append({
                            "signal_id": signal.get("signal_id"),
                            "timestamp": signal.get("timestamp"),
                            "action_taken": signal.get("action_taken"),
                            "reward_proxy": signal.get("reward_proxy"),
                            "state_features": signal.get("state_features", {}),
                            "confidence": signal.get("confidence"),
                        })
                    except (json.JSONDecodeError, ValueError):
                        continue
        except (IOError, OSError):
            pass
    
    # Return signals in reverse chronological order (newest first)
    return {"signals": list(reversed(signals))}

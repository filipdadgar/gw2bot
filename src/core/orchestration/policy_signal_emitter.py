"""Policy signal emission for future RL integration."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4


class PolicySignalEmitter:
    """Creates normalized policy signal payloads from run steps."""

    def emit(
        self,
        cycle_id: str,
        step_index: int,
        state_features: dict[str, object],
        action_taken: str,
        reward_proxy: float,
        terminal: bool,
        observation_ref: str | None = None,
    ) -> dict[str, object]:
        return {
            "signal_id": f"signal-{uuid4().hex[:10]}",
            "cycle_id": cycle_id,
            "step_index": step_index,
            "observation_ref": observation_ref,
            "state_features": state_features,
            "action_taken": action_taken,
            "reward_proxy": reward_proxy,
            "terminal": terminal,
            "generated_at_utc": datetime.now(UTC).isoformat(),
        }

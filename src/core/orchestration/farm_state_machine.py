"""Base state machine shell for farm run lifecycle orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from src.core.orchestration.state_types import RunState


@dataclass
class FarmStateMachine:
    """Minimal lifecycle model used as a foundation for later phases."""

    state: RunState = RunState.IDLE

    def start(self) -> None:
        if self.state in {RunState.IDLE, RunState.PAUSED}:
            self.state = RunState.RUNNING

    def pause(self) -> None:
        if self.state == RunState.RUNNING:
            self.state = RunState.PAUSED

    def stop(self) -> None:
        if self.state in {RunState.RUNNING, RunState.PAUSED}:
            self.state = RunState.STOPPING

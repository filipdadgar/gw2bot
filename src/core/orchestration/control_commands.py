"""Run control command handlers for pause/resume/stop operations."""

from __future__ import annotations


class ControlCommands:
    """Thin command layer over the farm orchestrator."""

    def __init__(self, farm_orchestrator) -> None:
        self._farm = farm_orchestrator

    def pause(self) -> tuple[bool, object]:
        ok = self._farm.pause()
        return ok, self._farm.status()

    def resume(self) -> tuple[bool, object]:
        ok = self._farm.resume()
        return ok, self._farm.status()

    def stop(self) -> tuple[bool, object]:
        ok = self._farm.stop()
        return ok, self._farm.status()

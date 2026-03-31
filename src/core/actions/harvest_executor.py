"""Harvest input execution with retry policy."""

from __future__ import annotations

from dataclasses import dataclass

from src.adapters.bridge_interfaces import InputBridge


@dataclass(frozen=True)
class HarvestResult:
    success: bool
    retry_count: int
    failure_reason: str | None = None


class HarvestExecutor:
    """Executes harvest actions through the configured input bridge."""

    def __init__(self, bridge: InputBridge) -> None:
        self._bridge = bridge

    def execute(self, x: int, y: int, key: str = "f", max_retries: int = 2) -> HarvestResult:
        """Attempt a harvest action and retry on failure."""

        for retry in range(max_retries + 1):
            try:
                self._bridge.click(x, y)
                self._bridge.press(key)
                return HarvestResult(success=True, retry_count=retry)
            except Exception:  # pragma: no cover - defensive by design
                if retry == max_retries:
                    return HarvestResult(
                        success=False,
                        retry_count=retry,
                        failure_reason="input_bridge_error",
                    )
        return HarvestResult(success=False, retry_count=max_retries, failure_reason="unknown")

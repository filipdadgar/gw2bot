"""Host bridge interfaces for screen capture and input automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class FrameCapture:
    """Container for a captured frame and metadata."""

    frame: np.ndarray
    width: int
    height: int


class CaptureBridge(Protocol):
    """Interface for host-backed frame capture providers."""

    def capture(self) -> FrameCapture:
        """Capture a single frame from the host game client."""


class InputBridge(Protocol):
    """Interface for host-backed input providers."""

    def press(self, key: str) -> None:
        """Send a key press command to the host game client."""

    def click(self, x: int, y: int) -> None:
        """Send a mouse click command to host coordinates."""

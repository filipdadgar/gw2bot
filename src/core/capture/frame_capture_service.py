"""Frame capture service using host bridge adapters."""

from __future__ import annotations

from src.adapters.bridge_interfaces import CaptureBridge, FrameCapture


class FrameCaptureService:
    """Service abstraction for obtaining fresh frames from the host client."""

    def __init__(self, bridge: CaptureBridge) -> None:
        self._bridge = bridge

    def capture_frame(self) -> FrameCapture:
        """Capture and return a frame payload from the configured bridge."""

        return self._bridge.capture()

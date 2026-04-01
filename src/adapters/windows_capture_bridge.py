"""Windows host bridge for screen capture."""

from __future__ import annotations

import logging
from PIL import ImageGrab
import numpy as np
from src.adapters.bridge_interfaces import FrameCapture, CaptureBridge

logger = logging.getLogger(__name__)


def _grab(bbox: tuple[int, int, int, int] | None = None) -> FrameCapture:
    """Capture screen or a region and return as a FrameCapture."""
    img_pil = ImageGrab.grab(bbox=bbox, all_screens=True)
    frame_array = np.array(img_pil, dtype=np.uint8)
    height, width = frame_array.shape[:2]
    return FrameCapture(frame=frame_array, width=width, height=height)


class WindowsCaptureBridge(CaptureBridge):
    """Capture full-screen frames on Windows using PIL.ImageGrab."""

    def __init__(self, monitor_index: int = 0):
        self.monitor_index = monitor_index

    def capture(self) -> FrameCapture:
        try:
            return _grab()
        except Exception as e:
            raise RuntimeError(f"Failed to capture Windows screen: {e}") from e


class WindowsCaptureBridgeWithWindow(CaptureBridge):
    """Capture only the GW2 window region using pygetwindow + PIL.ImageGrab.

    Finds the window by title on every capture so it handles the window being
    moved or resized between calls.  Falls back to full-screen if the window
    cannot be found.
    """

    def __init__(self, window_title: str | None = None):
        self.window_title = window_title
        self._warned_fallback = False

        try:
            import pygetwindow as gw  # noqa: F401 — verify importable at init time
            self._pygetwindow_available = True
        except Exception:
            self._pygetwindow_available = False
            logger.warning("pygetwindow unavailable — capture will use full screen")

    def _find_window_bbox(self) -> tuple[int, int, int, int] | None:
        """Return (left, top, right, bottom) of the target window, or None."""
        if not self._pygetwindow_available or not self.window_title:
            return None
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(self.window_title)
            if not windows:
                return None
            win = windows[0]
            # Skip minimised or zero-size windows
            if win.width <= 0 or win.height <= 0:
                return None
            return (win.left, win.top, win.left + win.width, win.top + win.height)
        except Exception:
            return None

    def capture(self) -> FrameCapture:
        bbox = self._find_window_bbox()
        if bbox is None:
            if not self._warned_fallback:
                logger.warning(
                    "GW2 window '%s' not found — falling back to full-screen capture",
                    self.window_title,
                )
                self._warned_fallback = True
            return _grab()

        self._warned_fallback = False  # reset so we log again if window disappears
        try:
            return _grab(bbox)
        except Exception as e:
            raise RuntimeError(f"Failed to capture window region {bbox}: {e}") from e

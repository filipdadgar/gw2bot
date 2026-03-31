"""macOS host bridge implementation for frame capture."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from PIL import ImageGrab

from src.adapters.bridge_interfaces import CaptureBridge, FrameCapture

logger = logging.getLogger(__name__)


class MacOSCaptureBridge(CaptureBridge):
    """Capture frames from macOS screen using PIL ImageGrab."""

    def __init__(self, window_title: Optional[str] = None, monitor_index: int = 0) -> None:
        """Initialize macOS capture bridge.

        Args:
            window_title: Optional window title to search for (not used in PIL, kept for compatibility)
            monitor_index: Monitor index to capture from (0 = primary)
        """
        self.window_title = window_title
        self.monitor_index = monitor_index
        self._frame_count = 0

    def capture(self) -> FrameCapture:
        """Capture a single frame from the primary macOS display.

        Returns:
            FrameCapture with frame data and dimensions
        """
        try:
            # On macOS, ImageGrab captures the full screen
            # Bbox format: (left, top, right, bottom)
            # None means full screen
            img_pil = ImageGrab.grab()

            # Convert PIL Image to NumPy array (RGB)
            frame_rgb = np.array(img_pil)

            # Get dimensions
            height, width = frame_rgb.shape[:2]

            self._frame_count += 1
            logger.debug(f"Captured frame {self._frame_count}: {width}x{height}")

            return FrameCapture(frame=frame_rgb, width=width, height=height)

        except Exception as e:
            logger.error(f"Frame capture failed: {e}")
            raise


class MacOSCaptureBridgeWithWindow(CaptureBridge):
    """macOS capture bridge that attempts to capture a specific window.

    Note: macOS window-specific capture is more complex (requires Quartz APIs).
    This implementation provides a fallback to full-screen capture.
    """

    def __init__(self, window_title: str) -> None:
        """Initialize with target window title.

        Args:
            window_title: Title of window to capture (e.g., "Guild Wars 2")
        """
        self.window_title = window_title
        self._fallback_bridge = MacOSCaptureBridge()

    def capture(self) -> FrameCapture:
        """Attempt to capture window; fall back to full screen.

        Returns:
            FrameCapture with frame data
        """
        try:
            # Try to import pygetwindow for window finding
            import pygetwindow

            windows = pygetwindow.getWindowsWithTitle(self.window_title)
            if not windows:
                logger.warning(f"Window '{self.window_title}' not found; falling back to full screen")
                return self._fallback_bridge.capture()

            window = windows[0]
            # PIL ImageGrab on macOS doesn't support window-specific capture easily
            # So we fall back to full screen for now
            logger.debug(f"Found window '{self.window_title}'; using full-screen capture")
            return self._fallback_bridge.capture()

        except ImportError:
            logger.warning("pygetwindow not available; falling back to full screen")
            return self._fallback_bridge.capture()
        except Exception as e:
            logger.warning(f"Window-specific capture failed: {e}; falling back to full screen")
            return self._fallback_bridge.capture()

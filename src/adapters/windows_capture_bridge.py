"""Windows host bridge for screen capture.

This module provides screen capture functionality for Windows systems using PIL.ImageGrab.
It implements the CaptureBridge protocol for cross-platform compatibility.

Example:
    >>> from src.adapters.windows_capture_bridge import WindowsCaptureBridge
    >>> bridge = WindowsCaptureBridge()
    >>> frame = bridge.capture()
    >>> print(f"Captured {frame.width}x{frame.height} frame")
"""

import logging
from PIL import ImageGrab
import numpy as np
from src.adapters.bridge_interfaces import FrameCapture, CaptureBridge

logger = logging.getLogger(__name__)


class WindowsCaptureBridge(CaptureBridge):
    """Capture full-screen frames on Windows using PIL.ImageGrab.
    
    Performance: Typically 30-50ms per capture on modern Windows systems.
    
    Attributes:
        monitor_index: Monitor index (currently unused - PIL captures all monitors)
        
    Raises:
        RuntimeError: If screen capture fails or no display is available.
    """

    def __init__(self, monitor_index: int = 0):
        """Initialize Windows capture bridge.
        
        Args:
            monitor_index: Monitor index (default: 0 for primary).
        """
        self.monitor_index = monitor_index
    def capture(self) -> FrameCapture:
        """Capture full-screen and return as RGB NumPy array.
        
        Returns:
            FrameCapture: Dataclass containing:
                - frame: (height, width, 3) uint8 NumPy array in RGB format
                - width: Screen width in pixels
                - height: Screen height in pixels
                
        Raises:
            RuntimeError: If PIL.ImageGrab fails to capture screen.
        """
        try:
            # Capture full screen with PIL - returns PIL Image in RGB
            img_pil = ImageGrab.grab()

            # Convert PIL Image to NumPy array (RGB format)
            frame_array = np.array(img_pil, dtype=np.uint8)

            # Get dimensions
            height, width = frame_array.shape[:2]

            logger.debug(
                f"Captured Windows screen: {width}x{height} "
                f"({frame_array.nbytes / 1024 / 1024:.1f}MB)"
            )

            return FrameCapture(frame=frame_array, width=width, height=height)

        except Exception as e:
            error_msg = f"Failed to capture Windows screen: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e


class WindowsCaptureBridgeWithWindow(CaptureBridge):
    """Capture specific window on Windows (fallback/advanced usage).
    
    Note: PIL.ImageGrab doesn't directly support window captures.
    This class provides fallback behavior by capturing full screen.
    For true window capture on Windows, use pygetwindow + PIL or MSS.
    
    This implementation falls back to full-screen capture.
    """

    def __init__(self, window_title: str | None = None):
        """Initialize window capture bridge.
        
        Args:
            window_title: Target window title (currently unused,
                         falls back to full-screen capture)
        """
        self.window_title = window_title

    def capture(self) -> FrameCapture:
        """Capture screen (currently full-screen on Windows).
        
        Returns:
            FrameCapture: Full-screen capture (see WindowsCaptureBridge.capture)
        """
        # For Windows, PIL.ImageGrab doesn't support window-specific capture
        # Implement using pygetwindow if available, otherwise use full-screen
        logger.debug(
            f"Capturing Windows screen (window filter not supported): {self.window_title}"
        )
        bridge = WindowsCaptureBridge()
        return bridge.capture()

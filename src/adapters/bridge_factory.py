"""Bridge factory and platform detection utility."""

from __future__ import annotations

import logging
import platform
from typing import Optional, Union

from src.adapters.bridge_interfaces import CaptureBridge, InputBridge

logger = logging.getLogger(__name__)


def get_platform() -> str:
    """Get current platform identifier.

    Returns:
        Platform string: 'macos', 'linux', 'windows', or 'unknown'
    """
    system = platform.system().lower()
    return {
        "darwin": "macos",
        "linux": "linux",
        "windows": "windows",
    }.get(system, "unknown")


def get_capture_bridge(
    window_title: Optional[str] = None,
    monitor_index: int = 0,
) -> CaptureBridge:
    """Factory function to get appropriate capture bridge for current platform.

    Args:
        window_title: Optional window title for window-specific capture
        monitor_index: Monitor index (default: 0 for primary)

    Returns:
        Platform-appropriate CaptureBridge implementation

    Raises:
        NotImplementedError: If platform is not yet supported
    """
    plat = get_platform()
    logger.debug(f"Creating capture bridge for platform: {plat}")

    if plat == "macos":
        from src.adapters.macos_capture_bridge import (
            MacOSCaptureBridge,
            MacOSCaptureBridgeWithWindow,
        )

        if window_title:
            return MacOSCaptureBridgeWithWindow(window_title)
        return MacOSCaptureBridge(monitor_index=monitor_index)

    elif plat == "windows":
        try:
            from src.adapters.windows_capture_bridge import (
                WindowsCaptureBridge,
                WindowsCaptureBridgeWithWindow,
            )

            if window_title:
                return WindowsCaptureBridgeWithWindow(window_title)
            return WindowsCaptureBridge(monitor_index=monitor_index)
        except ImportError:
            raise NotImplementedError("Windows bridge not yet implemented")

    elif plat == "linux":
        try:
            from src.adapters.linux_capture_bridge import (
                LinuxCaptureBridge,
                LinuxCaptureBridgeWithWindow,
            )

            if window_title:
                return LinuxCaptureBridgeWithWindow(window_title)
            return LinuxCaptureBridge(monitor_index=monitor_index)
        except ImportError:
            raise NotImplementedError("Linux bridge not yet implemented")

    else:
        raise NotImplementedError(f"Unsupported platform: {plat}")


def get_input_bridge(
    window_title: Optional[str] = None,
) -> InputBridge:
    """Factory function to get appropriate input bridge for current platform.

    Args:
        window_title: Optional window title for focus management

    Returns:
        Platform-appropriate InputBridge implementation

    Raises:
        NotImplementedError: If platform is not yet supported
    """
    plat = get_platform()
    logger.debug(f"Creating input bridge for platform: {plat}")

    if plat == "macos":
        from src.adapters.macos_input_bridge import MacOSInputBridge

        return MacOSInputBridge(window_title=window_title)

    elif plat == "windows":
        try:
            from src.adapters.windows_input_bridge import WindowsInputBridge

            return WindowsInputBridge(window_title=window_title)
        except ImportError:
            raise NotImplementedError("Windows bridge not yet implemented")

    elif plat == "linux":
        try:
            from src.adapters.linux_input_bridge import LinuxInputBridge

            return LinuxInputBridge(window_title=window_title)
        except ImportError:
            raise NotImplementedError("Linux bridge not yet implemented")

    else:
        raise NotImplementedError(f"Unsupported platform: {plat}")


def get_bridges(
    window_title: Optional[str] = None,
    monitor_index: int = 0,
) -> tuple[CaptureBridge, InputBridge]:
    """Factory function to get both capture and input bridges.

    Convenience function to initialize both bridges at once.

    Args:
        window_title: Optional window title
        monitor_index: Monitor index for capture

    Returns:
        Tuple of (CaptureBridge, InputBridge)

    Raises:
        NotImplementedError: If platform or bridge is not yet supported
    """
    return (
        get_capture_bridge(window_title, monitor_index),
        get_input_bridge(window_title),
    )

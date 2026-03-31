"""macOS host bridge implementation for input automation."""

from __future__ import annotations

import logging
import time
from typing import Optional

from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key
from pynput.mouse import Controller as MouseController
from pynput.mouse import Button

from src.adapters.bridge_interfaces import InputBridge

logger = logging.getLogger(__name__)


class MacOSInputBridge(InputBridge):
    """Input automation for macOS using pynput."""

    def __init__(self, window_title: Optional[str] = None, focus_delay: float = 0.1) -> None:
        """Initialize macOS input bridge.

        Args:
            window_title: Optional window title (for focus management, not yet implemented)
            focus_delay: Delay after mouse move before action (avoid race conditions)
        """
        self.window_title = window_title
        self.focus_delay = focus_delay
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self._action_count = 0

    def press(self, key: str) -> None:
        """Send a key press (down + up) to the system.

        Args:
            key: Key name (e.g., 'a', 'enter', 'space', 'shift', 'ctrl')
        """
        try:
            # Map string key names to pynput Key enums
            key_map = {
                "enter": Key.enter,
                "return": Key.enter,
                "space": Key.space,
                "tab": Key.tab,
                "esc": Key.esc,
                "escape": Key.esc,
                "ctrl": Key.ctrl,
                "control": Key.ctrl,
                "shift": Key.shift,
                "alt": Key.alt,
                "cmd": Key.cmd,
                "delete": Key.delete,
                "backspace": Key.backspace,
                "up": Key.up,
                "down": Key.down,
                "left": Key.left,
                "right": Key.right,
            }

            if key in key_map:
                press_key = key_map[key]
            else:
                # Single character key
                press_key = key if len(key) == 1 else key

            self.keyboard.press(press_key)
            time.sleep(0.05)  # Brief hold
            self.keyboard.release(press_key)

            self._action_count += 1
            logger.debug(f"Key pressed: {key} (action #{self._action_count})")

        except Exception as e:
            logger.error(f"Key press failed for '{key}': {e}")
            raise

    def click(self, x: int, y: int, button: str = "left", delay: float = 0.05) -> None:
        """Send a mouse click at specified coordinates.

        Args:
            x: X coordinate (pixels)
            y: Y coordinate (pixels)
            button: Mouse button ("left", "right", "middle")
            delay: Delay between move and click (seconds)
        """
        try:
            # Move mouse to position
            self.mouse.position = (x, y)
            time.sleep(delay)

            # Map button string to pynput Button
            button_map = {
                "left": Button.left,
                "right": Button.right,
                "middle": Button.middle,
            }
            click_button = button_map.get(button, Button.left)

            # Click
            self.mouse.click(click_button, 1)

            self._action_count += 1
            logger.debug(f"Clicked at ({x}, {y}) with {button} button (action #{self._action_count})")

        except Exception as e:
            logger.error(f"Click failed at ({x}, {y}): {e}")
            raise

    def move_mouse(self, x: int, y: int) -> None:
        """Move mouse to specified coordinates.

        Args:
            x: X coordinate (pixels)
            y: Y coordinate (pixels)
        """
        try:
            self.mouse.position = (x, y)
            self._action_count += 1
            logger.debug(f"Mouse moved to ({x}, {y}) (action #{self._action_count})")

        except Exception as e:
            logger.error(f"Mouse move failed to ({x}, {y}): {e}")
            raise

    def type_text(self, text: str, interval: float = 0.05) -> None:
        """Type text character by character.

        Args:
            text: Text to type
            interval: Delay between keystrokes (seconds)
        """
        try:
            # pynput controller.type() doesn't support interval parameter
            for char in text:
                self.keyboard.type(char)
                time.sleep(interval)
            
            self._action_count += 1
            logger.debug(f"Typed text: '{text}' (action #{self._action_count})")

        except Exception as e:
            logger.error(f"Type text failed: {e}")
            raise

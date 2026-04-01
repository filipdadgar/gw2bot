"""Windows host bridge for input automation.

This module provides keyboard and mouse control on Windows systems using pynput.
It implements the InputBridge protocol for cross-platform compatibility.

For accessibility on Windows, pynput should work directly without special permissions
(unlike macOS which requires Accessibility permissions).

Example:
    >>> from src.adapters.windows_input_bridge import WindowsInputBridge
    >>> bridge = WindowsInputBridge()
    >>> bridge.press("enter")
    >>> bridge.click(100, 200)
    >>> bridge.type_text("Hello")
"""

import logging
import time
from typing import Optional
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button
from src.adapters.bridge_interfaces import InputBridge

logger = logging.getLogger(__name__)


class WindowsInputBridge(InputBridge):
    """Control keyboard and mouse input on Windows using pynput.
    
    Performance: Typically 10-20ms per action on modern Windows systems.
    
    Attributes:
        keyboard: pynput KeyboardController instance
        mouse: pynput MouseController instance
    """

    def __init__(self, window_title: Optional[str] = None):
        """Initialize keyboard and mouse controllers.

        Args:
            window_title: Optional target window title for interface compatibility.
                Currently unused on Windows input bridge.
        """
        try:
            self.window_title = window_title
            self.keyboard = KeyboardController()
            self.mouse = MouseController()
            logger.debug("WindowsInputBridge initialized")
        except Exception as e:
            error_msg = f"Failed to initialize Windows input bridge: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def press(self, key: str) -> None:
        """Press a key (for special keys, use lowercase name: enter, space, cmd, shift, ctrl, alt).
        
        Supported special keys:
            enter, space, tab, escape, backspace, delete,
            home, end, page_up, page_down, up, down, left, right,
            f1-f12, shift, ctrl, alt, cmd (windows key)
        
        For single characters, pass the character directly: "a", "1", etc.
        
        Args:
            key: Special key name (lowercase) or single character
            
        Raises:
            ValueError: If key is not recognized
        """
        key_map = {
            "enter": Key.enter,
            "return": Key.enter,
            "space": Key.space,
            "tab": Key.tab,
            "escape": Key.esc,
            "esc": Key.esc,
            "backspace": Key.backspace,
            "delete": Key.delete,
            "home": Key.home,
            "end": Key.end,
            "page_up": Key.page_up,
            "page_down": Key.page_down,
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
            "f1": Key.f1,
            "f2": Key.f2,
            "f3": Key.f3,
            "f4": Key.f4,
            "f5": Key.f5,
            "f6": Key.f6,
            "f7": Key.f7,
            "f8": Key.f8,
            "f9": Key.f9,
            "f10": Key.f10,
            "f11": Key.f11,
            "f12": Key.f12,
            "shift": Key.shift,
            "ctrl": Key.ctrl,
            "alt": Key.alt,
            "cmd": Key.cmd,
            "windows": Key.cmd,
        }

        try:
            if key.lower() in key_map:
                actual_key = key_map[key.lower()]
            else:
                # Treat as single character
                actual_key = key
            
            self.keyboard.press(actual_key)
            logger.debug(f"Pressed key: {key}")
        except Exception as e:
            error_msg = f"Failed to press key '{key}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def release(self, key: str) -> None:
        """Release a key.
        
        Args:
            key: Special key name (lowercase) or single character
        """
        key_map = {
            "enter": Key.enter,
            "return": Key.enter,
            "space": Key.space,
            "tab": Key.tab,
            "escape": Key.esc,
            "esc": Key.esc,
            "backspace": Key.backspace,
            "delete": Key.delete,
            "home": Key.home,
            "end": Key.end,
            "page_up": Key.page_up,
            "page_down": Key.page_down,
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
            "f1": Key.f1,
            "f2": Key.f2,
            "f3": Key.f3,
            "f4": Key.f4,
            "f5": Key.f5,
            "f6": Key.f6,
            "f7": Key.f7,
            "f8": Key.f8,
            "f9": Key.f9,
            "f10": Key.f10,
            "f11": Key.f11,
            "f12": Key.f12,
            "shift": Key.shift,
            "ctrl": Key.ctrl,
            "alt": Key.alt,
            "cmd": Key.cmd,
            "windows": Key.cmd,
        }

        try:
            if key.lower() in key_map:
                actual_key = key_map[key.lower()]
            else:
                actual_key = key
            
            self.keyboard.release(actual_key)
            logger.debug(f"Released key: {key}")
        except Exception as e:
            error_msg = f"Failed to release key '{key}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def click(
        self, x: int, y: int, button: str = "left", count: int = 1, delay: float = 0.1
    ) -> None:
        """Click mouse button at (x, y) position.
        
        Args:
            x: X coordinate in pixels
            y: Y coordinate in pixels
            button: Mouse button ('left', 'right', 'middle') - default 'left'
            count: Number of clicks - default 1
            delay: Delay between clicks in seconds - default 0.1
            
        Raises:
            RuntimeError: If mouse control fails
        """
        button_map = {
            "left": Button.left,
            "right": Button.right,
            "middle": Button.middle,
        }

        try:
            actual_button = button_map.get(button.lower(), Button.left)
            self.mouse.position = (x, y)
            time.sleep(0.05)  # Small delay after moving
            
            for i in range(count):
                self.mouse.click(actual_button)
                if i < count - 1:
                    time.sleep(delay)
            
            logger.debug(f"Clicked {button} button at ({x}, {y}) {count}x")
        except Exception as e:
            error_msg = f"Failed to click at ({x}, {y}): {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def type_text(self, text: str, interval: float = 0.05) -> None:
        """Type text character by character with delay between characters.
        
        Note: pynput's Controller.type() doesn't support interval parameter,
        so we loop through characters and sleep between each one.
        
        Args:
            text: Text to type
            interval: Delay between characters in seconds - default 0.05
            
        Raises:
            RuntimeError: If typing fails
        """
        try:
            for char in text:
                self.keyboard.type(char)
                time.sleep(interval)
            
            logger.debug(f"Typed {len(text)} characters")
        except Exception as e:
            error_msg = f"Failed to type text: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def move_mouse(self, x: int, y: int) -> None:
        """Move mouse to (x, y) position without clicking.
        
        Args:
            x: X coordinate in pixels
            y: Y coordinate in pixels
            
        Raises:
            RuntimeError: If mouse control fails
        """
        try:
            self.mouse.position = (x, y)
            logger.debug(f"Moved mouse to ({x}, {y})")
        except Exception as e:
            error_msg = f"Failed to move mouse to ({x}, {y}): {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

"""Optional host-side manual input listener for demonstration capture."""

from __future__ import annotations

import logging
from typing import Any

try:
    from pynput import keyboard, mouse
except Exception:  # pragma: no cover - environment-dependent import
    keyboard = None  # type: ignore[assignment]
    mouse = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class ManualInputListener:
    """Listens to local keyboard/mouse input and records demo actions."""

    def __init__(self, demonstration_recorder: Any) -> None:
        self._recorder = demonstration_recorder
        self._keyboard_listener = None
        self._mouse_listener = None
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> bool:
        if self._running:
            return True
        if keyboard is None or mouse is None:
            logger.warning("manual_input_listener_unavailable")
            return False

        try:
            self._keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
            self._mouse_listener = mouse.Listener(on_click=self._on_click)
            self._keyboard_listener.start()
            self._mouse_listener.start()
            self._running = True
            return True
        except Exception:
            logger.exception("manual_input_listener_start_failed")
            self._keyboard_listener = None
            self._mouse_listener = None
            self._running = False
            return False

    def stop(self) -> None:
        if self._keyboard_listener is not None:
            try:
                self._keyboard_listener.stop()
            except Exception:
                logger.exception("manual_input_listener_keyboard_stop_failed")
        if self._mouse_listener is not None:
            try:
                self._mouse_listener.stop()
            except Exception:
                logger.exception("manual_input_listener_mouse_stop_failed")

        self._keyboard_listener = None
        self._mouse_listener = None
        self._running = False

    def _on_key_press(self, key: Any) -> None:
        action = self._map_key_to_action(key)
        if action is None:
            return
        self._record_action(action=action)

    def _on_click(self, x: int, y: int, button: Any, pressed: bool) -> None:
        if not pressed:
            return
        action = self._map_click_to_action(button)
        if action is None:
            return
        self._record_action(
            action=action,
            state_features={"click_x": x, "click_y": y},
        )

    def _record_action(self, action: str, state_features: dict[str, object] | None = None) -> None:
        reward_proxy = 0.3
        if action == "harvest":
            reward_proxy = 1.0
        elif action == "interact":
            reward_proxy = 0.8

        try:
            self._recorder.record(
                action_taken=action,
                reward_proxy=reward_proxy,
                terminal=False,
                state_features=state_features,
            )
        except RuntimeError:
            # No active demo session; ignore until session is started.
            return
        except Exception:
            logger.exception("manual_input_listener_record_failed")

    @staticmethod
    def _map_key_to_action(key: Any) -> str | None:
        text = str(key).lower()

        if any(token in text for token in ["'w'", "'a'", "'s'", "'d'", "up", "down", "left", "right"]):
            return "navigate"
        if any(token in text for token in ["space", "enter", "return", "'e'", "'f'"]):
            return "interact"
        if any(token in text for token in ["'r'", "'h'"]):
            return "harvest"
        return None

    @staticmethod
    def _map_click_to_action(button: Any) -> str | None:
        text = str(button).lower()
        if "left" in text:
            return "harvest"
        if "right" in text:
            return "interact"
        return None

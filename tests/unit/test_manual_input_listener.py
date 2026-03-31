from __future__ import annotations

from src.core.training.manual_input_listener import ManualInputListener


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.raise_runtime_error = False

    def record(
        self,
        action_taken: str,
        reward_proxy: float,
        terminal: bool,
        state_features: dict[str, object] | None = None,
    ) -> None:
        if self.raise_runtime_error:
            raise RuntimeError("demo_session_not_active")
        self.calls.append(
            {
                "action_taken": action_taken,
                "reward_proxy": reward_proxy,
                "terminal": terminal,
                "state_features": state_features,
            }
        )


class _DummyListener:
    def __init__(self) -> None:
        self.stop_called = False

    def stop(self) -> None:
        self.stop_called = True


def test_map_key_to_action() -> None:
    assert ManualInputListener._map_key_to_action("'w'") == "navigate"
    assert ManualInputListener._map_key_to_action("Key.left") == "navigate"
    assert ManualInputListener._map_key_to_action("Key.space") == "interact"
    assert ManualInputListener._map_key_to_action("'h'") == "harvest"
    assert ManualInputListener._map_key_to_action("'z'") is None


def test_map_click_to_action() -> None:
    assert ManualInputListener._map_click_to_action("Button.left") == "harvest"
    assert ManualInputListener._map_click_to_action("Button.right") == "interact"
    assert ManualInputListener._map_click_to_action("Button.middle") is None


def test_record_action_ignores_inactive_demo_session() -> None:
    recorder = _Recorder()
    recorder.raise_runtime_error = True
    listener = ManualInputListener(recorder)

    listener._record_action(action="navigate")

    assert recorder.calls == []


def test_on_click_records_coordinates() -> None:
    recorder = _Recorder()
    listener = ManualInputListener(recorder)

    listener._on_click(10, 20, "Button.left", True)

    assert len(recorder.calls) == 1
    assert recorder.calls[0]["action_taken"] == "harvest"
    assert recorder.calls[0]["state_features"] == {"click_x": 10, "click_y": 20}


def test_stop_resets_running_and_listeners() -> None:
    recorder = _Recorder()
    listener = ManualInputListener(recorder)
    keyboard_listener = _DummyListener()
    mouse_listener = _DummyListener()
    listener._keyboard_listener = keyboard_listener
    listener._mouse_listener = mouse_listener
    listener._running = True

    listener.stop()

    assert keyboard_listener.stop_called is True
    assert mouse_listener.stop_called is True
    assert listener.running is False
    assert listener._keyboard_listener is None
    assert listener._mouse_listener is None

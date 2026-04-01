from src.core.orchestration.farm_cycle_orchestrator import FarmCycleOrchestrator


class _InputBridgeStub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def press(self, key: str) -> None:
        self.calls.append(("press", key))

    def release(self, key: str) -> None:
        self.calls.append(("release", key))


class _PressOnlyBridgeStub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def press(self, key: str) -> None:
        self.calls.append(("press", key))


def test_execute_runtime_action_navigate_taps_w_with_release() -> None:
    bridge = _InputBridgeStub()

    FarmCycleOrchestrator._execute_runtime_action(action_taken="navigate", input_bridge=bridge)

    assert bridge.calls[0] == ("press", "w")
    assert bridge.calls[1] == ("release", "w")


def test_execute_runtime_action_navigate_step_with_left_correction() -> None:
    bridge = _InputBridgeStub()

    FarmCycleOrchestrator._execute_runtime_action(action_taken="navigate", input_bridge=bridge, step_index=2)

    assert bridge.calls == [
        ("press", "w"),
        ("release", "w"),
        ("press", "a"),
        ("release", "a"),
    ]


def test_execute_runtime_action_navigate_step_with_right_correction() -> None:
    bridge = _InputBridgeStub()

    FarmCycleOrchestrator._execute_runtime_action(action_taken="navigate", input_bridge=bridge, step_index=4)

    assert bridge.calls == [
        ("press", "w"),
        ("release", "w"),
        ("press", "d"),
        ("release", "d"),
    ]


def test_execute_runtime_action_interact_taps_f_with_release() -> None:
    bridge = _InputBridgeStub()

    FarmCycleOrchestrator._execute_runtime_action(action_taken="interact", input_bridge=bridge)

    assert bridge.calls[0] == ("press", "f")
    assert bridge.calls[1] == ("release", "f")


def test_execute_runtime_action_handles_press_only_bridge() -> None:
    bridge = _PressOnlyBridgeStub()

    FarmCycleOrchestrator._execute_runtime_action(action_taken="harvest", input_bridge=bridge)

    assert bridge.calls == [("press", "f")]


def test_execute_runtime_action_unknown_action_noop() -> None:
    bridge = _InputBridgeStub()

    FarmCycleOrchestrator._execute_runtime_action(action_taken="unknown", input_bridge=bridge)

    assert bridge.calls == []

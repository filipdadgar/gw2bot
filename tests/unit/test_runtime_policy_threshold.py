from src.core.orchestration.farm_cycle_orchestrator import FarmCycleOrchestrator


class _PolicyRegistryStub:
    def __init__(self, confidence: float, action: str = "interact") -> None:
        self._confidence = confidence
        self._action = action

    def has_artifact(self) -> bool:
        return True

    def recommend(self, state_features):
        return {"action": self._action, "confidence": self._confidence}


def test_select_action_uses_policy_when_confident() -> None:
    state = {"brightness": 0.2}
    registry = _PolicyRegistryStub(confidence=0.9, action="interact")

    action = FarmCycleOrchestrator._select_action(
        state_features=state,
        policy_registry=registry,
        policy_enabled=True,
        policy_min_confidence=0.7,
    )

    assert action == "interact"


def test_select_action_falls_back_when_low_confidence() -> None:
    state = {"brightness": 0.8}
    registry = _PolicyRegistryStub(confidence=0.2, action="interact")

    action = FarmCycleOrchestrator._select_action(
        state_features=state,
        policy_registry=registry,
        policy_enabled=True,
        policy_min_confidence=0.7,
    )

    assert action == "harvest"


def test_select_action_uses_fallback_when_policy_disabled() -> None:
    state = {"brightness": 0.1}
    registry = _PolicyRegistryStub(confidence=0.99, action="interact")

    action = FarmCycleOrchestrator._select_action(
        state_features=state,
        policy_registry=registry,
        policy_enabled=False,
        policy_min_confidence=0.7,
    )

    assert action == "navigate"


def test_select_action_forces_harvest_when_gather_prompt_visible() -> None:
    state = {"brightness": 0.1, "gather_prompt_visible": 1.0}
    registry = _PolicyRegistryStub(confidence=0.99, action="navigate")

    action = FarmCycleOrchestrator._select_action(
        state_features=state,
        policy_registry=registry,
        policy_enabled=True,
        policy_min_confidence=0.7,
    )

    assert action == "harvest"

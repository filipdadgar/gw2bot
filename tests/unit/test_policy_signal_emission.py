from src.core.orchestration.policy_signal_emitter import PolicySignalEmitter


def test_policy_signal_emission_shape() -> None:
    emitter = PolicySignalEmitter()

    signal = emitter.emit(
        cycle_id="cycle-1",
        step_index=4,
        state_features={"hp": 0.8},
        action_taken="harvest",
        reward_proxy=1.25,
        terminal=False,
    )

    assert signal["cycle_id"] == "cycle-1"
    assert signal["step_index"] == 4
    assert signal["action_taken"] == "harvest"
    assert signal["terminal"] is False
    assert "generated_at_utc" in signal

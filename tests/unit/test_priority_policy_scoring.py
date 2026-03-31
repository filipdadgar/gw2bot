from src.core.navigation.prioritization_policy import Candidate, PrioritizationPolicy


def test_priority_policy_prefers_higher_score_candidate() -> None:
    policy = PrioritizationPolicy(distance_weight=0.4, confidence_weight=0.6)

    near_low_conf = Candidate(candidate_id="a", distance=5.0, confidence=0.4, rarity=0.2)
    far_high_conf = Candidate(candidate_id="b", distance=9.0, confidence=0.95, rarity=0.2)

    selected = policy.select_best([near_low_conf, far_high_conf])

    assert selected is not None
    assert selected.candidate_id == "b"

from src.core.navigation.prioritization_policy import Candidate, PrioritizationPolicy


def test_dynamic_prioritization_changes_selection_order() -> None:
    candidates = [
        Candidate(candidate_id="normal-near", distance=3.0, confidence=0.65, rarity=0.1),
        Candidate(candidate_id="rich-far", distance=7.0, confidence=0.8, rarity=0.9),
    ]

    baseline = PrioritizationPolicy(distance_weight=0.7, confidence_weight=0.3, rarity_weight=0.0)
    dynamic = PrioritizationPolicy(distance_weight=0.2, confidence_weight=0.3, rarity_weight=0.5)

    baseline_pick = baseline.select_best(candidates)
    dynamic_pick = dynamic.select_best(candidates)

    assert baseline_pick is not None
    assert dynamic_pick is not None
    assert baseline_pick.candidate_id == "normal-near"
    assert dynamic_pick.candidate_id == "rich-far"

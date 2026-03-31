"""Target selector integrates prioritization policy into candidate selection."""

from __future__ import annotations

from typing import Optional

from src.core.navigation.prioritization_policy import Candidate, PrioritizationPolicy


class TargetSelector:
    """Select next harvest target using prioritization policy."""

    def __init__(self, policy: Optional[PrioritizationPolicy] = None) -> None:
        self._policy = policy or PrioritizationPolicy()

    def select_target(self, candidates: list[Candidate]) -> Optional[Candidate]:
        """Use policy to select best target from available candidates."""
        return self._policy.select_best(candidates)

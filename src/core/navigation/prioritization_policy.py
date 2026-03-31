"""Dynamic node prioritization based on configurable policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Candidate:
    """Candidate node with scoring attributes."""

    candidate_id: str
    distance: float
    confidence: float
    rarity: float


class PrioritizationPolicy:
    """Weighted scoring policy for candidate selection."""

    def __init__(
        self,
        distance_weight: float = 0.5,
        confidence_weight: float = 0.3,
        rarity_weight: float = 0.2,
    ) -> None:
        """Initialize policy with configurable weights.

        Args:
            distance_weight: Priority for being close (favor lower distance).
            confidence_weight: Priority for detection confidence.
            rarity_weight: Priority for node rarity/value.
        """
        self.distance_weight = distance_weight
        self.confidence_weight = confidence_weight
        self.rarity_weight = rarity_weight

    def select_best(self, candidates: list[Candidate]) -> Optional[Candidate]:
        """Score candidates and return the highest-scoring one."""

        if not candidates:
            return None

        def score(c: Candidate) -> float:
            # Normalize distance: lower distance → higher score (max range 20, so 0..1 becomes 1..0)
            dist_score = max(0.0, 1.0 - (c.distance / 20.0))
            conf_score = c.confidence  # Already 0..1
            rarity_score = c.rarity  # Already 0..1

            weighted = (
                dist_score * self.distance_weight
                + conf_score * self.confidence_weight
                + rarity_score * self.rarity_weight
            )
            return weighted

        best = max(candidates, key=score)
        return best

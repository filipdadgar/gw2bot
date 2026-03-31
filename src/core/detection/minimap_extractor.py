"""Minimap-based node detection for off-screen candidates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MinimapCandidate:
    """Candidate extracted from minimap signal."""

    screen_x: int
    screen_y: int
    confidence: float


class MinimapExtractor:
    """Extract node candidates from minimap context."""

    def __init__(self, min_confidence: float = 0.5) -> None:
        self._min_confidence = min_confidence

    def extract_candidates(self, minimap_points: list[dict]) -> list[MinimapCandidate]:
        """Extract candidates from raw minimap point data, filtering by confidence."""

        candidates: list[MinimapCandidate] = []
        for point in minimap_points:
            confidence = float(point.get("confidence", 0.0))
            if confidence < self._min_confidence:
                continue
            candidates.append(
                MinimapCandidate(
                    screen_x=int(point.get("x", 0)),
                    screen_y=int(point.get("y", 0)),
                    confidence=confidence,
                )
            )
        return candidates

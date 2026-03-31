"""Fuse screen-detected and minimap-detected candidates for prioritization."""

from __future__ import annotations

from typing import Any


class CandidateFusion:
    """Combine detection streams into unified candidate list."""

    def fuse(
        self,
        screen_candidates: list[dict[str, Any]],
        minimap_candidates: list[Any],
    ) -> list[dict[str, Any]]:
        """Merge screen and minimap candidates, assigning IDs and preserving all data."""

        fused: list[dict[str, Any]] = []

        # Pass through screen candidates as-is
        for sc in screen_candidates:
            fused.append(sc)

        # Add minimap candidates with synthetic ID
        for idx, mc in enumerate(minimap_candidates):
            fused.append(
                {
                    "candidate_id": f"minimap-{idx}",
                    "confidence": mc.confidence,
                    "distance": getattr(mc, "distance", 0.0),
                    "source": "minimap",
                }
            )

        return fused

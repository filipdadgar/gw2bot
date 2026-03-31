"""Node detection service wrapper around model inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np


@dataclass(frozen=True)
class Detection:
    node_type: str
    confidence: float
    x: int
    y: int


class NodeDetector:
    """Detect harvestable nodes from a frame payload."""

    def __init__(self, predictor: Callable[[np.ndarray], list[dict[str, Any]]] | None = None) -> None:
        self._predictor = predictor

    def detect(self, frame: np.ndarray, min_confidence: float = 0.5) -> list[Detection]:
        """Return detections above threshold from predictor output."""

        if self._predictor is None:
            return []

        raw = self._predictor(frame)
        detections: list[Detection] = []
        for item in raw:
            confidence = float(item.get("confidence", 0.0))
            if confidence < min_confidence:
                continue
            detections.append(
                Detection(
                    node_type=str(item.get("node_type", "unknown")),
                    confidence=confidence,
                    x=int(item.get("x", 0)),
                    y=int(item.get("y", 0)),
                )
            )
        return detections

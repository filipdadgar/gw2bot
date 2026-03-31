"""Capture-to-decision latency benchmark performance validation."""

import time
from unittest.mock import MagicMock

import numpy as np

from src.core.detection.node_detector import NodeDetector


def test_capture_decision_latency_p95_under_900ms() -> None:
    """Benchmark capture → detection → decision pipeline latency.
    
    Success Criteria: p95 latency ≤ 900ms, median ≤ 500ms.
    This test uses synthetic predictor for reproducibility.
    """
    # Create synthetic frame and predictor
    frame_shape = (1080, 1920, 3)
    predictor = MagicMock(return_value=[{"confidence": 0.9, "node_type": "herb", "x": 512, "y": 384}])
    detector = NodeDetector(predictor=predictor)

    latencies = []
    for _ in range(100):
        start = time.perf_counter()

        # Simulate capture
        frame = np.random.randint(0, 255, frame_shape, dtype=np.uint8)

        # Simulate detection decision
        detections = detector.detect(frame, min_confidence=0.5)

        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)

    latencies.sort()
    median = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]

    assert median <= 500, f"Median latency {median}ms exceeds 500ms budget"
    assert p95 <= 900, f"p95 latency {p95}ms exceeds 900ms budget"

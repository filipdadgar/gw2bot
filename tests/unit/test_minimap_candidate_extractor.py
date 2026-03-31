from src.core.detection.minimap_extractor import MinimapExtractor


def test_extract_candidates_filters_by_min_confidence() -> None:
    extractor = MinimapExtractor(min_confidence=0.6)

    points = [
        {"x": 100, "y": 120, "confidence": 0.95},
        {"x": 200, "y": 210, "confidence": 0.59},
        {"x": 50, "y": 80, "confidence": 0.6},
    ]

    candidates = extractor.extract_candidates(points)

    assert len(candidates) == 2
    assert all(c.confidence >= 0.6 for c in candidates)
    assert [c.screen_x for c in candidates] == [100, 50]

from src.core.detection.candidate_fusion import CandidateFusion
from src.core.detection.minimap_extractor import MinimapExtractor


def test_minimap_candidates_are_fused_with_screen_candidates() -> None:
    extractor = MinimapExtractor(min_confidence=0.5)
    fusion = CandidateFusion()

    screen_candidates = [{"candidate_id": "screen-1", "confidence": 0.8, "distance": 6.0}]
    minimap_raw = [
        {"x": 120, "y": 90, "confidence": 0.7},
        {"x": 30, "y": 10, "confidence": 0.2},
    ]

    minimap_candidates = extractor.extract_candidates(minimap_raw)
    fused = fusion.fuse(screen_candidates=screen_candidates, minimap_candidates=minimap_candidates)

    ids = {item["candidate_id"] for item in fused}
    assert "screen-1" in ids
    assert any(cid.startswith("minimap-") for cid in ids)
    assert all(item["confidence"] >= 0.5 for item in fused if item["candidate_id"].startswith("minimap-"))

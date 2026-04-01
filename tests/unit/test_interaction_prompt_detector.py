import numpy as np

from src.core.capture.interaction_prompt_detector import detect_gather_prompt_visible


def test_detect_gather_prompt_visible_returns_false_for_empty_frame() -> None:
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    assert detect_gather_prompt_visible(frame) is False


def test_detect_gather_prompt_visible_returns_true_for_prompt_like_roi() -> None:
    frame = np.zeros((900, 1600, 3), dtype=np.uint8)

    y0 = int(900 * 0.60)
    y1 = int(900 * 0.78)
    x0 = int(1600 * 0.39)
    x1 = int(1600 * 0.66)

    # Dark banner background
    frame[y0:y1, x0:x1, :] = 20

    # Gold/orange accent area (RGB-like ordering)
    frame[y0 + 42 : y0 + 86, x0 + 50 : x0 + 260, 0] = 210
    frame[y0 + 42 : y0 + 86, x0 + 50 : x0 + 260, 1] = 140
    frame[y0 + 42 : y0 + 86, x0 + 50 : x0 + 260, 2] = 40

    assert detect_gather_prompt_visible(frame) is True

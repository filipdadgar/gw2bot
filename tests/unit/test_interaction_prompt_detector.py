import numpy as np

from src.core.capture.interaction_prompt_detector import detect_gather_prompt_visible


def test_detect_gather_prompt_visible_returns_false_for_empty_frame() -> None:
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    assert detect_gather_prompt_visible(frame) is False


def test_detect_gather_prompt_visible_returns_true_for_prompt_like_roi() -> None:
    frame = np.zeros((900, 1600, 3), dtype=np.uint8)

    y0 = int(900 * 0.58)
    y1 = int(900 * 0.88)
    x0 = int(1600 * 0.28)
    x1 = int(1600 * 0.72)

    # Dark banner background
    frame[y0:y1, x0:x1, :] = 20

    # Gold/orange accent area (RGB-like ordering)
    frame[y0 + 70 : y0 + 120, x0 + 140 : x0 + 420, 0] = 210
    frame[y0 + 70 : y0 + 120, x0 + 140 : x0 + 420, 1] = 140
    frame[y0 + 70 : y0 + 120, x0 + 140 : x0 + 420, 2] = 40

    assert detect_gather_prompt_visible(frame) is True

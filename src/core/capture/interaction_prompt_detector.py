"""Heuristics for detecting on-screen gather/interact prompt visibility."""

from __future__ import annotations

import numpy as np


def detect_gather_prompt_visible(frame: np.ndarray) -> bool:
    """Return True when the lower-center prompt area looks like a gather prompt.

    This uses conservative color and darkness heuristics so we can deterministically
    prioritize a harvest/interact action when the in-game prompt is likely visible.
    """

    if frame.ndim != 3 or frame.shape[2] < 3:
        return False

    height, width = frame.shape[0], frame.shape[1]
    if height < 64 or width < 64:
        return False

    # Prompt tends to appear in a compact lower-center zone above the skill bar.
    y0 = int(height * 0.60)
    y1 = int(height * 0.78)
    x0 = int(width * 0.39)
    x1 = int(width * 0.66)
    roi = frame[y0:y1, x0:x1]

    if roi.size == 0:
        return False

    # Work in int space to avoid uint8 wrap during comparisons.
    c0 = roi[:, :, 0].astype(np.int16)
    c1 = roi[:, :, 1].astype(np.int16)
    c2 = roi[:, :, 2].astype(np.int16)

    # Support either RGB or BGR channel ordering.
    orange_rgb = (c0 > 150) & (c1 > 90) & (c2 < 130) & (c0 > c1) & (c1 > c2)
    orange_bgr = (c2 > 150) & (c1 > 90) & (c0 < 130) & (c2 > c1) & (c1 > c0)
    orange_mask = orange_rgb | orange_bgr

    # Prompt banner has dark background with bright gold accent.
    dark_mask = ((c0 + c1 + c2) / 3.0) < 65

    orange_ratio = float(orange_mask.mean())
    dark_ratio = float(dark_mask.mean())

    if orange_ratio < 0.002 or orange_ratio > 0.14:
        return False
    if dark_ratio < 0.22:
        return False

    ys, xs = np.where(orange_mask)
    if ys.size == 0 or xs.size == 0:
        return False

    # Prompt accent is typically elongated horizontally and not full-height.
    h = ys.max() - ys.min() + 1
    w = xs.max() - xs.min() + 1
    roi_h, roi_w = orange_mask.shape
    width_frac = float(w) / float(roi_w)
    height_frac = float(h) / float(roi_h)
    return width_frac >= 0.18 and height_frac <= 0.48

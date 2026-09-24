"""Colour-based screen tracking. Images are HxWx3 RGB uint8 numpy arrays."""

import numpy as np


def color_mask(img: np.ndarray, color, tolerance: int) -> np.ndarray:
    """True where every RGB channel is within `tolerance` of `color`."""
    diff = np.abs(img[..., :3].astype(np.int16) - np.asarray(color, dtype=np.int16))
    return np.all(diff <= tolerance, axis=-1)


def find_x(img: np.ndarray, color, tolerance: int, min_pixels: int = 3):
    """Horizontal centre of the pixels matching `color`, or None if too few."""
    mask = color_mask(img, color, tolerance)
    ys, xs = np.nonzero(mask)
    if xs.size < min_pixels:
        return None
    return float(xs.mean())


def color_matches(pixel, color, tolerance: int) -> bool:
    return all(abs(int(a) - int(b)) <= tolerance for a, b in zip(pixel[:3], color[:3]))

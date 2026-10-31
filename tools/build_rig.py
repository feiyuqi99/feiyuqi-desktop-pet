from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw


def polygon_mask(size: tuple[int, int], points: list[tuple[int, int]]) -> np.ndarray:
    image = Image.new("L", size, 0)
    ImageDraw.Draw(image).polygon(points, fill=255)
    return np.asarray(image) > 0


def color_masks(rgba: np.ndarray) -> dict[str, np.ndarray]:
    data = rgba.astype(np.int16)
    r, g, b, a = data[..., 0], data[..., 1], data[..., 2], data[..., 3]
    hair = (a > 8) & (r > 150) & (r - b > 55) & (r - g > 20) & (g > 50) & (b < 180)
    dark = (a > 8) & (r < 120) & (g < 110) & (b < 100)
    cream = (a > 8) & (r > 220) & (g > 195) & (b > 160) & (r - b < 90)
    return {"hair": hair, "dark": dark, "cream": cream}


def fill_region(
    rgba: np.ndarray,
    mask: np.ndarray,
    color: tuple[int, int, int, int],
) -> np.ndarray:
    out = rgba.copy()
    out[mask] = color
    return out


def best_shift(ref: np.ndarray, target: np.ndarray, max_shift: int = 3) -> tuple[int, int]:
    best = (0, 0)
    best_score = -1
    for dy in range(-max_shift, max_shift + 1):
        for dx in range(-max_shift, max_shift + 1):
            shifted = np.roll(target, (dy, dx), axis=(0, 1))
            score = int((ref & shifted).sum())
            if score > best_score:
                best_score = score
                best = (dy, dx)
    return best


def composite(layers: dict[str, np.ndarray], order: list[str]) -> np.ndarray:
    first = next(iter(layers.values()))
    out = np.zeros_like(first)
    for role in order:
        src = layers[role]
        alpha = src[..., 3:4].astype(np.float32) / 255.0
        out[..., :3] = (
            src[..., :3] * alpha + out[..., :3] * (1 - alpha)
        ).astype(np.uint8)
        out[..., 3:4] = np.maximum(out[..., 3:4], src[..., 3:4])
    return out


def diff_metrics(actual: np.ndarray, expected: np.ndarray) -> tuple[float, float]:
    a = actual.astype(np.int16)
    b = expected.astype(np.int16)
    mask = (a[..., 3] > 8) | (b[..., 3] > 8)
    if not mask.any():
        return 0.0, 0.0
    rgb = np.abs(a[..., :3] - b[..., :3]).mean(axis=2)
    mean = float(rgb[mask].mean())
    coverage = abs(
        float((a[..., 3] > 8).mean()) - float((b[..., 3] > 8).mean())
    )
    return mean, coverage

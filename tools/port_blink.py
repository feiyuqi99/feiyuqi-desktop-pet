from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from PIL import Image, ImageFilter

from tools.build_rig import CANVAS, polygon_mask, shift_rgba

BASE = Path(__file__).resolve().parent.parent
SPRITES = BASE / "assets" / "sprites"

DIFF_THRESHOLD = 60
FACE_POLY = ((218, 165), (310, 165), (310, 252), (218, 252))
# 必须完整盖住两只眼睛：参考帧左眼一直延伸到 x≈185，右边缘截断会留下半只睁眼。
EYE_BAND = ((170, 166), (330, 166), (330, 238), (170, 238))
ALIGN_PAD = 10
MIN_PIECE = 250
SCALES = (0.90, 0.94, 0.98, 1.0, 1.02)
FACE_CENTER = (264, 208)


def dilate(mask: np.ndarray, radius: int = 1) -> np.ndarray:
    image = Image.fromarray((mask * 255).astype(np.uint8))
    image = image.filter(ImageFilter.MaxFilter(radius * 2 + 1))
    return np.asarray(image) > 0


def components(mask: np.ndarray) -> list[np.ndarray]:
    height, width = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    found: list[np.ndarray] = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        stack = [(int(y0), int(x0))]
        seen[y0, x0] = True
        out = np.zeros_like(mask)
        count = 0
        while stack:
            y, x = stack.pop()
            out[y, x] = True
            count += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if count >= MIN_PIECE:
            found.append(out)
    return found


def scale_rgba(rgba: np.ndarray, scale: float, center: tuple[int, int]) -> np.ndarray:
    cx, cy = center
    coeffs = (1 / scale, 0, cx - cx / scale, 0, 1 / scale, cy - cy / scale)
    image = Image.fromarray(rgba)
    out = image.transform(
        (CANVAS, CANVAS), Image.AFFINE, coeffs, resample=Image.BILINEAR
    )
    return np.asarray(out)


def sad_shift(
    ref: np.ndarray,
    target: np.ndarray,
    window: np.ndarray,
    max_shift: int = 16,
) -> tuple[int, int, int]:
    base = window & (ref[..., 3] > 8) & (target[..., 3] > 8)
    best = (0, 0)
    best_score = float("inf")
    ref_rgb = ref[..., :3].astype(np.int32)
    for dy in range(-max_shift, max_shift + 1):
        for dx in range(-max_shift, max_shift + 1):
            shifted = shift_rgba(target, -dy, -dx)
            score = int(np.abs(ref_rgb - shifted[..., :3].astype(np.int32))[base].sum())
            if score < best_score:
                best_score = score
                best = (dy, dx)
    return best[0], best[1], int(best_score)


def eye_mask(ref_idle: np.ndarray, ref_blink: np.ndarray) -> np.ndarray:
    band = polygon_mask((CANVAS, CANVAS), EYE_BAND)
    both = (ref_idle[..., 3] > 8) & (ref_blink[..., 3] > 8)
    diff = np.abs(
        ref_idle[..., :3].astype(np.int16) - ref_blink[..., :3].astype(np.int16)
    ).sum(axis=2)
    return band & both & (diff > DIFF_THRESHOLD)


def port_blink(outfit: str, ref: str = "casual") -> Path:
    ref_idle = np.asarray(Image.open(SPRITES / ref / "idle.png").convert("RGBA"))
    ref_blink = np.asarray(Image.open(SPRITES / ref / "blink.png").convert("RGBA"))
    idle = np.asarray(Image.open(SPRITES / outfit / "idle.png").convert("RGBA"))
    window = polygon_mask((CANVAS, CANVAS), FACE_POLY)

    # 第一段：参考 blink 对齐到参考 idle，收紧眼部差异
    rdy, rdx, _ = sad_shift(ref_idle, ref_blink, window)
    ref_blink = shift_rgba(ref_blink, rdy, rdx)

    # 第二段：尺度 + 平移对齐参考 idle 到目标 idle
    best = (1.0, 0, 0, float("inf"))
    for scale in SCALES:
        si = scale_rgba(ref_idle, scale, FACE_CENTER)
        dy, dx, score = sad_shift(si, idle, window)
        if score < best[3]:
            best = (scale, dy, dx, score)
    scale, tdy, tdx, _ = best
    si = scale_rgba(ref_idle, scale, FACE_CENTER)
    sb = scale_rgba(ref_blink, scale, FACE_CENTER)

    out = idle.copy()
    pieces = 0
    for part in components(eye_mask(si, sb)):
        ys, xs = np.where(part)
        y0, y1 = max(0, ys.min() - ALIGN_PAD), min(CANVAS, ys.max() + ALIGN_PAD + 1)
        x0, x1 = max(0, xs.min() - ALIGN_PAD), min(CANVAS, xs.max() + ALIGN_PAD + 1)
        piece_window = np.zeros((CANVAS, CANVAS), dtype=bool)
        piece_window[y0:y1, x0:x1] = True
        pdy, pdx, _ = sad_shift(si, idle, piece_window)
        aligned_blink = shift_rgba(sb, pdy, pdx)
        patch = shift_rgba(dilate(part, 2).astype(np.uint8), pdy, pdx).astype(bool)
        patch &= idle[..., 3] > 8
        out[patch] = aligned_blink[patch]
        pieces += 1
    target = SPRITES / outfit / "blink.png"
    Image.fromarray(out).save(target)
    print(
        f"{outfit}: blink ported from {ref} "
        f"(ref shift {rdy},{rdx}, scale {scale:.2f}, base {tdy},{tdx}, {pieces} pieces)"
    )
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="从基础角色眨眼帧移植眼部区域生成 blink 帧")
    parser.add_argument("outfits", nargs="+")
    parser.add_argument("--ref", default="casual")
    args = parser.parse_args()
    for outfit in args.outfits:
        port_blink(outfit, args.ref)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

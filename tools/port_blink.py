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
EYE_BAND = ((212, 182), (314, 182), (314, 242), (212, 242))
ALIGN_PAD = 10
MIN_PIECE = 250


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


def sad_shift(
    ref: np.ndarray,
    target: np.ndarray,
    window: np.ndarray,
    max_shift: int = 10,
) -> tuple[int, int]:
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
    return best


def face_window() -> np.ndarray:
    return polygon_mask((CANVAS, CANVAS), FACE_POLY)


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
    window = face_window()

    # 第一段：参考 blink 对齐到参考 idle，收紧眼部差异
    rdy, rdx = sad_shift(ref_idle, ref_blink, window)
    ref_blink_aligned = shift_rgba(ref_blink, rdy, rdx)

    # 第二段：参考 idle 对齐到目标 idle
    tdy, tdx = sad_shift(ref_idle, idle, window)

    out = idle.copy()
    pieces = 0
    aligned_blink = shift_rgba(ref_blink_aligned, tdy, tdx)
    for part in components(eye_mask(ref_idle, ref_blink_aligned)):
        patch = shift_rgba(dilate(part, 1).astype(np.uint8), tdy, tdx).astype(bool)
        patch &= idle[..., 3] > 8
        out[patch] = aligned_blink[patch]
        pieces += 1
    target = SPRITES / outfit / "blink.png"
    Image.fromarray(out).save(target)
    print(
        f"{outfit}: blink ported from {ref} "
        f"(ref shift {rdy},{rdx}, target shift {tdy},{tdx}, {pieces} pieces)"
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

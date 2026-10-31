from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = Path(__file__).resolve().parent.parent
SPRITES = BASE / "assets" / "sprites" / "casual"
OUT = BASE / "assets" / "rig" / "casual"

CANVAS = 512
HAIR_TOP = 240
LEG_TOP = 410
Y, X = np.mgrid[0:CANVAS, 0:CANVAS]
HEAD_POLY = [
    (126, 30), (398, 30), (400, 220), (370, 255), (315, 265),
    (280, 250), (260, 265), (240, 250), (205, 265), (140, 250), (120, 220),
]
BODY_POLY = [
    (150, 245), (360, 245), (392, 300), (388, 360), (366, 415),
    (342, 432), (178, 432), (150, 412), (126, 360), (124, 300),
]
ARM_DOWN_POLY = [
    (150, 265), (228, 265), (240, 320), (226, 390),
    (190, 405), (156, 375), (140, 315),
]
ARM_UP_POLY = [(120, 150), (252, 150), (252, 330), (120, 330)]
FACE_POLY = [(218, 165), (310, 165), (310, 252), (218, 252)]


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


def load(frame: str) -> np.ndarray:
    return np.asarray(Image.open(SPRITES / f"{frame}.png").convert("RGBA"))


def shift_rgba(rgba: np.ndarray, dy: int, dx: int) -> np.ndarray:
    return np.roll(rgba, (dy, dx), axis=(0, 1))


def cut(rgba: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = rgba.copy()
    out[~mask] = 0
    return out


def dilate(mask: np.ndarray, radius: int = 1) -> np.ndarray:
    image = Image.fromarray((mask * 255).astype(np.uint8))
    image = image.filter(ImageFilter.MaxFilter(radius * 2 + 1))
    return np.asarray(image) > 0


def aligned_head(
    rgba: np.ndarray,
    head_poly: np.ndarray,
    base_mask: np.ndarray,
    exclude: np.ndarray | None = None,
) -> np.ndarray:
    mask = head_poly & (rgba[..., 3] > 8)
    if exclude is not None:
        mask &= ~exclude
    dy, dx = best_shift(base_mask, mask)
    shifted = shift_rgba(rgba, dy, dx)
    shifted_mask = shift_rgba(mask.astype(np.uint8), dy, dx).astype(bool)
    return cut(shifted, shifted_mask)


def happy_head(
    idle: np.ndarray,
    happy: np.ndarray,
    head_poly: np.ndarray,
    head_mask: np.ndarray,
    arm_mask: np.ndarray,
    face_poly: np.ndarray,
) -> np.ndarray:
    base = cut(idle, head_mask)
    mask = head_poly & (happy[..., 3] > 8) & ~arm_mask
    dy, dx = best_shift(head_mask, mask)
    aligned = shift_rgba(happy, dy, dx)
    face = face_poly & (aligned[..., 3] > 8) & (base[..., 3] > 8)
    out = base.copy()
    out[face] = aligned[face]
    return out


def build_casual() -> None:
    idle = load("idle")
    blink = load("blink")
    happy = load("happy")
    alpha = idle[..., 3] > 8
    hair = color_masks(idle)["hair"]
    dark = color_masks(idle)["dark"]
    happy_alpha = happy[..., 3] > 8
    happy_masks = color_masks(happy)
    happy_hair = happy_masks["hair"]
    happy_cream = happy_masks["cream"]
    body_poly = polygon_mask((CANVAS, CANVAS), BODY_POLY)
    arm_down_poly = polygon_mask((CANVAS, CANVAS), ARM_DOWN_POLY)
    arm_up_poly = polygon_mask((CANVAS, CANVAS), ARM_UP_POLY)
    head_poly = polygon_mask((CANVAS, CANVAS), HEAD_POLY)
    face_poly = polygon_mask((CANVAS, CANVAS), FACE_POLY)

    head_mask = head_poly & alpha
    side_mask = hair & (Y >= HAIR_TOP)
    legs_mask = dark & (Y >= LEG_TOP)
    left_arm_mask = arm_down_poly & alpha & ~hair & ~head_mask
    arm_region = arm_up_poly & happy_alpha & ~happy_hair & (
        ((X < 188) & (Y < 235))
        | ((X < 198) & (Y >= 235) & (Y < 270))
        | ((X < 208) & (Y >= 270))
    )
    arm_base = arm_region & happy_cream
    arm_up_mask = dilate(arm_base, 2) & arm_region

    side_cover = dilate(side_mask)
    arm_cover = dilate(left_arm_mask)
    body_visible = alpha & ~head_mask & ~side_cover & ~legs_mask & ~arm_cover
    body_fill = body_poly & alpha & (side_cover | arm_cover)
    body_cream = (250, 233, 203, 255)

    layers = {
        "legs": cut(idle, legs_mask),
        "body": fill_region(
            cut(idle, body_visible),
            body_fill & ~body_visible,
            body_cream,
        ),
        "left_arm": cut(idle, left_arm_mask),
        "side_hair": cut(idle, side_mask),
        "head_idle": cut(idle, head_mask),
        "head_blink": aligned_head(blink, head_poly, head_mask),
        "head_happy": happy_head(
            idle, happy, head_poly, head_mask, arm_up_mask, face_poly
        ),
        "arm_up": cut(happy, arm_up_mask),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    for name, rgba in layers.items():
        Image.fromarray(rgba).save(OUT / f"{name}.png")
    spec = {
        "outfit": "casual",
        "canvas": CANVAS,
        "feet": [256, 500],
        "draw_order": ["legs", "body", "left_arm", "side_hair", "head", "arm_up"],
        "layers": {
            "legs": {"file": "legs.png", "depth": 0.55, "anchor": [256, 415]},
            "body": {"file": "body.png", "depth": 0.8, "anchor": [256, 430]},
            "left_arm": {"file": "left_arm.png", "depth": 0.9, "anchor": [185, 275]},
            "side_hair": {
                "file": "side_hair.png",
                "depth": 1.15,
                "anchor": [256, 300],
            },
            "head": {
                "file": "head_idle.png",
                "depth": 1.0,
                "anchor": [256, 250],
                "frames": {
                    "idle": "head_idle.png",
                    "blink": "head_blink.png",
                    "happy": "head_happy.png",
                },
            },
            "arm_up": {"file": "arm_up.png", "depth": 1.1, "anchor": [185, 275]},
        },
    }
    (OUT / "rig.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def check() -> int:
    idle = load("idle")
    head = np.asarray(Image.open(OUT / "head_idle.png").convert("RGBA"))
    layers = {
        "legs": np.asarray(Image.open(OUT / "legs.png").convert("RGBA")),
        "body": np.asarray(Image.open(OUT / "body.png").convert("RGBA")),
        "left_arm": np.asarray(Image.open(OUT / "left_arm.png").convert("RGBA")),
        "side_hair": np.asarray(Image.open(OUT / "side_hair.png").convert("RGBA")),
        "head": head,
    }
    composed = composite(layers, ["legs", "body", "left_arm", "side_hair", "head"])
    mean, coverage = diff_metrics(composed, idle)
    print(f"idle composite mean_rgb={mean:.2f} coverage={coverage:.4f}")
    return 0 if mean <= 3.0 and coverage <= 0.005 else 1


def main() -> int:
    if "--check" in sys.argv:
        return check()
    build_casual()
    return check()


if __name__ == "__main__":
    raise SystemExit(main())

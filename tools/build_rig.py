from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = Path(__file__).resolve().parent.parent
SPRITE_ROOT = BASE / "assets" / "sprites"
RIG_ROOT = BASE / "assets" / "rig"

CANVAS = 512
Y, X = np.mgrid[0:CANVAS, 0:CANVAS]
LAYER_ORDER = ["legs", "body", "left_arm", "side_hair", "head", "arm_up"]


@dataclass(frozen=True)
class OutfitConfig:
    outfit: str
    hair_top: int
    leg_top: int
    legs: str
    head_poly: tuple[tuple[int, int], ...]
    body_poly: tuple[tuple[int, int], ...]
    arm_down_poly: tuple[tuple[int, int], ...]
    arm_up_poly: tuple[tuple[int, int], ...]
    face_poly: tuple[tuple[int, int], ...]
    arm_rule: str
    fill_color: tuple[int, int, int, int] | None
    arm_sleeve_poly: tuple[tuple[int, int], ...] = ()
    legs_poly: tuple[tuple[int, int], ...] = ()
    arm_geometry_poly: tuple[tuple[int, int], ...] = ()
    anchors: dict[str, tuple[int, int]] = field(
        default_factory=lambda: {
            "legs": (256, 415),
            "body": (256, 430),
            "left_arm": (185, 275),
            "side_hair": (256, 300),
            "head": (256, 250),
            "arm_up": (185, 275),
        }
    )
    depths: dict[str, float] = field(
        default_factory=lambda: {
            "legs": 0.55,
            "body": 0.8,
            "left_arm": 0.9,
            "side_hair": 1.15,
            "head": 1.0,
            "arm_up": 1.1,
        }
    )

    @property
    def sprites(self) -> Path:
        return SPRITE_ROOT / self.outfit

    @property
    def out(self) -> Path:
        return RIG_ROOT / self.outfit


CASUAL = OutfitConfig(
    outfit="casual",
    hair_top=240,
    leg_top=410,
    legs="dark",
    head_poly=(
        (126, 30), (398, 30), (400, 220), (370, 255), (315, 265),
        (280, 250), (260, 265), (240, 250), (205, 265), (140, 250), (120, 220),
    ),
    body_poly=(
        (150, 245), (360, 245), (392, 300), (388, 360), (366, 415),
        (342, 432), (178, 432), (150, 412), (126, 360), (124, 300),
    ),
    arm_down_poly=(
        (150, 265), (228, 265), (240, 320), (226, 390),
        (190, 405), (156, 375), (140, 315),
    ),
    arm_up_poly=((120, 150), (252, 150), (252, 330), (120, 330)),
    face_poly=((218, 165), (310, 165), (310, 252), (218, 252)),
    arm_rule="cream",
    fill_color=(250, 233, 203, 255),
)

MAID = OutfitConfig(
    outfit="maid",
    hair_top=240,
    leg_top=436,
    legs="silhouette",
    head_poly=(
        (126, 30), (412, 30), (414, 225), (380, 258), (320, 268),
        (280, 252), (260, 268), (240, 252), (205, 268), (140, 252), (120, 220),
    ),
    body_poly=(
        (150, 245), (360, 245), (392, 300), (388, 360), (366, 415),
        (342, 432), (178, 432), (150, 412), (126, 360), (124, 300),
    ),
    arm_down_poly=(
        (155, 265), (200, 265), (210, 300), (206, 345),
        (198, 378), (178, 388), (158, 372), (148, 330), (146, 290),
    ),
    arm_up_poly=(
        (118, 208), (202, 208), (206, 248), (202, 282), (194, 318),
        (176, 330), (148, 322), (126, 300), (118, 265),
    ),
    arm_sleeve_poly=(
        (160, 285), (205, 280), (215, 310), (212, 345),
        (192, 352), (170, 340), (160, 315),
    ),
    legs_poly=((205, 436), (305, 436), (305, 500), (205, 500)),
    face_poly=((218, 165), (310, 165), (310, 252), (218, 252)),
    arm_rule="skin",
    fill_color=None,
    anchors={
        "legs": (256, 420),
        "body": (256, 430),
        "left_arm": (185, 290),
        "side_hair": (256, 300),
        "head": (256, 250),
        "arm_up": (200, 300),
    },
)

CONFIGS = {config.outfit: config for config in (CASUAL, MAID)}

JK = OutfitConfig(
    outfit="jk",
    hair_top=240,
    leg_top=434,
    legs="silhouette",
    head_poly=(
        (126, 30), (398, 30), (400, 220), (370, 255), (315, 265),
        (280, 250), (260, 265), (240, 250), (205, 265), (140, 250), (120, 220),
    ),
    body_poly=(
        (150, 245), (360, 245), (392, 300), (388, 360), (366, 415),
        (342, 432), (178, 432), (150, 412), (126, 360), (124, 300),
    ),
    arm_down_poly=(
        (150, 265), (228, 265), (240, 320), (226, 390),
        (190, 405), (156, 375), (140, 315),
    ),
    arm_up_poly=((120, 150), (252, 150), (252, 330), (120, 330)),
    face_poly=((218, 165), (310, 165), (310, 252), (218, 252)),
    arm_rule="auto",
    fill_color=None,
    legs_poly=((200, 434), (314, 434), (314, 505), (200, 505)),
    arm_geometry_poly=(
        (112, 145), (198, 145), (210, 230), (224, 262), (236, 300),
        (232, 312), (150, 312), (142, 258), (104, 202),
    ),
)

CONFIGS[JK.outfit] = JK


def polygon_mask(size: tuple[int, int], points: tuple[tuple[int, int], ...]) -> np.ndarray:
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


def inpaint_neighbors(
    rgba: np.ndarray,
    target: np.ndarray,
    source: np.ndarray,
    max_iterations: int = 256,
) -> np.ndarray:
    out = rgba.copy()
    known = source & (rgba[..., 3] > 0)
    pending = target & ~known
    for _ in range(max_iterations):
        if not pending.any():
            break
        total = np.zeros(out.shape, dtype=np.float32)
        count = np.zeros(out.shape[:2], dtype=np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            near_known = np.roll(known, (dy, dx), axis=(0, 1))
            near_rgba = np.roll(out, (dy, dx), axis=(0, 1)).astype(np.float32)
            total += near_rgba * near_known[..., None]
            count += near_known
        grow = pending & (count > 0)
        if not grow.any():
            break
        out[grow] = (total[grow] / count[grow, None]).astype(np.uint8)
        known |= grow
        pending &= ~grow
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


def load(config: OutfitConfig, frame: str) -> np.ndarray:
    return np.asarray(Image.open(config.sprites / f"{frame}.png").convert("RGBA"))


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


def fill_holes(mask: np.ndarray) -> np.ndarray:
    background = (~mask).astype(np.uint8) * 255
    image = Image.fromarray(background).copy()
    start = (0, 0) if not mask[0, 0] else (int(mask.shape[1]) - 1, 0)
    ImageDraw.floodfill(image, start, 128)
    exterior = np.asarray(image) == 128
    return mask | (~mask & ~exterior)


def largest_component(mask: np.ndarray) -> np.ndarray:
    seen = np.zeros_like(mask, dtype=bool)
    best: list[tuple[int, int]] = []
    height, width = mask.shape
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        stack = [(int(y0), int(x0))]
        seen[y0, x0] = True
        component: list[tuple[int, int]] = []
        while stack:
            y, x = stack.pop()
            component.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if len(component) > len(best):
            best = component
    out = np.zeros_like(mask)
    if best:
        ys, xs = zip(*best)
        out[list(ys), list(xs)] = True
    return out


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


def arm_up_mask(
    config: OutfitConfig,
    happy: np.ndarray,
    happy_masks: dict[str, np.ndarray],
    region: np.ndarray,
) -> np.ndarray:
    alpha = happy[..., 3] > 8
    if config.arm_rule == "auto":
        geometry = polygon_mask((CANVAS, CANVAS), config.arm_geometry_poly)
        core = alpha & ~happy_masks["hair"] & ~happy_masks["dark"] & geometry & region
        mask = core | (happy_masks["dark"] & dilate(core, 2) & geometry & region)
        mask = largest_component(fill_holes(mask))
        return mask & alpha
    if config.arm_rule == "cream":
        if config.arm_geometry_poly:
            geometry = polygon_mask((CANVAS, CANVAS), config.arm_geometry_poly)
        else:
            geometry = (
                ((X < 188) & (Y < 235))
                | ((X < 198) & (Y >= 235) & (Y < 270))
                | ((X < 208) & (Y >= 270))
            )
        base = region & alpha & ~happy_masks["hair"] & geometry & happy_masks["cream"]
        mask = dilate(base, 2) & region & geometry
        if config.arm_geometry_poly:
            mask = largest_component(fill_holes(mask))
        return mask & alpha
    data = happy.astype(np.int16)
    r, g, b = data[..., 0], data[..., 1], data[..., 2]
    skin = (
        (alpha)
        & (r > 190)
        & (g > 140)
        & (b > 110)
        & (r - b < 110)
        & (r - g < 90)
    )
    mask = skin & region
    mask |= happy_masks["dark"] & dilate(mask, 2) & region
    if config.arm_sleeve_poly:
        sleeve = polygon_mask((CANVAS, CANVAS), config.arm_sleeve_poly)
        mask |= happy_masks["dark"] & sleeve
    mask = fill_holes(mask)
    mask = largest_component(mask)
    return mask & alpha


def hand_anchor(mask: np.ndarray) -> tuple[int, int]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return (150, 200)
    top = int(ys.min())
    bottom = int(ys.max())
    band = max(4, int((bottom - top) * 0.18))
    selected = ys <= top + band
    return (int(round(xs[selected].mean())), int(round(ys[selected].mean())))


def build(config: OutfitConfig) -> None:
    idle = load(config, "idle")
    blink = load(config, "blink")
    happy = load(config, "happy")
    alpha = idle[..., 3] > 8
    idle_masks = color_masks(idle)
    happy_alpha = happy[..., 3] > 8
    happy_masks = color_masks(happy)

    def mask(points: tuple[tuple[int, int], ...]) -> np.ndarray:
        return polygon_mask((CANVAS, CANVAS), points)

    body_poly = mask(config.body_poly)
    arm_down_poly = mask(config.arm_down_poly)
    arm_up_poly = mask(config.arm_up_poly)
    head_poly = mask(config.head_poly)
    face_poly = mask(config.face_poly)

    head_mask = head_poly & alpha
    side_mask = idle_masks["hair"] & (Y >= config.hair_top)
    if config.legs == "silhouette":
        legs_mask = mask(config.legs_poly) & alpha & ~idle_masks["hair"]
    else:
        legs_mask = idle_masks["dark"] & (Y >= config.leg_top)
    left_arm_mask = arm_down_poly & alpha & ~idle_masks["hair"] & ~head_mask
    arm_region = arm_up_poly & happy_alpha & ~happy_masks["hair"]
    raised_arm = arm_up_mask(config, happy, happy_masks, arm_region)

    side_cover = dilate(side_mask)
    arm_cover = dilate(left_arm_mask)
    body_visible = alpha & ~head_mask & ~side_cover & ~legs_mask & ~arm_cover
    body_hidden = body_poly & alpha & (side_cover | arm_cover) & ~body_visible

    body = cut(idle, body_visible)
    if config.fill_color is not None:
        body = fill_region(body, body_hidden, config.fill_color)
    else:
        body = inpaint_neighbors(body, body_hidden, body_visible & (body[..., 3] > 0))

    layers = {
        "legs": cut(idle, legs_mask),
        "body": body,
        "left_arm": cut(idle, left_arm_mask),
        "side_hair": cut(idle, side_mask),
        "head_idle": cut(idle, head_mask),
        "head_blink": aligned_head(blink, head_poly, head_mask),
        "head_happy": happy_head(
            idle, happy, head_poly, head_mask, raised_arm, face_poly
        ),
        "arm_up": cut(happy, raised_arm),
    }

    config.out.mkdir(parents=True, exist_ok=True)
    for name, rgba in layers.items():
        Image.fromarray(rgba).save(config.out / f"{name}.png")
    spec = {
        "outfit": config.outfit,
        "canvas": CANVAS,
        "feet": [256, 500],
        "hand": list(hand_anchor(raised_arm)),
        "draw_order": LAYER_ORDER,
        "layers": {
            role: {
                "file": f"{'head_idle' if role == 'head' else role}.png",
                "depth": config.depths[role],
                "anchor": list(config.anchors[role]),
                **(
                    {
                        "frames": {
                            "idle": "head_idle.png",
                            "blink": "head_blink.png",
                            "happy": "head_happy.png",
                        }
                    }
                    if role == "head"
                    else {}
                ),
            }
            for role in LAYER_ORDER
        },
    }
    (config.out / "rig.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def check(outfit: str = "casual") -> int:
    config = CONFIGS[outfit]
    idle = load(config, "idle")
    layers = {
        "legs": np.asarray(Image.open(config.out / "legs.png").convert("RGBA")),
        "body": np.asarray(Image.open(config.out / "body.png").convert("RGBA")),
        "left_arm": np.asarray(Image.open(config.out / "left_arm.png").convert("RGBA")),
        "side_hair": np.asarray(Image.open(config.out / "side_hair.png").convert("RGBA")),
        "head": np.asarray(Image.open(config.out / "head_idle.png").convert("RGBA")),
    }
    composed = composite(layers, ["legs", "body", "left_arm", "side_hair", "head"])
    mean, coverage = diff_metrics(composed, idle)
    print(f"{outfit} idle composite mean_rgb={mean:.2f} coverage={coverage:.4f}")
    return 0 if mean <= 3.0 and coverage <= 0.005 else 1


def main() -> int:
    names = [arg for arg in sys.argv[1:] if not arg.startswith("--")] or list(CONFIGS)
    unknown = [name for name in names if name not in CONFIGS]
    if unknown:
        print(f"unknown outfit: {', '.join(unknown)}")
        return 2
    if "--check" not in sys.argv:
        for name in names:
            build(CONFIGS[name])
    return max(check(name) for name in names)


if __name__ == "__main__":
    raise SystemExit(main())

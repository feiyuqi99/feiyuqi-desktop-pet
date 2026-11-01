from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "assets" / "raw"
OUT = BASE / "assets" / "sprites"
ICONS = BASE / "assets" / "icons"

CANVAS = 512
BASELINE = 500
TARGET_H = 460
KEY_LOW = 18
KEY_HIGH = 50
ALPHA_THRESHOLD = 8

OUTFITS = {
    "maid": ["idle", "blink", "happy"],
    "casual": ["idle", "blink", "happy"],
    "jk": ["idle", "happy"],
    "pajama": ["idle", "happy"],
    "sport": ["idle", "happy"],
    "sweater": ["idle", "happy"],
    "yukata": ["idle", "happy"],
    "qipao": ["idle", "happy"],
    "santa": ["idle", "happy"],
    "raincoat": ["idle", "happy"],
    "trench": ["idle", "happy"],
    "witch": ["idle", "happy"],
}


def key_green(path: Path) -> Image.Image:
    rgb = Image.open(path).convert("RGB")
    arr = np.asarray(rgb).astype(np.int16)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    max_rb = np.maximum(r, b)
    greenness = g - max_rb
    alpha = np.clip((KEY_HIGH - greenness) * 255.0 / (KEY_HIGH - KEY_LOW), 0, 255)
    green = np.minimum(g, max_rb + 6)
    rgba = np.dstack(
        [r.astype(np.uint8), green.astype(np.uint8), b.astype(np.uint8), alpha.astype(np.uint8)]
    )
    image = Image.fromarray(rgba, "RGBA")
    image.putalpha(image.getchannel("A").filter(ImageFilter.MinFilter(3)))
    return image


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    alpha = np.asarray(image.getchannel("A"))
    ys, xs = np.where(alpha > ALPHA_THRESHOLD)
    if len(xs) == 0:
        raise ValueError("sprite is fully transparent")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def feet_center_x(image: Image.Image, bbox: tuple[int, int, int, int]) -> float:
    alpha = np.asarray(image.getchannel("A"))
    x0, y0, x1, y1 = bbox
    band = max(4, int((y1 - y0) * 0.08))
    region = alpha[y1 - band : y1, x0:x1]
    ys, xs = np.where(region > 100)
    if len(xs) == 0:
        return (x0 + x1) / 2
    return x0 + float(xs.mean())


def build_outfit(outfit: str, frames: list[str]) -> dict[str, Image.Image]:
    keyed: dict[str, Image.Image] = {}
    boxes: dict[str, tuple[int, int, int, int]] = {}
    for frame in frames:
        image = key_green(RAW / f"{outfit}_{frame}.png")
        keyed[frame] = image
        boxes[frame] = alpha_bbox(image)

    idle_box = boxes["idle"]
    idle_h = idle_box[3] - idle_box[1]
    max_h = max(box[3] - box[1] for box in boxes.values())
    scale = min(TARGET_H / idle_h, (BASELINE - 6) / max_h)

    for _ in range(40):
        fits = True
        for frame, image in keyed.items():
            box = boxes[frame]
            feet_x = feet_center_x(image, box) - box[0]
            width = (box[2] - box[0]) * scale
            height = (box[3] - box[1]) * scale
            left = CANVAS / 2 - feet_x * scale
            if left < 4 or left + width > CANVAS - 4 or BASELINE - height < 4:
                fits = False
                break
        if fits:
            break
        scale *= 0.98

    results: dict[str, Image.Image] = {}
    for frame, image in keyed.items():
        box = boxes[frame]
        feet_x = feet_center_x(image, box) - box[0]
        crop = image.crop(box)
        width = max(1, round(crop.width * scale))
        height = max(1, round(crop.height * scale))
        crop = crop.resize((width, height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        left = round(CANVAS / 2 - feet_x * scale)
        top = BASELINE - height
        canvas.alpha_composite(crop, (left, top))
        results[frame] = canvas
    return results


def make_tray_icon(idle: Image.Image) -> None:
    box = alpha_bbox(idle)
    x0, y0, x1, y1 = box
    char_h = y1 - y0
    side = int(char_h * 0.62)
    center_x = int((x0 + x1) / 2)
    center_y = y0 + int(side * 0.46)
    left = max(0, center_x - side // 2)
    top = max(0, center_y - side // 2)
    head = idle.crop((left, top, left + side, top + side))
    head = head.resize((200, 200), Image.Resampling.LANCZOS)

    icon = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    draw.ellipse((10, 10, 246, 246), fill=(240, 238, 230, 255), outline=(217, 119, 87, 255), width=8)
    icon.alpha_composite(head, (28, 28))
    ICONS.mkdir(parents=True, exist_ok=True)
    icon.resize((128, 128), Image.Resampling.LANCZOS).save(ICONS / "tray.png")
    icon.save(ICONS / "pet.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def make_preview(images: dict[str, dict[str, Image.Image]]) -> None:
    tile = 180
    cols = 3
    rows = max(1, len(images))
    sheet = Image.new("RGB", (tile * cols, tile * rows), (236, 233, 224))
    draw = ImageDraw.Draw(sheet)
    for y in range(0, sheet.height, 16):
        for x in range(0, sheet.width, 16):
            if (x // 16 + y // 16) % 2 == 0:
                draw.rectangle((x, y, x + 15, y + 15), fill=(248, 246, 240))
    for row, (outfit, frames) in enumerate(images.items()):
        for col, frame in enumerate(("idle", "blink", "happy")):
            if frame not in frames:
                continue
            sprite = frames[frame].resize((tile, tile), Image.Resampling.LANCZOS)
            sheet.paste(sprite, (col * tile, row * tile), sprite)
    sheet.save(OUT / "preview.png")


def main() -> int:
    names = sys.argv[1:] or [
        outfit for outfit, frames in OUTFITS.items() if (RAW / f"{outfit}_{frames[0]}.png").is_file()
    ]
    unknown = [name for name in names if name not in OUTFITS]
    if unknown:
        print(f"unknown outfit: {', '.join(unknown)}")
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    all_images: dict[str, dict[str, Image.Image]] = {}
    for outfit in names:
        frames = [
            frame for frame in OUTFITS[outfit] if (RAW / f"{outfit}_{frame}.png").is_file()
        ]
        images = build_outfit(outfit, frames)
        target = OUT / outfit
        target.mkdir(parents=True, exist_ok=True)
        for frame, image in images.items():
            alpha = np.asarray(image.getchannel("A"))
            assert image.size == (CANVAS, CANVAS), image.size
            assert alpha[0, 0] == 0 and alpha[0, -1] == 0 and alpha[-1, 0] == 0 and alpha[-1, -1] == 0
            image.save(target / f"{frame}.png")
        all_images[outfit] = images
        print(f"{outfit}: frames={len(images)}")
    if "maid" in all_images:
        make_tray_icon(all_images["maid"]["idle"])
    make_preview(all_images)
    print(f"sprites -> {OUT}")
    print(f"icons   -> {ICONS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "assets" / "raw"

BG_THRESHOLD = 40
CORNER = 16


def background_color(rgb: np.ndarray) -> np.ndarray:
    height, width = rgb.shape[:2]
    patches = [
        rgb[:CORNER, :CORNER],
        rgb[:CORNER, -CORNER:],
        rgb[-CORNER:, :CORNER],
        rgb[-CORNER:, -CORNER:],
    ]
    return np.median(np.concatenate([p.reshape(-1, 3) for p in patches]), axis=0)


def components(mask: np.ndarray) -> list[tuple[tuple[int, int], ...]]:
    height, width = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    found: list[tuple[tuple[int, int], ...]] = []
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
        found.append(tuple(component))
    return found


def clean_array(rgb: np.ndarray) -> np.ndarray:
    bg = background_color(rgb)
    fg = np.abs(rgb.astype(np.int16) - bg).sum(axis=2) > BG_THRESHOLD
    parts = components(fg)
    if not parts:
        raise ValueError("image is empty")
    main = max(parts, key=len)
    ys, xs = zip(*main)
    main_box = (min(ys), min(xs), max(ys), max(xs))
    keep = np.zeros(fg.shape, dtype=bool)
    for part in parts:
        if part is main:
            keep[list(ys), list(xs)] = True
            continue
        if len(part) < 0.005 * len(main):
            continue
        p_ys, p_xs = zip(*part)
        cy, cx = sum(p_ys) / len(part), sum(p_xs) / len(part)
        pad = 24
        inside = (
            main_box[0] - pad <= cy <= main_box[2] + pad
            and main_box[1] - pad <= cx <= main_box[3] + pad
        )
        if inside or len(part) > 0.25 * len(main):
            keep[list(p_ys), list(p_xs)] = True
    out = rgb.copy()
    out[~keep] = bg.astype(np.uint8) if rgb.dtype == np.uint8 else bg
    return out.astype(np.uint8)


def clean_file(src: Path, dst: Path) -> None:
    rgb = np.asarray(Image.open(src).convert("RGB"))
    out = clean_array(rgb)
    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(dst)
    print(f"{src.name} -> {dst}")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: clean_raw.py <src.png> [dst.png] | --gen <id>=<src.png> ...")
        return 2
    if sys.argv[1] == "--gen":
        for pair in sys.argv[2:]:
            outfit_id, src = pair.split("=", 1)
            clean_file(Path(src), RAW / f"{outfit_id}.png")
        return 0
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else RAW / src.name
    clean_file(src, dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

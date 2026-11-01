from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from tools.build_sprites import alpha_bbox, feet_center_x, key_green

ROOT = Path(__file__).resolve().parent.parent
SPRITES = ROOT / "assets" / "sprites"
ICONS = ROOT / "assets" / "icons"


def test_green_key_on_synthetic_image(tmp_path):
    image = Image.new("RGB", (120, 120), (0, 200, 0))
    for x in range(40, 80):
        for y in range(30, 110):
            image.putpixel((x, y), (200, 40, 30))
    path = tmp_path / "raw.png"
    image.save(path)
    keyed = key_green(path)
    alpha = keyed.getchannel("A")
    assert alpha.getpixel((0, 0)) == 0
    assert alpha.getpixel((119, 119)) == 0
    assert alpha.getpixel((60, 70)) == 255
    box = alpha_bbox(keyed)
    assert 38 <= box[0] <= 42
    assert 28 <= box[1] <= 32
    assert 78 <= box[2] <= 82
    assert 108 <= box[3] <= 112
    assert 58 <= feet_center_x(keyed, box) <= 62


def test_output_sprites_are_clean():
    for outfit in ("maid", "casual"):
        for frame in ("idle", "blink", "happy"):
            path = SPRITES / outfit / f"{frame}.png"
            assert path.exists(), path
            image = Image.open(path).convert("RGBA")
            assert image.size == (512, 512)
            alpha = image.getchannel("A")
            for corner in ((0, 0), (511, 0), (0, 511), (511, 511)):
                assert alpha.getpixel(corner) == 0
            box = alpha_bbox(image)
            assert abs(box[3] - 500) <= 1, (path, box)
            assert 455 <= box[3] - box[1] <= 461, (path, box)
            arr = np.asarray(image).astype(np.int16)
            mask = arr[..., 3] > 128
            greenness = arr[..., 1] - np.maximum(arr[..., 0], arr[..., 2])
            assert int((greenness[mask] > 40).sum()) == 0, path


def test_icons_exist():
    tray = Image.open(ICONS / "tray.png")
    assert tray.size == (128, 128)
    assert (ICONS / "pet.ico").exists()


def test_blink_mask_covers_both_eyes():
    from tools.port_blink import SPRITES, components, eye_mask

    idle = np.asarray(Image.open(SPRITES / "casual" / "idle.png").convert("RGBA"))
    blink = np.asarray(Image.open(SPRITES / "casual" / "blink.png").convert("RGBA"))
    pieces = []
    for piece in components(eye_mask(idle, blink)):
        xs = np.where(piece)[1]
        pieces.append((int(xs.min()), int(xs.max()), int(piece.sum())))
    assert len(pieces) == 2, pieces
    left, right = sorted(pieces)
    # 参考帧左眼一直延伸到 x≈185；掩码左边缘一旦收窄，目标帧会残留半只睁眼。
    assert left[0] <= 195 and left[1] - left[0] >= 40, left
    assert right[0] >= 250 and right[1] - right[0] >= 40, right
    assert left[2] > 900 and right[2] > 900, pieces

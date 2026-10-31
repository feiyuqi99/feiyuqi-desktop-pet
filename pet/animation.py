from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtGui import QImage, QPixmap

SPRITE_DIR = Path(__file__).resolve().parent.parent / "assets" / "sprites"
SPRITE_SIZE = 512
DISPLAY_SCALE = 0.4
DRAW_SIZE = SPRITE_SIZE * DISPLAY_SCALE
FEET_Y = 500 * DISPLAY_SCALE
WINDOW_WIDTH = 248
WINDOW_HEIGHT = 216
FEET_X = WINDOW_WIDTH / 2

OUTFITS = ("maid", "casual")
FRAMES = ("idle", "blink", "happy")

HEAD = "head"
FACE = "face"
BODY = "body"
HAND = "hand"
SKIRT = "skirt"
FEET = "feet"

SPRITE_FEET_X = 256
SPRITE_FEET_Y = 500
HAND_SPOTS = ((174, 330, 30), (338, 330, 30))


def part_at(sx: int, sy: int) -> str:
    if sy >= 412:
        return FEET
    for hx, hy, radius in HAND_SPOTS:
        if (sx - hx) ** 2 + (sy - hy) ** 2 <= radius**2:
            return HAND
    if sy >= 345:
        return SKIRT
    if sy >= 248:
        return HAND if abs(sx - 256) > 96 else BODY
    if sy >= 150:
        return FACE if abs(sx - 256) <= 74 else HEAD
    return HEAD


class SpriteLibrary:
    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], QPixmap] = {}
        self._images: dict[tuple[str, str], QImage] = {}
        self.missing: list[str] = []

    def preload(self) -> None:
        for outfit in OUTFITS:
            for frame in FRAMES:
                self.get(outfit, frame)

    def path_for(self, outfit: str, frame: str) -> Path:
        path = SPRITE_DIR / outfit / f"{frame}.png"
        if not path.exists():
            self.missing.append(str(path))
            logging.warning("sprite missing: %s", path)
            path = SPRITE_DIR / outfit / "idle.png"
        if not path.exists():
            path = SPRITE_DIR / "maid" / "idle.png"
        return path

    def get(self, outfit: str, frame: str) -> QPixmap:
        key = (outfit, frame)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        path = self.path_for(outfit, frame)
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            logging.error("sprite failed to load: %s", path)
            pixmap = QPixmap(SPRITE_SIZE, SPRITE_SIZE)
            pixmap.fill(0)
        self._cache[key] = pixmap
        return pixmap

    def image(self, outfit: str, frame: str) -> QImage:
        key = (outfit, frame)
        cached = self._images.get(key)
        if cached is not None:
            return cached
        image = self.get(outfit, frame).toImage()
        self._images[key] = image
        return image

    def alpha_at(self, outfit: str, frame: str, sx: int, sy: int) -> int:
        if not (0 <= sx < SPRITE_SIZE and 0 <= sy < SPRITE_SIZE):
            return 0
        return self.image(outfit, frame).pixelColor(sx, sy).alpha()

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

SPRITE_DIR = Path(__file__).resolve().parent.parent / "assets" / "sprites"
SPRITE_SIZE = 512
DISPLAY_SCALE = 0.6
DRAW_SIZE = SPRITE_SIZE * DISPLAY_SCALE
FEET_Y = 500 * DISPLAY_SCALE
WINDOW_WIDTH = 360
WINDOW_HEIGHT = 320
FEET_X = WINDOW_WIDTH / 2
HEAD_TOP = 24
HEAD_BOTTOM = 152

OUTFITS = ("maid", "casual")
FRAMES = ("idle", "blink", "happy")


class SpriteLibrary:
    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], QPixmap] = {}
        self.missing: list[str] = []

    def preload(self) -> None:
        for outfit in OUTFITS:
            for frame in FRAMES:
                self.get(outfit, frame)

    def get(self, outfit: str, frame: str) -> QPixmap:
        key = (outfit, frame)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        path = SPRITE_DIR / outfit / f"{frame}.png"
        if not path.exists():
            self.missing.append(str(path))
            logging.warning("sprite missing: %s", path)
            path = SPRITE_DIR / outfit / "idle.png"
        if not path.exists():
            path = SPRITE_DIR / "maid" / "idle.png"
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            logging.error("sprite failed to load: %s", path)
            pixmap = QPixmap(int(DRAW_SIZE), int(DRAW_SIZE))
            pixmap.fill(Qt.transparent)
        else:
            pixmap = pixmap.scaled(
                int(round(DRAW_SIZE)),
                int(round(DRAW_SIZE)),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        self._cache[key] = pixmap
        return pixmap

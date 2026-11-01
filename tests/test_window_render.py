from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from pet.animation import WINK_BOX, SpriteLibrary
from pet.behavior import PetState
from pet.outfits import available_ids
from pet.rig import RigLibrary
from pet.window import PetWindow

_APP = QApplication.instance() or QApplication([])


def qimage_array(image: QImage) -> np.ndarray:
    image = image.convertToFormat(QImage.Format_RGBA8888)
    data = np.frombuffer(image.constBits(), np.uint8)
    rows = data.reshape(image.height(), image.bytesPerLine())
    return rows[:, : image.width() * 4].reshape(image.height(), image.width(), 4).copy()


def render(window: PetWindow) -> QImage:
    image = QImage(window.width(), window.height(), QImage.Format_ARGB32)
    image.fill(0)
    window.render(image)
    return image


def opaque_count(image: QImage) -> int:
    return sum(
        1
        for y in range(image.height())
        for x in range(image.width())
        if image.pixelColor(x, y).alpha() > 0
    )


def test_hover_lean_ramps_instead_of_snapping():
    window = PetWindow(SpriteLibrary())
    window._hover_target = 2.5
    rising = [window.step_hover(1 / 30) for _ in range(8)]
    assert max(abs(b - a) for a, b in zip([0.0] + rising, rising)) < 0.6
    assert rising[-1] > 1.5
    window._hover_target = 0.0
    falling = [window.step_hover(1 / 30) for _ in range(8)]
    assert max(abs(b - a) for a, b in zip(falling, falling[1:])) < 0.6
    assert falling[-1] < 0.6


def test_wink_closes_the_whole_left_eye_for_every_outfit():
    from tools.port_blink import components

    sprites = SpriteLibrary()
    window = PetWindow(sprites)
    box_x, box_y, box_w, box_h = WINK_BOX
    for outfit in available_ids():
        idle = qimage_array(sprites.image(outfit, "idle"))
        blink = qimage_array(sprites.image(outfit, "blink"))
        diff = np.abs(
            idle[..., :3].astype(np.int16) - blink[..., :3].astype(np.int16)
        ).sum(axis=2)
        mask = (idle[..., 3] > 8) & (blink[..., 3] > 8) & (diff > 100)
        mask[:, 245:] = False
        mask[:140] = False
        mask[250:] = False
        eye = max(components(mask), key=lambda piece: int(piece.sum()))
        ys, xs = np.where(eye)
        assert box_x <= xs.min() and xs.max() < box_x + box_w, outfit
        assert box_y <= ys.min() and ys.max() < box_y + box_h, outfit

        canvas = sprites.image(outfit, "idle").copy()
        painter = QPainter(canvas)
        window.set_outfit(outfit)
        window._draw_expression(painter, PetState(expression="wink"))
        painter.end()
        result = qimage_array(canvas)
        delta = np.abs(
            result[ys, xs, :3].astype(np.int16) - blink[ys, xs, :3].astype(np.int16)
        )
        assert int(delta.max()) <= 6, outfit


def test_maid_and_casual_both_render():
    sprites = SpriteLibrary()
    sprites.preload()
    window = PetWindow(sprites)
    window.apply_state(PetState())
    window.set_outfit("maid")
    assert opaque_count(render(window)) > 1000
    window.set_outfit("casual")
    assert opaque_count(render(window)) > 1000


def test_maid_uses_rig_when_available():
    sprites = SpriteLibrary()
    sprites.preload()
    window = PetWindow(sprites)
    window.apply_state(PetState())
    window.set_outfit("maid")
    assert window._rig is not None
    assert opaque_count(render(window)) > 1000


def test_casual_without_rig_falls_back(tmp_path):
    sprites = SpriteLibrary()
    window = PetWindow(sprites)
    window.apply_state(PetState())
    window._rig_library = RigLibrary(tmp_path)
    window.set_outfit("casual")
    assert window._rig is None
    assert opaque_count(render(window)) > 1000

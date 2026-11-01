from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from pet.animation import SpriteLibrary
from pet.behavior import PetState
from pet.rig import RigLibrary
from pet.window import PetWindow

_APP = QApplication.instance() or QApplication([])


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

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


def test_maid_and_casual_both_render():
    sprites = SpriteLibrary()
    sprites.preload()
    window = PetWindow(sprites)
    window.apply_state(PetState())
    window.set_outfit("maid")
    assert opaque_count(render(window)) > 1000
    window.set_outfit("casual")
    assert opaque_count(render(window)) > 1000


def test_casual_without_rig_falls_back(tmp_path):
    sprites = SpriteLibrary()
    window = PetWindow(sprites)
    window.apply_state(PetState())
    window._rig_library = RigLibrary(tmp_path)
    window.set_outfit("casual")
    assert window._rig is None
    assert opaque_count(render(window)) > 1000

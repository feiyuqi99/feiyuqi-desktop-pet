from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from pet.animation import SpriteLibrary
from pet.behavior import PetState
from pet.window import PetWindow

_APP = QApplication.instance() or QApplication([])

NEW_EXPRESSIONS = (
    "wink",
    "tears",
    "pout",
    "confused",
    "shy",
    "dizzy",
    "sweat",
    "expect",
)


def render(window: PetWindow) -> QImage:
    image = QImage(window.width(), window.height(), QImage.Format_ARGB32)
    image.fill(0)
    window.render(image)
    return image


def diff_count(first: QImage, second: QImage) -> int:
    return sum(
        1
        for y in range(first.height())
        for x in range(first.width())
        if first.pixel(x, y) != second.pixel(x, y)
    )


def make_window() -> PetWindow:
    sprites = SpriteLibrary()
    sprites.preload()
    window = PetWindow(sprites)
    window.set_outfit("maid")
    window._rig = None
    return window


def test_new_expressions_draw_visible_overlay():
    window = make_window()
    window.apply_state(PetState(expression="neutral"))
    base = render(window)
    for name in NEW_EXPRESSIONS:
        window.apply_state(PetState(expression=name))
        assert diff_count(base, render(window)) > 30, name


def test_neutral_has_no_overlay():
    window = make_window()
    window.apply_state(PetState(expression="neutral"))
    first = render(window)
    second = render(window)
    assert diff_count(first, second) == 0

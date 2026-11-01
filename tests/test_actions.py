from __future__ import annotations

import os
import random
from datetime import datetime

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from pet import behavior
from pet.animation import SpriteLibrary
from pet.behavior import Behavior, BehaviorContext, PetState
from pet.rig import RigMotion
from pet.window import PetWindow

_APP = QApplication.instance() or QApplication([])
DAY = datetime(2026, 1, 5, 10, 0).timestamp()


def ctx(now: float, **kwargs) -> BehaviorContext:
    base = dict(
        now=now,
        time_band="morning",
        activity="coding",
        idle_seconds=0.0,
        quiet=False,
        mood=70,
        gap=0.0,
        pet_x=100.0,
        screen_left=0.0,
        screen_right=1000.0,
    )
    base.update(kwargs)
    return BehaviorContext(**base)


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


def test_action_sets_prop_and_returns_to_idle():
    b = Behavior(random.Random(40))
    assert b.start_action("drink", DAY)
    state = b.tick(ctx(DAY + 0.1))
    assert state.mode == behavior.ACTION
    assert state.action == "drink"
    assert state.prop == "drink"
    state = b.tick(ctx(DAY + 4.0))
    assert state.action == ""
    assert state.prop == ""
    assert b.mode == behavior.IDLE


def test_quiet_action_does_not_queue_a_line():
    b = Behavior(random.Random(41))
    assert b.start_action("read", DAY, quiet=True)
    assert b.drain() == []
    b.start_action("eat", DAY + 5.0)
    assert [action.event for action in b.drain()] == ["action_eat"]


def test_action_is_ignored_while_dragging():
    b = Behavior(random.Random(42))
    b.on_drag_start(DAY)
    b.drain()
    assert not b.start_action("wave", DAY + 0.1)
    assert b.mode == behavior.DRAG


def test_umbrella_raises_arm_but_held_props_stay_down():
    motion = RigMotion()
    state = PetState(mode="action", action="umbrella", prop="umbrella")
    for _ in range(40):
        motion.update(0.05, state, 0.1)
    assert motion.arm.value > 0.5
    for kind in ("drink", "eat", "read"):
        motion = RigMotion()
        state = PetState(mode="action", action=kind, prop=kind)
        for _ in range(40):
            motion.update(0.05, state, 0.1)
        assert motion.arm.value < 0.1, kind


def test_look_action_turns_the_upper_body():
    motion = RigMotion()
    state = PetState(mode="action", action="look")
    for index in range(20):
        motion.update(0.05, state, index * 0.05)
    assert abs(motion.body_angle.value) > 0.2


def test_props_and_action_overlays_are_visible():
    sprites = SpriteLibrary()
    sprites.preload()
    window = PetWindow(sprites)
    window.set_outfit("maid")
    window._rig = None
    window.apply_state(PetState())
    base = render(window)
    states = [
        PetState(mode="action", action="yawn"),
        PetState(mode="action", action="wave"),
        PetState(mode="action", action="drink", prop="drink"),
        PetState(mode="action", action="eat", prop="eat"),
        PetState(mode="action", action="read", prop="read"),
        PetState(mode="action", action="umbrella", prop="umbrella"),
    ]
    for state in states:
        window.apply_state(state)
        assert diff_count(base, render(window)) > 30, state.action

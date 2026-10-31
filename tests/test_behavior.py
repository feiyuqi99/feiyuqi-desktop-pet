from __future__ import annotations

import random
from datetime import datetime

from pet import behavior
from pet.behavior import Behavior, BehaviorContext
from pet.perception import time_band

DAY = datetime(2026, 1, 5, 10, 0).timestamp()
NIGHT = datetime(2026, 1, 5, 3, 0).timestamp()


def ctx(now: float, **kwargs) -> BehaviorContext:
    base = dict(
        now=now,
        time_band=time_band(now),
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


def test_head_click_pets():
    b = Behavior(random.Random(1))
    b.on_click(DAY, head=True)
    assert b.mode == behavior.PET
    assert b.drain()[0].event == "pet"
    state = b.tick(ctx(DAY + 0.1))
    assert state.frame == "happy"


def test_body_click_pokes():
    b = Behavior(random.Random(2))
    b.on_click(DAY, head=False)
    assert b.mode == behavior.POKE
    assert b.drain()[0].event == "click"


def test_three_rapid_clicks_annoy():
    b = Behavior(random.Random(3))
    for offset in (0.0, 1.0, 2.0):
        b.on_click(DAY + offset, head=False)
        b.drain()
    assert b.mode == behavior.ANNOYED
    state = b.tick(ctx(DAY + 3.0))
    assert state.facing == -1
    assert b.drain() == []
    state = b.tick(ctx(DAY + 11.0))
    assert state.mode == behavior.IDLE


def test_nap_and_return_greeting():
    b = Behavior(random.Random(4))
    state = b.tick(ctx(DAY, idle_seconds=700))
    assert state.mode == behavior.NAP
    assert state.zzz
    state = b.tick(ctx(DAY + 1, idle_seconds=0, gap=2000))
    assert state.mode == behavior.IDLE
    events = [action.event for action in b.drain()]
    assert "greet_return" in events


def test_night_sleep():
    b = Behavior(random.Random(5))
    state = b.tick(ctx(NIGHT, idle_seconds=400))
    assert state.mode == behavior.SLEEP
    assert state.zzz
    state = b.tick(ctx(NIGHT + 1, idle_seconds=0, gap=2000))
    assert state.mode == behavior.IDLE
    assert any(action.event in ("greet_return", "greet_long") for action in b.drain())


def test_quiet_blocks_wander():
    b = Behavior(random.Random(6))
    b.tick(ctx(DAY))
    b.next_wander = DAY
    state = b.tick(ctx(DAY + 0.1, quiet=True))
    assert state.mode == behavior.IDLE
    state = b.tick(ctx(DAY + 0.2, quiet=False))
    assert state.mode == behavior.WANDER
    assert abs(state.move_speed) == 60.0


def test_blink_frame():
    b = Behavior(random.Random(7))
    b.tick(ctx(DAY))
    b.next_blink = DAY + 0.5
    state = b.tick(ctx(DAY + 0.6))
    assert state.frame == "blink"


def test_drag_fast_wobble():
    b = Behavior(random.Random(8))
    b.on_drag_start(DAY)
    assert b.mode == behavior.DRAG
    assert b.drain()[0].event == "drag_start"
    b.on_drag_end(DAY + 1, speed=2500)
    actions = [action.event for action in b.drain()]
    assert actions == ["drag_fast"]
    state = b.tick(ctx(DAY + 2))
    assert b.mode == behavior.IDLE
    assert state is not None

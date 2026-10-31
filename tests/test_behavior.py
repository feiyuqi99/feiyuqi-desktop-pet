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
    b.on_click(DAY, "head")
    assert b.mode == behavior.PET
    assert b.drain()[0].event == "pet"
    state = b.tick(ctx(DAY + 0.1))
    assert state.frame == "happy"
    assert state.expression == "heart"


def test_body_click_pokes():
    b = Behavior(random.Random(2))
    b.on_click(DAY, "body")
    assert b.mode == behavior.POKE
    assert b.drain()[0].event == "click"


def test_face_click_blushes():
    b = Behavior(random.Random(20))
    b.on_click(DAY, "face")
    assert b.drain()[0].event == "face_poke"
    state = b.tick(ctx(DAY + 0.1))
    assert state.expression == "blush"


def test_hand_click_high_fives():
    b = Behavior(random.Random(21))
    b.on_click(DAY, "hand")
    assert b.drain()[0].event == "high_five"
    state = b.tick(ctx(DAY + 0.1))
    assert state.expression == "sparkle"
    assert state.hop < 0


def test_skirt_click_annoys_immediately():
    b = Behavior(random.Random(22))
    b.on_click(DAY, "skirt")
    assert b.mode == behavior.ANNOYED
    assert b.drain()[0].event == "skirt"
    state = b.tick(ctx(DAY + 0.2))
    assert state.facing == -1
    assert state.expression == "annoyed"


def test_feet_click_hops():
    b = Behavior(random.Random(23))
    b.on_click(DAY, "feet")
    assert b.drain()[0].event == "feet"
    state = b.tick(ctx(DAY + 0.1))
    assert state.hop < 0
    assert state.expression == "surprised"


def test_double_click_hops():
    b = Behavior(random.Random(24))
    b.on_double_click(DAY)
    state = b.tick(ctx(DAY + 0.1))
    assert state.hop < 0
    assert state.expression == "sparkle"


def test_landing_squashes():
    b = Behavior(random.Random(25))
    b.start_fall(DAY)
    assert b.mode == behavior.FALL
    b.land(DAY + 1.0)
    state = b.tick(ctx(DAY + 1.05))
    assert state.mode == behavior.IDLE
    assert state.squash_y < 1.0
    assert state.squash_x > 1.0


def test_three_rapid_clicks_annoy():
    b = Behavior(random.Random(3))
    for offset in (0.0, 1.0, 2.0):
        b.on_click(DAY + offset, "body")
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


def test_drag_hold_struggles():
    b = Behavior(random.Random(9))
    b.on_drag_start(DAY)
    b.drain()
    b.set_drag_motion(800.0, -400.0)
    state = b.tick(ctx(DAY + 0.1))
    assert state.expression == "surprised"
    assert state.tilt < 0
    assert state.squash_y > 1.0
    state = b.tick(ctx(DAY + 2.5))
    assert state.expression == "annoyed"
    assert [action.event for action in b.drain()] == ["drag_hold"]
    b.tick(ctx(DAY + 2.6))
    assert b.drain() == []


def test_music_makes_her_sway_with_note():
    b = Behavior(random.Random(11))
    b.tick(
        ctx(
            100.0,
            music_active=True,
            music_energy=0.8,
            music_pulse=1.0,
            music_tempo=120.0,
        )
    )
    state = b.tick(
        ctx(
            100.1,
            music_active=True,
            music_energy=0.8,
            music_pulse=1.0,
            music_tempo=120.0,
        )
    )
    assert state.note
    assert state.expression == "sparkle"
    assert abs(state.tilt) > 0.5


def test_soft_music_blinks_and_blushes():
    b = Behavior(random.Random(12))
    state = b.tick(
        ctx(
            DAY + 0.1,
            music_active=True,
            music_energy=0.05,
            music_tempo=70.0,
        )
    )
    assert state.note
    assert state.frame == "blink"
    assert state.expression == "blush"


def test_no_music_no_note():
    b = Behavior(random.Random(13))
    state = b.tick(ctx(DAY + 0.1))
    assert not state.note
    assert state.expression == "neutral"


def test_say_something_always_queues_talk():
    b = Behavior(random.Random(21))
    b.mode = behavior.ANNOYED
    b.annoyed_until = DAY + 10
    b.say(DAY)
    assert [action.event for action in b.drain()] == ["talk"]
    state = b.tick(ctx(DAY + 0.1))
    assert state.expression == "happy"


def test_music_sway_smooth_when_tempo_jitters():
    b = Behavior(random.Random(30))
    b.tick(ctx(DAY, music_active=True, music_energy=0.5, music_tempo=90.0))
    last_tilt = b.tick(
        ctx(DAY + 0.016, music_active=True, music_energy=0.5, music_tempo=90.0)
    ).tilt
    worst = 0.0
    now = DAY + 0.016
    for index in range(240):
        now += 0.016
        tempo = 200.0 if index % 2 else 80.0
        state = b.tick(
            ctx(now, music_active=True, music_energy=0.5, music_tempo=tempo)
        )
        worst = max(worst, abs(state.tilt - last_tilt))
        last_tilt = state.tilt
    assert worst < 0.5


def test_music_sway_capped_at_one_hertz():
    b = Behavior(random.Random(31))
    now = DAY
    previous = 0.0
    crossings = 0
    for _ in range(625):
        now += 0.016
        tilt = b.tick(
            ctx(now, music_active=True, music_energy=0.8, music_tempo=200.0)
        ).tilt
        if previous and tilt * previous < 0:
            crossings += 1
        if tilt:
            previous = tilt
    assert crossings <= 21


def test_fast_release_wobble_is_gentle():
    b = Behavior(random.Random(32))
    b.on_drag_end(DAY, 2000.0)
    b.drain()
    last_tilt = None
    worst = 0.0
    for index in range(50):
        state = b.tick(ctx(DAY + index * 0.016))
        if last_tilt is not None:
            worst = max(worst, abs(state.tilt - last_tilt))
        last_tilt = state.tilt
    assert worst < 1.0

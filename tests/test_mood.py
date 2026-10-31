from __future__ import annotations

import time

from pet import mood


def test_decay_steps():
    start = 1_000_000.0
    value, updated = mood.decay(70, start, start + 14 * 60)
    assert value == 70
    assert updated == start
    value, updated = mood.decay(70, start, start + 44 * 60)
    assert value == 68
    assert updated == start + 30 * 60
    value, updated = mood.decay(70, start, start + 45 * 60)
    assert value == 67
    assert updated == start + 45 * 60


def test_decay_clamps_at_zero():
    value, _ = mood.decay(5, 0, 100 * 60 * 60)
    assert value == 0


def test_change_and_tier():
    assert mood.change(99, 5) == 100
    assert mood.change(1, -5) == 0
    assert mood.tier(10) == "low"
    assert mood.tier(50) == "normal"
    assert mood.tier(90) == "happy"
    assert mood.label(90) == "心情不错"

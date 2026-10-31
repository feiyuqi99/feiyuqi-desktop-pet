from __future__ import annotations

from pet.animation import (
    BODY,
    DISPLAY_SCALE,
    DRAW_SIZE,
    FACE,
    FEET,
    FEET_X,
    HAND,
    HEAD,
    SKIRT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    part_at,
)


def test_part_regions():
    assert part_at(256, 90) == HEAD
    assert part_at(180, 180) == HEAD
    assert part_at(210, 210) == FACE
    assert part_at(256, 300) == BODY
    assert part_at(174, 330) == HAND
    assert part_at(256, 380) == SKIRT
    assert part_at(256, 450) == FEET


def test_shrunk_geometry():
    assert DISPLAY_SCALE == 0.4
    assert DRAW_SIZE == 204.8
    assert WINDOW_WIDTH == 248
    assert WINDOW_HEIGHT == 216
    assert FEET_X == 124
    assert FEET_X - DRAW_SIZE / 2 >= 0
    assert FEET_X + DRAW_SIZE / 2 <= WINDOW_WIDTH

from __future__ import annotations

from pet.support import pick_surface


def test_pick_nearest_surface_below():
    windows = [(0, 200, 900, 500), (0, 600, 900, 900)]
    assert pick_surface(windows, 100, 50, 1200) == 200
    assert pick_surface(windows, 100, 300, 1200) == 600
    assert pick_surface(windows, 100, 700, 1200) is None


def test_pick_ignores_surface_below_floor():
    windows = [(0, 900, 900, 1200)]
    assert pick_surface(windows, 100, 100, 800) is None


def test_pick_requires_horizontal_overlap():
    windows = [(500, 200, 900, 500)]
    assert pick_surface(windows, 100, 50, 1200) is None
    assert pick_surface(windows, 600, 50, 1200) == 200


def test_pick_takes_highest_surface():
    windows = [(0, 300, 900, 700), (0, 600, 900, 900)]
    assert pick_surface(windows, 100, 50, 1200) == 300

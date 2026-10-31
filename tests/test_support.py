from __future__ import annotations

from pet.support import pick_surface, pick_surface_below, pick_standing_surface


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


def stack(*rects):
    return [(index + 1, rect) for index, rect in enumerate(rects)]


def test_input_top_is_landing_surface():
    windows = stack((0, 100, 900, 800), (0, 900, 900, 1000))
    inputs = [(100, 600, 400, 640, 1)]
    assert pick_surface_below(windows, inputs, 200, 300, 1200) == 600
    assert pick_surface_below(windows, inputs, 500, 300, 1200) == 900
    assert pick_surface_below(windows, inputs, 200, 650, 1200) == 900


def test_occluded_input_is_ignored():
    windows = stack((0, 100, 900, 900), (0, 200, 900, 1000))
    inputs = [(100, 600, 400, 640, 2)]
    assert pick_surface_below(windows, inputs, 200, 300, 1200) is None


def test_standing_on_input():
    windows = stack((0, 100, 900, 800))
    inputs = [(100, 600, 400, 640, 1)]
    assert pick_standing_surface(windows, inputs, 200, 600) == 600
    assert pick_standing_surface(windows, inputs, 200, 500) is None
    assert pick_standing_surface(windows, inputs, 500, 600) is None
    assert pick_standing_surface(windows, inputs, 200, 606) is None


def test_standing_picks_nearest_surface():
    windows = stack((0, 596, 900, 900))
    inputs = [(100, 600, 400, 640, 1)]
    assert pick_standing_surface(windows, inputs, 200, 600) == 600


def test_input_under_other_window_is_not_standable():
    windows = stack((0, 300, 400, 900), (0, 100, 900, 1000))
    inputs = [(100, 600, 300, 640, 2)]
    assert pick_standing_surface(windows, inputs, 200, 600) is None


def test_standing_prefers_nearest_input():
    windows = stack((0, 100, 900, 1000))
    inputs = [(100, 600, 400, 640, 1), (100, 602, 400, 642, 1)]
    assert pick_standing_surface(windows, inputs, 200, 603) == 602



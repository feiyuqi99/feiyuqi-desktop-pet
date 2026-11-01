from __future__ import annotations

import math

import pytest

from pet import physics
from pet.behavior import Behavior

DT = 1 / 21
FLIGHT_DT = 1 / 60
TARGET = 400.0
TOP = 0.0


def simulate(
    initial_vy: float,
    start_offset: float = 1.0,
    initial_vx: float = 0.0,
    frames: int = 1200,
    dt: float = DT,
):
    vx, vy = physics.limit_throw(initial_vx, initial_vy)
    x, y = 0.0, TARGET - start_offset
    heights = []
    xs = []
    t = 0.0
    landed = None
    for _ in range(frames):
        result = physics.step_flight(
            x, y, vx, vy, TARGET, TOP, -1e6, 1e6, dt
        )
        x, y, vx, vy = result.x, result.y, result.vx, result.vy
        t += dt
        heights.append(TARGET - y)
        xs.append(x)
        if result.landed:
            landed = t
            break
    return heights, xs, landed


def _drops(heights):
    return [
        heights[i] - heights[i + 1]
        for i in range(len(heights) - 1)
        if heights[i + 1] > 0
    ]


def test_launch_speed_is_bounded_on_both_axes():
    vx, vy = physics.limit_throw(1800.0, 1600.0)
    assert math.hypot(vx, vy) == pytest.approx(physics.MAX_THROW_SPEED)
    assert vx > 0.0 and vy > 0.0
    assert physics.limit_throw(100.0, -80.0) == (100.0, -80.0)


def test_side_throw_never_jumps_more_than_a_few_pixels_per_frame():
    vx, vy = physics.limit_throw(1800.0, 0.0)
    result = physics.step_flight(
        0.0, 0.0, vx, vy, TARGET, TOP, -1e6, 1e6, 1 / 60
    )
    assert result.x <= 32.0


def test_hard_throw_falls_without_rebound():
    heights, _, landed = simulate(900.0, start_offset=200.0)
    assert landed is not None
    assert all(a >= b - 1e-6 for a, b in zip(heights, heights[1:])), heights
    assert _drops(heights)[-1] <= 9.0


def test_free_fall_is_floaty():
    heights, _, landed = simulate(0.0, start_offset=200.0)
    assert landed is not None
    assert landed >= 0.9
    assert max(_drops(heights)) <= 32.0


def test_final_approach_eases_in_instead_of_slamming():
    heights, _, _ = simulate(0.0, start_offset=200.0)
    tail = _drops(heights)[-3:]
    assert tail, "never approached the floor"
    assert tail[-1] <= 4.0, tail
    assert tail == sorted(tail, reverse=True), tail


def test_gentle_drop_settles_without_bouncing():
    heights, _, landed = simulate(0.0, start_offset=40.0)
    assert landed is not None
    assert _drops(heights)[-1] <= 4.0


def test_slow_wall_contact_stops_instead_of_bouncing():
    result = physics.step_flight(
        799.0, 0.0, 50.0, 0.0, TARGET, TOP, 0.0, 800.0, 0.05
    )
    assert result.x <= 800.0
    assert result.vx == 0.0


def test_fast_throw_cannot_tunnel_through_a_wall_on_a_late_tick():
    result = physics.step_flight(
        795.0, 0.0, 900.0, 0.0, TARGET, TOP, 0.0, 800.0, 0.12
    )
    assert result.x <= 800.0


def test_flight_constants_are_soft():
    assert physics.GRAVITY <= 700.0
    assert physics.MAX_FALL_SPEED <= 800.0
    assert physics.MAX_THROW_SPEED <= 1900.0
    assert physics.CEILING_RESTITUTION <= 0.15
    assert physics.WALL_RESTITUTION <= 0.4
    assert physics.SOFT_LAND_DIST >= 30.0
    assert physics.TOUCH_SPEED <= 40.0
    assert physics.MAX_SUBSTEP <= 1 / 60


def test_landing_cushion_is_long_and_slow():
    b = Behavior()
    b.land(20.0)
    assert b.squash_until == pytest.approx(20.65)
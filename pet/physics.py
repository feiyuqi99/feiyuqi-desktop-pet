from __future__ import annotations

import math
from dataclasses import dataclass

# 纯函数抛掷物理，参数参考开源桌宠：
# - QCYTSN/ds-local-pet：总速度上限 + 1/120 子步 + 指数摩擦
# - MerZlin/dsh-pet-indesktop：低速贴墙/贴地直接停，避免边角反复弹
GRAVITY = 620.0
MAX_FALL_SPEED = 720.0
MAX_THROW_SPEED = 1800.0
CEILING_RESTITUTION = 0.12
WALL_RESTITUTION = 0.3
WALL_STOP_SPEED = 80.0
AIR_DRAG = 0.4
GROUND_FRICTION = 6.0
GROUND_STOP_SPEED = 24.0
AIR_STOP_SPEED = 8.0
SOFT_LAND_DIST = 34.0
SOFT_LAND_TAU = 0.09
TOUCH_SPEED = 36.0
MAX_SUBSTEP = 1 / 120


@dataclass(frozen=True, slots=True)
class FlightStep:
    x: float
    y: float
    vx: float
    vy: float
    landed: bool


def limit_throw(vx: float, vy: float, cap: float = MAX_THROW_SPEED) -> tuple[float, float]:
    speed = math.hypot(vx, vy)
    if speed <= cap or speed <= 0.0:
        return vx, vy
    scale = cap / speed
    return vx * scale, vy * scale


def damp_ground(vx: float, dt: float) -> float:
    vx *= max(0.0, 1.0 - GROUND_FRICTION * dt)
    return 0.0 if abs(vx) < GROUND_STOP_SPEED else vx


def reflect_wall(vx: float) -> float:
    if abs(vx) < WALL_STOP_SPEED:
        return 0.0
    return -vx * WALL_RESTITUTION


def step_flight(
    x: float,
    y: float,
    vx: float,
    vy: float,
    target_y: float,
    top_y: float,
    left_x: float,
    right_x: float,
    dt: float,
) -> FlightStep:
    remaining = max(0.0, min(0.1, dt))
    landed = False
    while remaining > 1e-9 and not landed:
        step = min(remaining, MAX_SUBSTEP)
        remaining -= step

        vy = min(MAX_FALL_SPEED, vy + GRAVITY * step)
        if vy > 0.0:
            dist = target_y - y
            if 0.0 < dist < SOFT_LAND_DIST:
                vy = min(vy, max(TOUCH_SPEED, dist / SOFT_LAND_TAU))

        x += vx * step
        y += vy * step

        if x < left_x:
            x = left_x
            vx = reflect_wall(abs(vx))
        elif x > right_x:
            x = right_x
            vx = reflect_wall(-abs(vx))
        if y < top_y:
            y = top_y
            vy = abs(vy) * CEILING_RESTITUTION
        if y >= target_y and vy > 0.0:
            y = target_y
            vy = 0.0
            landed = True

        vx *= max(0.0, 1.0 - AIR_DRAG * step)
        if abs(vx) < AIR_STOP_SPEED:
            vx = 0.0
    return FlightStep(x, y, vx, vy, landed)
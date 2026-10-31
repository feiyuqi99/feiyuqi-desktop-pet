from __future__ import annotations

DECAY_INTERVAL = 15 * 60


def clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, int(value)))


def change(value: int, delta: int) -> int:
    return clamp(value + delta)


def decay(value: int, updated_at: float, now: float) -> tuple[int, float]:
    value = clamp(value)
    if now <= updated_at:
        return value, updated_at
    steps = int((now - updated_at) // DECAY_INTERVAL)
    if steps <= 0:
        return value, updated_at
    return clamp(value - steps), updated_at + steps * DECAY_INTERVAL


def tier(value: int) -> str:
    if value < 30:
        return "low"
    if value >= 70:
        return "happy"
    return "normal"


def label(value: int) -> str:
    return {"low": "有点低落", "normal": "还好", "happy": "心情不错"}[tier(value)]

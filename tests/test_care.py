from __future__ import annotations

from datetime import datetime

from pet.care import Care, CareState

MINUTE = 60.0
HOUR = 60 * MINUTE


def ts(hour: int, minute: int = 0, second: int = 0, day: int = 5) -> float:
    return datetime(2026, 1, day, hour, minute, second).timestamp()


def make(now: float, state: CareState | None = None, **flags) -> Care:
    return Care(now, state or CareState(), **flags)


def tick(care: Care, now: float, idle: float = 0.0, quiet: bool = False):
    return care.tick(now, idle_seconds=idle, quiet=quiet)


def events(care: Care, now: float, idle: float = 0.0, quiet: bool = False):
    alert = tick(care, now, idle, quiet)
    return alert.event if alert is not None else None


def test_startup_band_is_covered_by_the_first_hello():
    care = make(ts(9, 0), eyes=False, water=False)
    assert events(care, ts(9, 0)) is None
    assert events(care, ts(10, 59)) is None
    assert events(care, ts(11, 0)) == "care_noon"
    assert events(care, ts(11, 1)) is None


def test_morning_greeting_fires_once_per_day():
    care = make(ts(6, 50), eyes=False, water=False)
    assert events(care, ts(7, 0)) == "care_morning"
    assert events(care, ts(7, 30)) is None
    assert events(care, ts(7, 0, day=6)) == "care_morning"


def test_no_greeting_at_night():
    care = make(ts(22, 50), eyes=False, water=False)
    assert events(care, ts(23, 0)) is None
    assert events(care, ts(23, 30)) is None
    assert events(care, ts(6, 0, day=6)) is None
    assert events(care, ts(7, 0, day=6)) == "care_morning"


def test_lunch_is_reminded_once_inside_the_window():
    care = make(ts(11, 50), eyes=False, water=False)
    assert events(care, ts(12, 0)) == "care_lunch"
    assert events(care, ts(12, 5)) is None
    assert events(care, ts(12, 44)) is None
    assert events(care, ts(12, 46)) is None
    assert "lunch" in care.state.meals
    assert events(care, ts(12, 0, day=6)) == "care_lunch"


def test_missed_meal_window_is_skipped():
    care = make(ts(12, 50))
    assert events(care, ts(12, 51)) is None
    assert events(care, ts(18, 0)) == "care_dinner"


def test_quiet_defers_meal_until_it_can_speak():
    care = make(ts(11, 50))
    assert events(care, ts(12, 0), quiet=True) is None
    assert events(care, ts(12, 20)) == "care_lunch"


def test_meal_window_closed_while_quiet_is_not_reminded_late():
    care = make(ts(11, 50), eyes=False, water=False)
    assert events(care, ts(12, 0), quiet=True) is None
    assert events(care, ts(12, 46)) is None


def test_eyes_reminder_every_thirty_minutes():
    care = make(ts(9, 0), water=False)
    assert events(care, ts(9, 30)) == "care_eyes"
    assert events(care, ts(9, 31)) is None
    assert events(care, ts(10, 30)) == "care_eyes"


def test_eyes_and_water_due_together_merge_into_one_line():
    care = make(ts(9, 0), greet=False)
    assert events(care, ts(10, 0)) == "care_both"
    assert events(care, ts(10, 30)) == "care_eyes"
    assert events(care, ts(11, 0)) == "care_both"


def test_water_reminder_when_eyes_are_off():
    care = make(ts(9, 0), eyes=False)
    assert events(care, ts(9, 30)) is None
    assert events(care, ts(10, 0)) == "care_water"


def test_meal_is_a_break_and_restarts_the_interval_timers():
    care = make(ts(11, 50))
    assert events(care, ts(12, 0)) == "care_lunch"
    assert events(care, ts(12, 5)) is None
    assert events(care, ts(12, 31)) == "care_eyes"


def test_dinner_suppresses_the_evening_greeting():
    care = make(ts(17, 50))
    assert events(care, ts(18, 0)) == "care_dinner"
    assert events(care, ts(18, 1)) is None
    assert "evening" in care.state.greeted


def test_greeting_comes_before_water_and_delays_it():
    care = make(ts(10, 0), eyes=False)
    assert events(care, ts(11, 0)) == "care_noon"
    assert events(care, ts(11, 1)) is None
    assert events(care, ts(11, 2)) == "care_water"


def test_away_resets_the_interval_timers():
    care = make(ts(9, 0))
    assert events(care, ts(9, 29), idle=400) is None
    assert events(care, ts(9, 30), idle=5) is None
    assert events(care, ts(9, 59), idle=1) is None
    assert events(care, ts(10, 0), idle=1) == "care_eyes"


def test_disabled_care_is_silent():
    care = make(ts(9, 0), greet=False, eyes=False, water=False, meal=False)
    assert events(care, ts(9, 30)) is None
    assert events(care, ts(10, 0)) is None
    assert events(care, ts(11, 0)) is None
    assert events(care, ts(12, 0)) is None


def test_enabling_eyes_starts_a_fresh_interval():
    care = make(ts(9, 0), eyes=False, water=False)
    assert events(care, ts(9, 30)) is None
    care.set_eyes(True, ts(9, 40))
    assert events(care, ts(9, 41)) is None
    assert events(care, ts(10, 10)) == "care_eyes"


def test_enabling_greetings_does_not_fire_mid_band():
    care = make(ts(11, 5), greet=False)
    assert events(care, ts(11, 6)) is None
    care.set_greet(True, ts(11, 10))
    assert events(care, ts(11, 11)) is None
    assert events(care, ts(14, 0)) == "care_afternoon"


def test_saved_state_survives_restart():
    state = CareState(
        day="2026-01-05",
        greeted=["morning"],
        meals=["breakfast"],
    )
    care = make(ts(9, 0), state)
    assert events(care, ts(9, 1)) is None
    assert events(care, ts(12, 0)) == "care_lunch"


def test_yesterdays_state_is_reset():
    state = CareState(
        day="2026-01-04",
        greeted=["morning", "noon", "afternoon", "evening"],
        meals=["breakfast", "lunch", "dinner"],
    )
    care = make(ts(9, 0), state)
    assert state.day == "2026-01-05"
    assert state.greeted == ["morning"]
    assert state.meals == []
    assert events(care, ts(11, 0)) == "care_noon"


CARE_EVENTS = {
    "care_morning",
    "care_noon",
    "care_afternoon",
    "care_evening",
    "care_breakfast",
    "care_lunch",
    "care_dinner",
    "care_eyes",
    "care_water",
    "care_both",
}


def test_every_care_event_has_lines():
    from pet.lines import LINES

    for event in CARE_EVENTS:
        count = sum(1 for line in LINES if line.event == event)
        assert count >= 2, event


def test_care_events_are_alerts_without_followups():
    from pet.dialogue import ALERT_EVENTS

    assert CARE_EVENTS <= ALERT_EVENTS

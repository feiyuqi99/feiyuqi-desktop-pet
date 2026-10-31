from __future__ import annotations

from datetime import datetime

from pet.companion import Companion


def ts(hour: int, minute: int = 0, second: int = 0) -> float:
    return datetime(2026, 1, 5, hour, minute, second).timestamp()


def test_hourly_fires_once_on_the_hour():
    now = ts(10, 30)
    companion = Companion(now, sit_enabled=False)
    assert companion.tick(ts(10, 59, 59)) == []
    alerts = companion.tick(ts(11, 0))
    assert [alert.kind for alert in alerts] == ["hourly"]
    assert companion.tick(ts(11, 0, 30)) == []
    assert [alert.kind for alert in companion.tick(ts(12, 0))] == ["hourly"]


def test_no_hourly_at_startup_on_the_hour():
    now = ts(11, 0)
    companion = Companion(now, sit_enabled=False)
    assert companion.tick(now) == []
    assert [alert.kind for alert in companion.tick(ts(12, 0))] == ["hourly"]


def test_sit_reminder():
    now = ts(9, 0)
    companion = Companion(now, sit_enabled=True)
    assert companion.tick(now + 2699) == []
    assert [alert.kind for alert in companion.tick(now + 2700)] == ["sit"]
    assert companion.tick(now + 2701) == []
    assert [alert.kind for alert in companion.tick(now + 2700 + 2700)] == ["sit"]


def test_pomodoro_cycle():
    now = ts(9, 0)
    companion = Companion(now)
    assert companion.start_focus(now).event == "pomo_start"
    assert companion.phase == "focus"
    assert companion.tick(now + 1499) == []
    alerts = companion.tick(now + 1500)
    assert [alert.event for alert in alerts] == ["pomo_end"]
    assert companion.phase == "break"
    alerts = companion.tick(now + 1800)
    assert [alert.event for alert in alerts] == ["pomo_break_end"]
    assert companion.phase == "idle"
    assert companion.ends_at is None


def test_stop_and_restore():
    now = ts(9, 0)
    companion = Companion(now)
    companion.start_focus(now)
    companion.stop()
    assert companion.phase == "idle"
    assert companion.remaining(now) == 0

    running = Companion(now, phase="focus", ends_at=now + 100)
    assert running.restore(now + 50) is None
    alert = running.restore(now + 150)
    assert alert is not None and alert.event == "pomo_missed"
    assert running.phase == "idle"

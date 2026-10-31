from __future__ import annotations

import random
from datetime import datetime

from pet.config import Config
from pet.dialogue import DialogueContext, DialogueEngine
from pet.lines import LINES, Line
from pet.memory import Memory
from pet.perception import time_band


def context(now: float, **kwargs) -> DialogueContext:
    base = dict(
        now=now,
        time_band=time_band(now),
        activity="coding",
        idle_seconds=0.0,
        quiet=False,
        mood=70,
        relationship="new",
        chattiness="normal",
    )
    base.update(kwargs)
    return DialogueContext(**base)


def test_click_rate_limit():
    now = datetime(2026, 1, 5, 10, 0).timestamp()
    memory = Memory()
    engine = DialogueEngine(LINES, memory, random.Random(3))
    first = engine.maybe_speak("click", context(now), allow_silence=False)
    assert first is not None
    second = engine.maybe_speak("click", context(now + 2), allow_silence=False)
    assert second is None
    third = engine.maybe_speak("click", context(now + 10), allow_silence=False)
    assert third is not None


def test_quiet_suppresses_but_alerts_work():
    now = datetime(2026, 1, 5, 10, 0).timestamp()
    memory = Memory()
    engine = DialogueEngine(LINES, memory, random.Random(4))
    quiet = context(now, quiet=True)
    assert engine.maybe_speak("click", quiet, allow_silence=False) is None
    alert = engine.alert("hourly", quiet)
    assert alert is not None


def test_unsolicited_interval():
    now = datetime(2026, 1, 5, 10, 0).timestamp()
    memory = Memory()
    engine = DialogueEngine(LINES, memory, random.Random(5))
    first = engine.maybe_speak("idle", context(now), allow_silence=False)
    assert first is not None
    second = engine.maybe_speak("idle", context(now + 60), allow_silence=False)
    assert second is None
    third = engine.maybe_speak("idle", context(now + 300), allow_silence=False)
    assert third is not None


def test_tag_filtering():
    now = datetime(2026, 1, 5, 10, 0).timestamp()
    memory = Memory()
    only_coding = [Line("编码台词", "click", frozenset({"coding"}))]
    engine = DialogueEngine(only_coding, memory, random.Random(6))
    assert engine.pick_line("click", context(now, activity="coding")) is not None
    assert engine.pick_line("click", context(now, activity="browser")) is None


def test_no_repeat_within_window():
    now = datetime(2026, 1, 5, 10, 0).timestamp()
    memory = Memory()
    lines = [Line(f"第{index}句台词", "click") for index in range(15)]
    engine = DialogueEngine(lines, memory, random.Random(7))
    seen = []
    for index in range(10):
        speech = engine.maybe_speak("click", context(now + index * 10), allow_silence=False)
        assert speech is not None
        assert speech.text not in seen
        seen.append(speech.text)


def test_alert_bypasses_quiet_and_has_no_followup():
    now = datetime(2026, 1, 5, 10, 0).timestamp()
    memory = Memory()
    engine = DialogueEngine(LINES, memory, random.Random(8))
    speech = engine.alert("sit", context(now, quiet=True))
    assert speech is not None
    assert speech.followup is None
    assert speech.delay_ms == 0

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from .lines import FOLLOWUPS, Line
from .memory import Memory
from .mood import tier
from .persona import followup_chance, postprocess, silence_chance, unsolicited_interval

ALERT_EVENTS = {"hourly", "sit", "pomo_start", "pomo_break", "pomo_end", "pomo_break_end", "pomo_stop", "pomo_missed"}
UNSOLICITED_EVENTS = {
    "idle",
    "coding",
    "affection",
    "late_night",
    "late_streak",
    "meeting_end",
    "wander_end",
    "anniversary_7",
    "anniversary_30",
    "anniversary_100",
}
SILENT_EVENTS = {"click", "pet", "double", "face_poke", "high_five", "skirt", "feet", "land"}
GLOBAL_GAP = 6.0


@dataclass
class DialogueContext:
    now: float
    time_band: str
    activity: str
    idle_seconds: float
    quiet: bool
    mood: int
    relationship: str
    chattiness: str = "normal"
    gap: float = 0.0
    flags: set[str] = field(default_factory=set)


@dataclass
class Speech:
    text: str
    event: str
    delay_ms: int
    followup: str | None = None


class DialogueEngine:
    def __init__(self, lines: list[Line], memory: Memory, rng: random.Random | None = None) -> None:
        self.lines = list(lines)
        self.memory = memory
        self.rng = rng or random.Random()
        self.last_spoken = 0.0
        self.last_unsolicited = 0.0
        self.recent: deque[str] = deque(maxlen=12)
        self.openers: deque[str] = deque(maxlen=3)

    def context_flags(self, ctx: DialogueContext) -> set[str]:
        moment = datetime.fromtimestamp(ctx.now)
        flags = {
            ctx.time_band,
            ctx.activity,
            ctx.relationship,
            tier(ctx.mood),
            *ctx.flags,
        }
        if moment.weekday() >= 5:
            flags.add("weekend")
        if moment.hour >= 23 or moment.hour < 2:
            flags.add("late_hours")
        if ctx.gap >= 1800:
            flags.add("return")
        if ctx.gap >= 86400:
            flags.add("long_absence")
        return flags

    def _eligible(self, line: Line, flags: set[str], event: str) -> bool:
        return line.event == event and all(tag in flags for tag in line.tags)

    def pick_line(self, event: str, ctx: DialogueContext) -> Line | None:
        flags = self.context_flags(ctx)
        remembered = set(self.memory.last_lines.get(event, [])[-12:])
        recent = set(self.recent)
        pool = [line for line in self.lines if self._eligible(line, flags, event)]
        if not pool:
            return None
        candidates = [line for line in pool if line.text not in remembered and line.text not in recent]
        if not candidates:
            candidates = [line for line in pool if line.text not in remembered]
        if not candidates:
            candidates = pool
        fresh_openers = [line for line in candidates if line.text[:2] not in self.openers]
        if fresh_openers:
            candidates = fresh_openers
        weights = [max(0.1, line.weight) for line in candidates]
        return self.rng.choices(candidates, weights=weights, k=1)[0]

    def _can_speak(self, event: str, ctx: DialogueContext, force: bool) -> bool:
        if force or event in ALERT_EVENTS:
            return True
        if ctx.quiet:
            return False
        if ctx.now - self.last_spoken < GLOBAL_GAP:
            return False
        if event in UNSOLICITED_EVENTS and ctx.now - self.last_unsolicited < unsolicited_interval(ctx.chattiness):
            return False
        return True

    def _record(self, event: str, text: str, ctx: DialogueContext, force: bool) -> None:
        self.last_spoken = ctx.now
        if event in UNSOLICITED_EVENTS and not force:
            self.last_unsolicited = ctx.now
        self.memory.note_line(event, text)
        self.recent.append(text)
        self.openers.append(text[:2])

    def maybe_speak(
        self,
        event: str,
        ctx: DialogueContext,
        force: bool = False,
        allow_silence: bool = True,
    ) -> Speech | None:
        if not self._can_speak(event, ctx, force):
            return None
        if allow_silence and event in SILENT_EVENTS and self.rng.random() < silence_chance(ctx.chattiness):
            return None
        line = self.pick_line(event, ctx)
        if line is None:
            return None
        text = postprocess(line.text, self.memory, ctx.now)
        followup = None
        if event not in ALERT_EVENTS and self.rng.random() < followup_chance(ctx.chattiness):
            followup = postprocess(self.rng.choice(FOLLOWUPS), self.memory, ctx.now)
        self._record(event, text, ctx, force)
        return Speech(
            text=text,
            event=event,
            delay_ms=0 if force else self.rng.randint(180, 450),
            followup=followup,
        )

    def alert(self, event: str, ctx: DialogueContext, fallback: str | None = None) -> Speech | None:
        speech = self.maybe_speak(event, ctx, force=True, allow_silence=False)
        if speech is None and fallback:
            self._record(event, fallback, ctx, True)
            return Speech(fallback, event, 0)
        return speech

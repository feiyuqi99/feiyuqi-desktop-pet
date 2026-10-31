from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .config import MEMORY_PATH, atomic_write_json, backup_corrupt


def _date_key(now: float) -> str:
    return datetime.fromtimestamp(now).date().isoformat()


@dataclass
class Memory:
    version: int = 1
    pet_name: str = "小橘"
    user_name: str = ""
    first_seen: float = 0.0
    last_seen: float = 0.0
    days_seen: list[str] = field(default_factory=list)
    total_interactions: int = 0
    affection: int = 0
    last_lines: dict[str, list[str]] = field(default_factory=dict)
    active_hours: dict[str, int] = field(default_factory=dict)
    late_night_days: list[str] = field(default_factory=list)
    coding_days: int = 0
    last_coding_day: str = ""
    events: list[dict[str, str]] = field(default_factory=list)
    greeted_today: str = ""
    last_activity: str = "other"

    @property
    def is_new(self) -> bool:
        return self.first_seen <= 0

    @property
    def days_known(self) -> int:
        return max(1, len(set(self.days_seen)))

    @property
    def relationship(self) -> str:
        days = self.days_known
        if self.affection >= 60 and days >= 5:
            return "close"
        if self.affection >= 20 or days >= 3:
            return "familiar"
        return "new"

    @property
    def relationship_label(self) -> str:
        return {"new": "初识", "familiar": "熟悉", "close": "亲近"}[self.relationship]

    def touch_session(self, now: float) -> float:
        gap = 0.0 if self.last_seen <= 0 else max(0.0, now - self.last_seen)
        if self.first_seen <= 0:
            self.first_seen = now
        today = _date_key(now)
        if today not in self.days_seen:
            self.days_seen.append(today)
            self.days_seen = self.days_seen[-400:]
        self.last_seen = now
        return gap

    def add_interaction(self, count: int = 1) -> None:
        self.total_interactions += max(0, count)

    def bump_affection(self, delta: int) -> None:
        self.affection = max(0, min(100, self.affection + delta))

    def note_line(self, event: str, text: str) -> None:
        lines = self.last_lines.setdefault(event, [])
        lines.append(text)
        del lines[:-12]

    def record_event(self, kind: str, now: float, note: str = "") -> None:
        self.events.append(
            {"at": datetime.fromtimestamp(now).isoformat(timespec="minutes"), "kind": kind, "note": note}
        )
        self.events = self.events[-20:]
        cutoff = datetime.fromtimestamp(now).date() - timedelta(days=30)
        kept = []
        for event in self.events:
            try:
                if date.fromisoformat(event["at"][:10]) >= cutoff:
                    kept.append(event)
            except (KeyError, ValueError):
                continue
        self.events = kept

    def has_event(self, kind: str, within_days: int, now: float) -> bool:
        cutoff = datetime.fromtimestamp(now).date() - timedelta(days=within_days)
        for event in self.events:
            if event.get("kind") != kind:
                continue
            try:
                if date.fromisoformat(event["at"][:10]) >= cutoff:
                    return True
            except (KeyError, ValueError):
                continue
        return False

    def observe(self, activity: str, now: float) -> None:
        moment = datetime.fromtimestamp(now)
        hour_key = str(moment.hour)
        self.active_hours[hour_key] = self.active_hours.get(hour_key, 0) + 1
        today = moment.date().isoformat()
        if moment.hour >= 23 or moment.hour < 2:
            if today not in self.late_night_days:
                self.late_night_days.append(today)
                self.late_night_days = self.late_night_days[-60:]
        if activity == "coding" and self.last_coding_day != today:
            self.coding_days += 1
            self.last_coding_day = today
        self.last_activity = activity

    def late_night_streak(self, now: float) -> int:
        days = set(self.late_night_days)
        cursor = datetime.fromtimestamp(now).date()
        if cursor.isoformat() not in days:
            cursor -= timedelta(days=1)
        streak = 0
        while cursor.isoformat() in days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def most_active_hour(self) -> int | None:
        if not self.active_hours:
            return None
        hour, count = max(self.active_hours.items(), key=lambda item: item[1])
        if count < 8:
            return None
        return int(hour)

    def mark_greeted(self, now: float) -> None:
        self.greeted_today = _date_key(now)

    def was_greeted_today(self, now: float) -> bool:
        return self.greeted_today == _date_key(now)


def _coerce_memory(raw: dict[str, Any]) -> Memory:
    memory = Memory()
    for key in Memory.__dataclass_fields__:
        if key in raw:
            setattr(memory, key, raw[key])
    memory.first_seen = float(memory.first_seen or 0.0)
    memory.last_seen = float(memory.last_seen or 0.0)
    memory.total_interactions = int(memory.total_interactions or 0)
    memory.affection = max(0, min(100, int(memory.affection or 0)))
    memory.days_seen = [str(item) for item in memory.days_seen][-400:] if isinstance(memory.days_seen, list) else []
    memory.late_night_days = (
        [str(item) for item in memory.late_night_days][-60:] if isinstance(memory.late_night_days, list) else []
    )
    memory.events = memory.events[-20:] if isinstance(memory.events, list) else []
    if not isinstance(memory.last_lines, dict):
        memory.last_lines = {}
    if not isinstance(memory.active_hours, dict):
        memory.active_hours = {}
    return memory


def load_memory(path: Path = MEMORY_PATH) -> Memory:
    if not path.exists():
        return Memory()
    try:
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raise ValueError("memory root is not an object")
        return _coerce_memory(raw)
    except (OSError, ValueError, json.JSONDecodeError):
        backup_corrupt(path)
        return Memory()


def save_memory(memory: Memory, path: Path = MEMORY_PATH) -> None:
    atomic_write_json(path, asdict(memory))

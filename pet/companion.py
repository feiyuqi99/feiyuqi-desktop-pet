from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

FOCUS_SECONDS = 25 * 60
BREAK_SECONDS = 5 * 60
SIT_SECONDS = 45 * 60


@dataclass
class Alert:
    kind: str
    event: str


class Companion:
    def __init__(
        self,
        now: float,
        sit_enabled: bool = True,
        hourly_enabled: bool = True,
        phase: str = "idle",
        ends_at: float | None = None,
    ) -> None:
        self.sit_enabled = sit_enabled
        self.hourly_enabled = hourly_enabled
        self.phase = phase if phase in ("idle", "focus", "break") else "idle"
        self.ends_at = float(ends_at) if ends_at and self.phase != "idle" else None
        self.next_sit_at = now + SIT_SECONDS
        self._last_hour_key = self._hour_key(now)

    @staticmethod
    def _hour_key(now: float) -> str:
        return datetime.fromtimestamp(now).strftime("%Y-%m-%d-%H")

    def reset_sit(self, now: float) -> None:
        self.next_sit_at = now + SIT_SECONDS

    def start_focus(self, now: float) -> Alert:
        self.phase = "focus"
        self.ends_at = now + FOCUS_SECONDS
        return Alert("pomo_start", "pomo_start")

    def start_break(self, now: float) -> Alert:
        self.phase = "break"
        self.ends_at = now + BREAK_SECONDS
        return Alert("pomo_break", "pomo_break")

    def stop(self) -> None:
        self.phase = "idle"
        self.ends_at = None

    def remaining(self, now: float) -> int:
        if self.phase == "idle" or self.ends_at is None:
            return 0
        return max(0, int(self.ends_at - now))

    def phase_label(self) -> str:
        return {"idle": "空闲", "focus": "专注 25 分钟", "break": "休息 5 分钟"}[self.phase]

    def restore(self, now: float) -> Alert | None:
        if self.phase == "idle":
            return None
        if self.ends_at is None or now >= self.ends_at:
            self.stop()
            return Alert("pomo_missed", "pomo_missed")
        return None

    def tick(self, now: float) -> list[Alert]:
        alerts: list[Alert] = []
        if self.hourly_enabled:
            key = self._hour_key(now)
            if datetime.fromtimestamp(now).minute == 0 and key != self._last_hour_key:
                alerts.append(Alert("hourly", "hourly"))
            self._last_hour_key = key
        if self.sit_enabled and now >= self.next_sit_at:
            alerts.append(Alert("sit", "sit"))
            self.next_sit_at = now + SIT_SECONDS
        if self.phase == "focus" and self.ends_at is not None and now >= self.ends_at:
            self.phase = "break"
            self.ends_at = now + BREAK_SECONDS
            alerts.append(Alert("pomo_end", "pomo_end"))
        elif self.phase == "break" and self.ends_at is not None and now >= self.ends_at:
            self.phase = "idle"
            self.ends_at = None
            alerts.append(Alert("pomo_break_end", "pomo_break_end"))
        return alerts

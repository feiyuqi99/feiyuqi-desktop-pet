from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

EYE_SECONDS = 30 * 60
WATER_SECONDS = 60 * 60
MEAL_WINDOW_MINUTES = 45
AWAY_SECONDS = 10 * 60
ALERT_GAP = 90.0
SLEEP_START = 2
SLEEP_END = 6

GREETINGS = (
    (7, "morning", "care_morning"),
    (11, "noon", "care_noon"),
    (14, "afternoon", "care_afternoon"),
    (18, "evening", "care_evening"),
)
MEALS = (
    (8, "breakfast", "care_breakfast"),
    (12, "lunch", "care_lunch"),
    (18, "dinner", "care_dinner"),
)


@dataclass
class CareState:
    day: str = ""
    greeted: list[str] = field(default_factory=list)
    meals: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CareAlert:
    kind: str
    event: str


class Care:
    def __init__(
        self,
        now: float,
        state: CareState,
        greet: bool = True,
        eyes: bool = True,
        water: bool = True,
        meal: bool = True,
    ) -> None:
        self.state = state
        self.greet_enabled = greet
        self.eyes_enabled = eyes
        self.water_enabled = water
        self.meal_enabled = meal
        self.next_eye_at = now + EYE_SECONDS
        self.next_water_at = now + WATER_SECONDS
        self._away = False
        self._away_for = 0.0
        self._allowed_at = 0.0
        self._roll_day(now)
        band = self._band(now)
        if band is not None and band[0] not in state.greeted:
            state.greeted.append(band[0])

    def tick(
        self, now: float, *, idle_seconds: float = 0.0, quiet: bool = False
    ) -> CareAlert | None:
        self._roll_day(now)
        if idle_seconds >= AWAY_SECONDS:
            self._away = True
            self._away_for = max(self._away_for, idle_seconds)
            return None
        if self._away:
            away_for = self._away_for
            self._away = False
            self._away_for = 0.0
            self.next_eye_at = self._resumed(
                self.next_eye_at, now, away_for, EYE_SECONDS
            )
            self.next_water_at = self._resumed(
                self.next_water_at, now, away_for, WATER_SECONDS
            )
            return None
        if quiet:
            return None
        if SLEEP_START <= datetime.fromtimestamp(now).hour < SLEEP_END:
            self.next_eye_at = now + EYE_SECONDS
            self.next_water_at = now + WATER_SECONDS
            return None

        meal = self._due_meal(now)
        if meal is not None and self.meal_enabled:
            name, event = meal
            self.state.meals.append(name)
            self.next_eye_at = now + EYE_SECONDS
            self.next_water_at = now + WATER_SECONDS
            band = self._band(now)
            if band is not None and band[0] not in self.state.greeted:
                self.state.greeted.append(band[0])
            return CareAlert("meal", event)

        band = self._band(now)
        if band is not None and self.greet_enabled and band[0] not in self.state.greeted:
            self.state.greeted.append(band[0])
            self._allowed_at = now + ALERT_GAP
            return CareAlert("greet", band[1])

        if now < self._allowed_at:
            return None
        eye_due = self.eyes_enabled and now >= self.next_eye_at
        water_due = self.water_enabled and now >= self.next_water_at
        if eye_due and water_due:
            self.next_eye_at = now + EYE_SECONDS
            self.next_water_at = now + WATER_SECONDS
            return CareAlert("both", "care_both")
        if water_due:
            self.next_water_at = now + WATER_SECONDS
            return CareAlert("water", "care_water")
        if eye_due:
            self.next_eye_at = now + EYE_SECONDS
            return CareAlert("eyes", "care_eyes")
        return None

    def set_greet(self, enabled: bool, now: float) -> None:
        self.greet_enabled = enabled
        if enabled:
            band = self._band(now)
            if band is not None and band[0] not in self.state.greeted:
                self.state.greeted.append(band[0])

    def set_eyes(self, enabled: bool, now: float) -> None:
        self.eyes_enabled = enabled
        if enabled:
            self.next_eye_at = now + EYE_SECONDS

    def set_water(self, enabled: bool, now: float) -> None:
        self.water_enabled = enabled
        if enabled:
            self.next_water_at = now + WATER_SECONDS

    def set_meal(self, enabled: bool) -> None:
        self.meal_enabled = enabled

    @staticmethod
    def _resumed(due: float, now: float, away_for: float, interval: float) -> float:
        """A break does not count toward the interval; a long one starts it over."""
        if away_for >= interval:
            return now + interval
        return due + away_for

    def _roll_day(self, now: float) -> None:
        day = datetime.fromtimestamp(now).strftime("%Y-%m-%d")
        if day != self.state.day:
            self.state.day = day
            self.state.greeted.clear()
            self.state.meals.clear()

    @staticmethod
    def _band(now: float) -> tuple[str, str] | None:
        hour = datetime.fromtimestamp(now).hour
        if hour >= 23:
            return None
        current = None
        for start, name, event in GREETINGS:
            if hour >= start:
                current = (name, event)
        return current

    def _due_meal(self, now: float) -> tuple[str, str] | None:
        moment = datetime.fromtimestamp(now)
        minutes = moment.hour * 60 + moment.minute
        for start, name, event in MEALS:
            window = start * 60
            if window <= minutes < window + MEAL_WINDOW_MINUTES:
                if name not in self.state.meals:
                    return name, event
        return None

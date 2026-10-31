from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass
from datetime import datetime

from .animation import BODY, FACE, FEET, HAND, HEAD, SKIRT

IDLE = "idle"
WANDER = "wander"
DRAG = "drag"
POKE = "poke"
PET = "pet"
ANNOYED = "annoyed"
NAP = "nap"
SLEEP = "sleep"
FALL = "fall"

PART_EVENTS = {
    HEAD: "pet",
    FACE: "face_poke",
    BODY: "click",
    HAND: "high_five",
    SKIRT: "skirt",
    FEET: "feet",
}
PART_MODES = {HEAD: PET, FACE: PET, BODY: POKE, HAND: PET, SKIRT: ANNOYED, FEET: POKE}
PART_EXPRESSIONS = {
    HEAD: "heart",
    FACE: "blush",
    BODY: "neutral",
    HAND: "sparkle",
    SKIRT: "annoyed",
    FEET: "surprised",
}


@dataclass
class BehaviorContext:
    now: float
    time_band: str
    activity: str
    idle_seconds: float
    quiet: bool
    mood: int
    gap: float = 0.0
    pet_x: float = 0.0
    screen_left: float = 0.0
    screen_right: float = 1920.0


@dataclass
class PetState:
    mode: str = IDLE
    frame: str = "idle"
    facing: int = 1
    bob: float = 0.0
    tilt: float = 0.0
    scale: float = 1.0
    zzz: bool = False
    move_speed: float = 0.0
    expression: str = "neutral"
    hop: float = 0.0
    spin: float = 0.0
    squash_x: float = 1.0
    squash_y: float = 1.0


@dataclass
class Action:
    kind: str
    event: str = ""


class Behavior:
    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.mode = IDLE
        self.mode_until = 0.0
        self.annoyed_until = 0.0
        self.blink_until = 0.0
        self.blink_again_at = 0.0
        self.next_blink = 0.0
        self.next_wander = 0.0
        self.wander_until = 0.0
        self.wander_target = 0.0
        self.wander_pause_at = 0.0
        self.wander_pause_until = 0.0
        self.next_micro = 0.0
        self.micro_until = 0.0
        self.micro_kind = ""
        self.poke_times: deque[float] = deque()
        self.last_input = 0.0
        self.last_tick = 0.0
        self.was_away = False
        self.was_away_long = False
        self.stretch_until = 0.0
        self.wobble_until = 0.0
        self.drag_tilt = 0.0
        self.last_activity = "other"
        self.pending: list[Action] = []
        self.expression = "neutral"
        self.expression_until = 0.0
        self.hop_started = 0.0
        self.hop_until = 0.0
        self.hop_height = 0.0
        self.spin_until = 0.0
        self.squash_until = 0.0

    def _ensure_timers(self, now: float) -> None:
        if self.next_blink <= 0:
            self.next_blink = now + self.rng.uniform(2, 5)
            self.next_wander = now + self.rng.uniform(30, 90)
            self.next_micro = now + self.rng.uniform(20, 50)
            self.last_input = now

    def _queue(self, event: str) -> None:
        self.pending.append(Action("speak", event))

    def drain(self) -> list[Action]:
        actions, self.pending = self.pending, []
        return actions

    def force_speak(self, event: str) -> None:
        self._queue(event)

    def interrupt(self) -> None:
        if self.mode == WANDER:
            self.mode = IDLE
            self.wander_pause_at = 0.0
            self.wander_pause_until = 0.0

    def set_drag_tilt(self, tilt: float) -> None:
        self.drag_tilt = max(-10.0, min(10.0, tilt))

    def _set_expression(self, name: str, until: float) -> None:
        self.expression = name
        self.expression_until = until

    def _hop(self, now: float, height: float = 9.0) -> None:
        self.hop_started = now
        self.hop_until = now + 0.42
        self.hop_height = height

    def _spin(self, now: float) -> None:
        self.spin_until = now + 0.55

    def _wake(self, ctx: BehaviorContext, greeting: str = "wake") -> None:
        self.mode = IDLE
        self.mode_until = 0.0
        self.stretch_until = ctx.now + 0.35
        self.next_wander = ctx.now + self.rng.uniform(30, 90)
        self._queue(greeting)

    def on_click(self, now: float, part: str = BODY) -> None:
        if self.mode in (DRAG, FALL):
            return
        self.last_input = now
        if self.mode == ANNOYED and now < self.annoyed_until:
            return
        while self.poke_times and now - self.poke_times[0] > 4.0:
            self.poke_times.popleft()
        self.poke_times.append(now)

        if part == SKIRT:
            self.mode = ANNOYED
            self.annoyed_until = now + 3.5
            self.mode_until = 0.0
            self.poke_times.clear()
            self._set_expression("annoyed", now + 2.2)
            self._queue("skirt")
            return

        if len(self.poke_times) >= 3:
            self.mode = ANNOYED
            self.annoyed_until = now + 8.0
            self.mode_until = 0.0
            self.poke_times.clear()
            self._set_expression("annoyed", now + 2.5)
            self._queue("annoyed")
            return

        self._set_expression(PART_EXPRESSIONS.get(part, "neutral"), now + 1.2)

        if self.mode in (NAP, SLEEP):
            self._wake(
                BehaviorContext(now=now, time_band="", activity="", idle_seconds=0, quiet=False, mood=50),
                "wake",
            )
            return

        self.mode = PART_MODES.get(part, POKE)
        self.mode_until = now + 1.2
        self.next_wander = now + self.rng.uniform(30, 90)
        self.next_micro = now + self.rng.uniform(20, 50)
        if part == FEET:
            self._hop(now, 9.0)
        elif part == HAND:
            self._hop(now, 7.0)
        elif part == HEAD and self.rng.random() < 0.3:
            self._hop(now, 6.0)
        self._queue(PART_EVENTS.get(part, "click"))

    def on_double_click(self, now: float) -> None:
        if self.mode in (DRAG, FALL):
            return
        if self.mode == ANNOYED and now < self.annoyed_until:
            return
        self.last_input = now
        self.poke_times.clear()
        if self.mode in (NAP, SLEEP):
            self._wake(
                BehaviorContext(now=now, time_band="", activity="", idle_seconds=0, quiet=False, mood=50),
                "wake",
            )
            return
        self.mode = POKE
        self.mode_until = now + 1.4
        self.next_wander = now + self.rng.uniform(30, 90)
        self._hop(now, 13.0)
        self._spin(now)
        self._set_expression("sparkle", now + 1.4)
        self._queue("double")

    def on_drag_start(self, now: float) -> None:
        self.last_input = now
        self.poke_times.clear()
        self.mode = DRAG
        self.mode_until = 0.0
        self.drag_tilt = 0.0
        self.hop_until = 0.0
        self._set_expression("surprised", now + 1.4)
        self._queue("drag_start")

    def on_drag_end(self, now: float, speed: float) -> None:
        self.mode = IDLE
        self.mode_until = now + 0.6
        self.last_input = now
        self.drag_tilt = 0.0
        self.next_wander = now + self.rng.uniform(30, 90)
        self.next_micro = now + self.rng.uniform(20, 50)
        if abs(speed) > 1500:
            self.wobble_until = now + 0.7
            self._queue("drag_fast")
        else:
            self._queue("drag_end")

    def start_fall(self, now: float) -> None:
        self.mode = FALL
        self.mode_until = 0.0
        self.last_input = now
        self.poke_times.clear()
        self.hop_until = 0.0
        self.wander_pause_until = 0.0
        self._set_expression("surprised", now + 3.0)

    def bounce(self, now: float) -> None:
        self.squash_until = now + 0.2
        self._set_expression("surprised", now + 0.5)

    def land(self, now: float) -> None:
        self.mode = IDLE
        self.mode_until = 0.0
        self.squash_until = now + 0.32
        self.next_wander = now + self.rng.uniform(30, 90)
        self._set_expression("surprised", now + 0.6)
        if self.rng.random() < 0.35:
            self._queue("land")

    def tick(self, ctx: BehaviorContext) -> PetState:
        now = ctx.now
        self._ensure_timers(now)
        self.last_tick = now
        dx = 0.0
        speed = 0.0
        facing = 1

        if ctx.idle_seconds >= 600:
            self.was_away = True
            if ctx.idle_seconds >= 1800:
                self.was_away_long = True
        elif ctx.idle_seconds < 5 and self.was_away:
            greeting = "greet_long" if self.was_away_long else "greet_return"
            self.was_away = False
            self.was_away_long = False
            if self.mode == NAP:
                self._wake(ctx, greeting)

        hour = datetime.fromtimestamp(now).hour
        if self.mode not in (FALL, DRAG):
            if self.mode in (IDLE, WANDER) and 2 <= hour < 6 and ctx.idle_seconds > 300:
                self.mode = SLEEP
                self.mode_until = 0.0
                speed = 0.0
            if self.mode == SLEEP and (not (2 <= hour < 6) or ctx.idle_seconds < 5):
                if ctx.idle_seconds < 5:
                    greeting = "greet_long" if ctx.gap >= 86400 else "greet_return" if ctx.gap >= 1800 else "wake"
                    self._wake(ctx, greeting)
                else:
                    self.mode = IDLE

            nap_threshold = 300 if ctx.mood < 30 else 600
            if self.mode in (IDLE, WANDER) and ctx.idle_seconds > nap_threshold:
                self.mode = NAP
                self.mode_until = 0.0
                speed = 0.0
            if self.mode == NAP and ctx.idle_seconds < 5:
                self._wake(ctx, "wake")

        if self.mode == ANNOYED and now >= self.annoyed_until:
            self.mode = IDLE
            self.next_wander = now + self.rng.uniform(30, 90)

        if self.mode in (PET, POKE) and now >= self.mode_until:
            self.mode = IDLE

        if self.mode == WANDER:
            if ctx.quiet or ctx.idle_seconds > 600:
                self.mode = IDLE
                speed = 0.0
            elif now < self.wander_pause_until:
                speed = 0.0
            else:
                if self.wander_pause_at and now >= self.wander_pause_at:
                    self.wander_pause_until = now + 0.8
                    self.wander_pause_at = 0.0
                dx = self.wander_target - ctx.pet_x
                if abs(dx) < 4 or now >= self.wander_until:
                    self.mode = IDLE
                    speed = 0.0
                    self.next_wander = now + self.rng.uniform(30, 90)
                    if self.rng.random() < 0.15:
                        self._queue("wander_end")
                else:
                    facing = 1 if dx > 0 else -1
                    speed = 60.0 * facing

        if self.mode == IDLE and not ctx.quiet and now >= self.next_wander and ctx.idle_seconds < 300:
            low = max(ctx.screen_left + 20.0, ctx.screen_left)
            high = max(low + 40.0, ctx.screen_right - 20.0)
            self.wander_target = self.rng.uniform(low, high)
            self.wander_until = now + self.rng.uniform(3, 8)
            self.next_wander = now + self.rng.uniform(30, 90)
            self.wander_pause_until = 0.0
            self.wander_pause_at = now + self.rng.uniform(1, 3) if self.rng.random() < 0.3 else 0.0
            self.mode = WANDER
            dx = self.wander_target - ctx.pet_x
            facing = 1 if dx > 0 else -1
            speed = 60.0 * facing

        if self.mode == IDLE and not ctx.quiet and now >= self.next_micro and now - self.last_input > 5:
            self.micro_kind = self.rng.choice(("look_left", "look_right", "shift", "hair", "yawn", "stretch"))
            self.micro_until = now + self.rng.uniform(0.6, 1.1)
            self.next_micro = now + self.rng.uniform(20, 50)
        if now >= self.micro_until:
            self.micro_kind = ""

        if self.mode not in (SLEEP, NAP):
            if now >= self.next_blink:
                self.blink_until = now + 0.12
                self.next_blink = now + self.rng.uniform(3, 7)
                if self.rng.random() < 0.2:
                    self.blink_again_at = now + 0.3
            if self.blink_again_at and now >= self.blink_again_at:
                self.blink_until = now + 0.12
                self.blink_again_at = 0.0
        else:
            self.blink_until = 0.0

        if self.mode in (PET, POKE):
            frame = "happy"
        elif self.mode in (SLEEP, NAP) or now < self.blink_until:
            frame = "blink"
        else:
            frame = "idle"

        if self.mode in (DRAG, FALL):
            bob = 0.0
        elif self.mode in (SLEEP, NAP):
            bob = math.sin(now * math.tau / 6.0) * 1.2
        elif self.mode == WANDER:
            bob = math.sin(now * math.tau * 3.0) * 2.0
        else:
            bob = math.sin(now * math.tau / 3.6) * 2.5

        tilt = 0.0
        if self.mode == DRAG:
            tilt = self.drag_tilt
        elif self.mode in (ANNOYED, FALL):
            tilt = 0.0
        elif self.micro_kind == "look_left":
            tilt = -1.5
        elif self.micro_kind == "look_right":
            tilt = 1.5
        elif self.micro_kind == "shift":
            tilt = 0.8
        elif self.micro_kind == "hair":
            tilt = -0.8
        elif self.mode == WANDER:
            tilt = 1.5 * facing + math.sin(now * math.tau * 1.5) * 1.4
        if now < self.wobble_until:
            tilt += math.sin(now * math.tau * 8.0) * 4.0

        scale = 1.03 if now < self.stretch_until else 1.0 + 0.004 * math.sin(now * math.tau / 3.6)
        if self.micro_kind == "yawn":
            scale = 1.0 + 0.012 * math.sin(now * 9.0) ** 2
        elif self.micro_kind == "stretch":
            stretch = max(0.0, min(1.0, (now - (self.micro_until - 1.1)) / 1.1))
            scale = 1.0 + 0.03 * math.sin(stretch * math.pi)

        expression = "neutral"
        if now < self.expression_until:
            expression = self.expression
        if self.mode in (SLEEP, NAP):
            expression = "sleepy"
        elif self.mode == ANNOYED:
            expression = "annoyed"
        elif self.mode == DRAG:
            expression = "surprised"

        hop = 0.0
        if self.hop_started < self.hop_until and now < self.hop_until:
            progress = (now - self.hop_started) / max(0.001, self.hop_until - self.hop_started)
            hop = -self.hop_height * math.sin(math.pi * max(0.0, min(1.0, progress)))

        spin = 0.0
        if now < self.spin_until:
            progress = max(0.0, min(1.0, 1.0 - (self.spin_until - now) / 0.55))
            spin = 360.0 * (progress * progress * (3.0 - 2.0 * progress))

        squash_x = 1.0
        squash_y = 1.0
        if now < self.squash_until:
            progress = max(0.0, 1.0 - (self.squash_until - now) / 0.32)
            ease = (1.0 - progress) ** 2
            squash_y = 1.0 - 0.14 * ease
            squash_x = 1.0 + 0.09 * ease

        if self.mode == ANNOYED:
            facing = -1
        elif self.mode == WANDER:
            pass
        else:
            facing = 1

        if self.last_activity == "meeting" and ctx.activity != "meeting" and not ctx.quiet:
            self._queue("meeting_end")
        self.last_activity = ctx.activity

        return PetState(
            mode=self.mode,
            frame=frame,
            facing=facing,
            bob=bob,
            tilt=tilt,
            scale=scale,
            zzz=self.mode in (SLEEP, NAP),
            move_speed=speed,
            expression=expression,
            hop=hop,
            spin=spin,
            squash_x=squash_x,
            squash_y=squash_y,
        )

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path

from .behavior import PetState

RIG_DIR = Path(__file__).resolve().parent.parent / "assets" / "rig"


@dataclass(frozen=True)
class RigLayer:
    role: str
    file: str
    depth: float
    anchor: tuple[float, float]
    frames: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RigSpec:
    outfit: str
    canvas: int
    feet: tuple[float, float]
    draw_order: tuple[str, ...]
    layers: dict[str, RigLayer]


class RigLibrary:
    def __init__(self, root: Path = RIG_DIR) -> None:
        self.root = Path(root)
        self._specs: dict[str, RigSpec | None] = {}
        self._rigs: dict[str, object | None] = {}

    def spec(self, outfit: str) -> RigSpec | None:
        if outfit not in self._specs:
            self._specs[outfit] = self._load_spec(outfit)
        return self._specs[outfit]

    def _load_spec(self, outfit: str) -> RigSpec | None:
        path = self.root / outfit / "rig.json"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            canvas = int(raw["canvas"])
            feet_raw = raw["feet"]
            feet = (float(feet_raw[0]), float(feet_raw[1]))
            draw_order = tuple(str(role) for role in raw["draw_order"])
            layers: dict[str, RigLayer] = {}
            for role, item in raw["layers"].items():
                frames = {
                    str(key): str(value)
                    for key, value in item.get("frames", {}).items()
                }
                layer = RigLayer(
                    role=str(role),
                    file=str(item["file"]),
                    depth=float(item["depth"]),
                    anchor=(float(item["anchor"][0]), float(item["anchor"][1])),
                    frames=frames,
                )
                for rel in (layer.file, *frames.values()):
                    if not (self.root / outfit / rel).is_file():
                        raise FileNotFoundError(rel)
                layers[layer.role] = layer
            if not draw_order or any(role not in layers for role in draw_order):
                raise ValueError("draw_order references unknown layer")
            return RigSpec(
                outfit=str(raw.get("outfit", outfit)),
                canvas=canvas,
                feet=feet,
                draw_order=draw_order,
                layers=layers,
            )
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            IndexError,
            AttributeError,
        ) as exc:
            logging.warning("rig unavailable for %s: %s", outfit, exc)
            return None


@dataclass
class Spring:
    value: float = 0.0
    velocity: float = 0.0

    def step(
        self,
        dt: float,
        target: float,
        stiffness: float = 70.0,
        damping: float = 12.0,
        limit: float = 3.0,
    ) -> float:
        dt = max(0.0, min(0.05, dt))
        accel = (target - self.value) * stiffness - self.velocity * damping
        self.velocity += accel * dt
        self.value = max(-limit, min(limit, self.value + self.velocity * dt))
        return self.value


@dataclass
class RigMotion:
    head_dx: Spring = field(default_factory=Spring)
    head_dy: Spring = field(default_factory=Spring)
    hair_angle: Spring = field(default_factory=Spring)
    hair_dx: Spring = field(default_factory=Spring)
    body_angle: Spring = field(default_factory=Spring)
    leg: Spring = field(default_factory=Spring)
    arm: Spring = field(default_factory=Spring)
    head_scale: float = 1.0
    breath: float = 0.0

    def update(self, dt: float, state: PetState, now: float) -> None:
        breath = math.sin(now * math.tau / 3.6)
        self.breath = breath
        head_dx_target = 0.0
        head_dy_target = 0.35 * breath
        hair_target = -0.35 * breath
        hair_dx_target = 0.0
        body_target = 0.0
        leg_target = 0.0
        expression = state.expression

        if expression == "heart":
            head_dy_target += 0.8
            hair_target += 0.7
        elif expression == "blush":
            head_dx_target = -0.9
            head_dy_target += 0.25
            hair_target += 0.35
        elif expression == "surprised":
            head_dy_target -= 0.8
            hair_target -= 0.45
        elif expression == "annoyed":
            head_dy_target += 0.2

        if state.mode in ("drag", "fall"):
            leg_target = 4.0
            head_dx_target += max(-1.2, min(1.2, -state.tilt * 0.15))
            hair_target += max(-0.9, min(0.9, state.tilt * 0.12))
        elif state.move_speed:
            lean = max(-0.7, min(0.7, state.move_speed * 0.01))
            hair_dx_target = -lean * 1.2
            body_target = lean

        energy = max(0.0, min(1.0, state.music_energy))
        if energy > 0.0:
            hair_target += math.sin(state.music_phase - 0.6) * 0.6 * energy
            head_dy_target += math.sin(state.music_phase - 0.3) * 0.3 * energy
            body_target += math.sin(state.music_phase) * 0.35 * energy
        if state.squash_y < 0.95:
            hair_target += 0.8

        self.head_dx.step(dt, head_dx_target, limit=2.5)
        self.head_dy.step(dt, head_dy_target, limit=2.0)
        self.hair_angle.step(dt, hair_target, stiffness=55.0, damping=9.0, limit=1.2)
        self.hair_dx.step(dt, hair_dx_target, limit=2.0)
        self.body_angle.step(dt, body_target, stiffness=45.0, damping=10.0, limit=0.8)
        self.leg.step(dt, leg_target, stiffness=60.0, damping=12.0, limit=6.0)
        arm_target = 1.0 if expression == "sparkle" else 0.0
        self.arm.step(dt, arm_target, stiffness=90.0, damping=13.0, limit=1.2)
        scale_target = 0.96 if expression == "heart" else 1.0
        self.head_scale += (scale_target - self.head_scale) * min(1.0, dt * 12.0)

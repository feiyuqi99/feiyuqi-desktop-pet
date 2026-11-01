from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPixmap

from .animation import DISPLAY_SCALE, DRAW_SIZE, FEET_Y, SPRITE_FEET_X, SPRITE_FEET_Y
from .behavior import PetState

RIG_DIR = Path(__file__).resolve().parent.parent / "assets" / "rig"
SLOT = QRectF(-DRAW_SIZE / 2, -FEET_Y, DRAW_SIZE, DRAW_SIZE)


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
    hand: tuple[float, float] = (150.0, 200.0)


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
            hand_raw = raw.get("hand", [150, 200])
            return RigSpec(
                outfit=str(raw.get("outfit", outfit)),
                canvas=canvas,
                feet=feet,
                draw_order=draw_order,
                layers=layers,
                hand=(float(hand_raw[0]), float(hand_raw[1])),
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

    def get(self, outfit: str):
        if outfit in self._rigs:
            return self._rigs[outfit]
        spec = self.spec(outfit)
        rig = None
        if spec is not None:
            try:
                rig = Rig(spec, self.root)
            except (OSError, ValueError) as exc:
                logging.warning("rig failed for %s: %s", outfit, exc)
        self._rigs[outfit] = rig
        return rig


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
        elif expression == "wink":
            head_dx_target = 0.5
            head_dy_target += 0.2
            hair_target += 0.2
        elif expression == "tears":
            head_dy_target += 0.6
            hair_target += 0.5
        elif expression == "pout":
            head_dx_target = -0.4
            head_dy_target += 0.2
        elif expression == "confused":
            head_dx_target = 0.8
            hair_target -= 0.2
        elif expression == "shy":
            head_dx_target = -0.7
            head_dy_target += 0.7
            hair_target += 0.4
        elif expression == "dizzy":
            head_dx_target = math.sin(now * 5.0) * 0.9
            hair_target += 0.2
        elif expression == "sweat":
            head_dy_target += 0.2
            hair_target -= 0.2
        elif expression == "expect":
            head_dy_target -= 0.3
            hair_target += 0.2

        action = state.action
        if action == "stretch":
            head_dy_target -= 0.6
            hair_target += 0.6
        elif action == "look":
            head_dx_target = math.sin(now * 1.7) * 2.0
            hair_target += math.sin(now * 1.7 - 0.5) * 0.5
        elif action == "wave":
            head_dx_target = 0.3
            hair_target += 0.3
        elif action == "yawn":
            head_dy_target += 0.5
            hair_target += 0.3
        elif action in ("drink", "eat", "read"):
            head_dy_target += 0.4
            hair_target += 0.2
        elif action == "umbrella":
            head_dy_target -= 0.3
            hair_target += 0.2

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
            beat = math.sin(state.music_phase)
            body_target += beat * 1.1 * energy
            head_dx_target += -beat * 1.0 * energy
            head_dy_target += math.sin(state.music_phase - 0.3) * 0.45 * energy
            hair_target += math.sin(state.music_phase - 0.6) * 1.1 * energy
            hair_dx_target += math.sin(state.music_phase - 0.9) * 1.0 * energy
        if state.squash_y < 0.95:
            hair_target += 0.8

        self.head_dx.step(dt, head_dx_target, limit=3.0)
        self.head_dy.step(dt, head_dy_target, limit=2.0)
        self.hair_angle.step(dt, hair_target, stiffness=55.0, damping=9.0, limit=1.6)
        self.hair_dx.step(dt, hair_dx_target, limit=2.5)
        self.body_angle.step(dt, body_target, stiffness=45.0, damping=10.0, limit=1.6)
        self.leg.step(dt, leg_target, stiffness=60.0, damping=12.0, limit=6.0)
        arm_target = (
            1.0
            if (
                expression == "sparkle"
                and state.mode in ("pet", "poke")
            )
            or state.action in ("stretch", "wave", "umbrella")
            else 0.0
        )
        self.arm.step(dt, arm_target, stiffness=90.0, damping=13.0, limit=1.2)
        scale_target = (
            0.96 if expression == "heart" else 0.98 if expression == "shy" else 1.0
        )
        self.head_scale += (scale_target - self.head_scale) * min(1.0, dt * 12.0)


class Rig:
    def __init__(self, spec: RigSpec, root: Path) -> None:
        self.spec = spec
        self.hand = spec.hand
        self.motion = RigMotion()
        self.base_rotation = 0.0
        self._pixmaps: dict[str, QPixmap] = {}
        folder = Path(root) / spec.outfit
        for layer in spec.layers.values():
            for rel in (layer.file, *layer.frames.values()):
                if rel in self._pixmaps:
                    continue
                pixmap = QPixmap(str(folder / rel))
                if pixmap.isNull():
                    raise FileNotFoundError(rel)
                self._pixmaps[rel] = pixmap.scaled(
                    int(round(DRAW_SIZE)),
                    int(round(DRAW_SIZE)),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )

    def _anchor(self, layer: RigLayer) -> tuple[float, float]:
        return (
            -DRAW_SIZE / 2 + layer.anchor[0] * DISPLAY_SCALE,
            -FEET_Y + layer.anchor[1] * DISPLAY_SCALE,
        )

    def _pixmap(self, layer: RigLayer, frame: str) -> QPixmap:
        return self._pixmaps[layer.frames.get(frame, layer.file)]

    def draw(
        self,
        painter: QPainter,
        state: PetState,
        now: float,
        dt: float,
        overlay,
        base_rotation: float = 0.0,
    ) -> None:
        self.base_rotation = base_rotation
        self.motion.update(dt, state, now)
        frame = state.frame if state.frame in ("blink", "happy") else "idle"
        arm = max(0.0, min(1.0, self.motion.arm.value))
        for role in self.spec.draw_order:
            layer = self.spec.layers[role]
            if role == "left_arm" and arm > 0.99:
                continue
            if role == "arm_up" and arm < 0.01:
                continue
            opacity = 1.0
            if role == "left_arm":
                opacity = 1.0 - arm
            elif role == "arm_up":
                opacity = arm
            self._draw_layer(painter, layer, frame, state, opacity, now)
        painter.save()
        painter.scale(DISPLAY_SCALE, DISPLAY_SCALE)
        painter.translate(-SPRITE_FEET_X, -SPRITE_FEET_Y)
        painter.setOpacity(1.0)
        overlay(painter)
        painter.restore()

    def _draw_layer(
        self,
        painter: QPainter,
        layer: RigLayer,
        frame: str,
        state: PetState,
        opacity: float,
        now: float,
    ) -> None:
        if opacity <= 0.01:
            return
        pixmap = self._pixmap(layer, frame)
        ax, ay = self._anchor(layer)
        dx = (layer.depth - 0.8) * state.tilt * 0.35
        dy = 0.0
        angle = 0.0
        scale_x = 1.0
        scale_y = 1.0
        if layer.role == "head":
            dx += self.motion.head_dx.value
            dy += self.motion.head_dy.value
            scale_y *= self.motion.head_scale
        elif layer.role == "side_hair":
            dx += self.motion.hair_dx.value
            dy += self.motion.head_dy.value * 0.3
            angle += self.motion.hair_angle.value
        elif layer.role == "body":
            dy += self.motion.head_dy.value * 0.15
            angle += self.motion.body_angle.value
            scale_y *= 1.0 + 0.006 * self.motion.breath
        elif layer.role == "legs":
            angle += self.motion.leg.value
        elif layer.role == "left_arm":
            angle += self.motion.body_angle.value * 0.5
        elif layer.role == "arm_up":
            dy -= 1.2 * opacity
            angle -= 3.0 * (1.0 - opacity)
            if state.action == "wave":
                angle += math.sin(now * 9.0) * 4.0 * opacity
        painter.save()
        if layer.role == "legs" and self.base_rotation:
            painter.rotate(-self.base_rotation)
        painter.setOpacity(opacity)
        painter.translate(ax + dx, ay + dy)
        painter.rotate(angle)
        painter.scale(scale_x, scale_y)
        painter.translate(-ax, -ay)
        painter.drawPixmap(SLOT, pixmap, pixmap.rect())
        painter.restore()

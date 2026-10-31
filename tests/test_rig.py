from __future__ import annotations

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from PIL import Image, ImageDraw
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from pet.animation import FEET_X, FEET_Y

from pet.behavior import PetState
from pet.rig import RigLibrary, RigMotion, Spring


def write_rig(root: Path) -> RigLibrary:
    folder = root / "casual"
    folder.mkdir(parents=True, exist_ok=True)
    files = [
        "legs.png",
        "body.png",
        "left_arm.png",
        "side_hair.png",
        "head_idle.png",
        "head_blink.png",
        "head_happy.png",
        "arm_up.png",
    ]
    for name in files:
        (folder / name).touch(exist_ok=True)
    spec = {
        "outfit": "casual",
        "canvas": 512,
        "feet": [256, 500],
        "draw_order": ["legs", "body", "left_arm", "side_hair", "head", "arm_up"],
        "layers": {
            "legs": {"file": "legs.png", "depth": 0.55, "anchor": [256, 415]},
            "body": {"file": "body.png", "depth": 0.8, "anchor": [256, 430]},
            "left_arm": {"file": "left_arm.png", "depth": 0.9, "anchor": [185, 275]},
            "side_hair": {"file": "side_hair.png", "depth": 1.15, "anchor": [256, 300]},
            "head": {
                "file": "head_idle.png",
                "depth": 1.0,
                "anchor": [256, 250],
                "frames": {
                    "idle": "head_idle.png",
                    "blink": "head_blink.png",
                    "happy": "head_happy.png",
                },
            },
            "arm_up": {"file": "arm_up.png", "depth": 1.1, "anchor": [185, 275]},
        },
    }
    (folder / "rig.json").write_text(json.dumps(spec), encoding="utf-8")
    return RigLibrary(root)


def test_rig_spec_loads_layers_and_head_variants(tmp_path):
    spec = write_rig(tmp_path).spec("casual")
    assert spec is not None
    assert spec.outfit == "casual"
    assert spec.feet == (256.0, 500.0)
    assert spec.draw_order[0] == "legs"
    assert spec.layers["head"].frames["blink"] == "head_blink.png"
    assert spec.layers["side_hair"].depth == 1.15


def test_rig_spec_missing_returns_none(tmp_path):
    assert RigLibrary(tmp_path).spec("casual") is None


def test_rig_spec_rejects_unknown_draw_role(tmp_path):
    write_rig(tmp_path)
    path = tmp_path / "casual" / "rig.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["draw_order"].append("missing_role")
    path.write_text(json.dumps(raw), encoding="utf-8")
    assert RigLibrary(tmp_path).spec("casual") is None


def advance(motion: RigMotion, state: PetState, seconds: float, start: float = 100.0):
    now = start
    for _ in range(int(seconds * 30)):
        now += 1 / 30
        motion.update(1 / 30, state, now)
    return now


def test_spring_decays_to_target_and_respects_limit():
    spring = Spring()
    for _ in range(120):
        spring.step(1 / 30, 1.0)
    assert 0.9 < spring.value <= 1.05
    hard = Spring()
    hard.step(10.0, 1.0, limit=2.0)
    assert abs(hard.value) <= 2.0


def test_idle_breathing_is_subtle():
    motion = RigMotion()
    advance(motion, PetState(mode="idle", expression="neutral"), 4.0)
    assert abs(motion.head_dy.value) <= 0.7
    assert abs(motion.hair_angle.value) <= 0.6
    assert abs(motion.arm.value) < 0.05


def test_head_pet_presses_head_and_hair():
    motion = RigMotion()
    advance(motion, PetState(mode="pet", expression="heart"), 1.0)
    assert motion.head_dy.value > 0.3
    assert motion.head_scale < 0.99
    assert motion.hair_angle.value > 0.5


def test_face_poke_recoils_then_returns():
    motion = RigMotion()
    advance(motion, PetState(mode="poke", expression="blush"), 0.6)
    assert abs(motion.head_dx.value) > 0.4
    advance(motion, PetState(mode="idle", expression="neutral"), 2.0, start=200.0)
    assert abs(motion.head_dx.value) < 0.15


def test_high_five_raises_arm_and_relaxes():
    motion = RigMotion()
    advance(motion, PetState(mode="pet", expression="sparkle"), 0.7)
    assert motion.arm.value > 0.7
    advance(motion, PetState(mode="idle", expression="neutral"), 2.0, start=200.0)
    assert motion.arm.value < 0.2


def test_music_sparkle_does_not_raise_arm():
    motion = RigMotion()
    advance(motion, PetState(mode="idle", expression="sparkle"), 1.0)
    assert motion.arm.value < 0.1


def test_dragging_makes_legs_dangle():
    motion = RigMotion()
    advance(motion, PetState(mode="drag", tilt=8.0), 0.6)
    assert motion.leg.value > 2.0
    assert abs(motion.hair_angle.value) <= 1.2


def test_music_and_walk_stay_bounded():
    motion = RigMotion()
    state = PetState(
        mode="wander",
        move_speed=60.0,
        music_phase=3.0,
        music_energy=1.0,
    )
    advance(motion, state, 3.0)
    assert abs(motion.hair_angle.value) <= 1.2
    assert abs(motion.hair_dx.value) <= 2.0
    assert abs(motion.body_angle.value) <= 0.8


_APP = QApplication.instance() or QApplication([])


def write_png_rig(root: Path) -> RigLibrary:
    write_rig(root)
    folder = root / "casual"
    colors = {
        "legs.png": (60, 80, 120, 255),
        "body.png": (250, 233, 203, 255),
        "left_arm.png": (240, 210, 180, 255),
        "side_hair.png": (230, 120, 60, 255),
        "head_idle.png": (250, 200, 170, 255),
        "head_blink.png": (240, 190, 160, 255),
        "head_happy.png": (255, 190, 170, 255),
        "arm_up.png": (250, 220, 190, 255),
    }
    for name, color in colors.items():
        image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((180, 200, 330, 460), fill=color)
        image.save(folder / name)
    return RigLibrary(root)


def test_rig_loads_pixmaps_and_draws(tmp_path):
    lib = write_png_rig(tmp_path)
    rig = lib.get("casual")
    assert rig is not None
    image = QImage(248, 216, QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    painter.translate(FEET_X, FEET_Y)
    rig.draw(painter, PetState(mode="idle"), 100.0, 1 / 30, lambda p: None)
    painter.end()
    opaque = sum(
        1
        for y in range(216)
        for x in range(248)
        if image.pixelColor(x, y).alpha() > 0
    )
    assert opaque > 1000


def test_rig_get_returns_none_when_assets_missing(tmp_path):
    assert RigLibrary(tmp_path).get("casual") is None

from __future__ import annotations

import json
from pathlib import Path

from pet.rig import RigLibrary


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
    lib = write_rig(tmp_path)
    path = tmp_path / "casual" / "rig.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["draw_order"].append("missing_role")
    path.write_text(json.dumps(raw), encoding="utf-8")
    assert RigLibrary(tmp_path).spec("casual") is None

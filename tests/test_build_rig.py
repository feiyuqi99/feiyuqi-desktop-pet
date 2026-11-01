from __future__ import annotations

import numpy as np

from tools.build_rig import (
    best_shift,
    color_masks,
    composite,
    diff_metrics,
    fill_region,
    fill_holes,
    hand_anchor,
    inpaint_neighbors,
    polygon_mask,
)


def test_hand_anchor_picks_top_cluster():
    mask = np.zeros((512, 512), dtype=bool)
    mask[200:300, 100:140] = True
    mask[196:206, 104:124] = True
    x, y = hand_anchor(mask)
    assert 100 <= x <= 140
    assert 196 <= y <= 215


def test_existing_rigs_have_hand_anchor():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "assets" / "rig"
    for outfit in ("casual", "maid"):
        raw = json.loads((root / outfit / "rig.json").read_text(encoding="utf-8"))
        assert len(raw["hand"]) == 2, outfit
        assert 0 < raw["hand"][0] < 512 and 0 < raw["hand"][1] < 512, outfit


def test_polygon_and_color_masks():
    mask = polygon_mask((16, 16), [(2, 2), (12, 2), (12, 12), (2, 12)])
    assert mask[5, 5]
    assert not mask[0, 0]

    rgba = np.zeros((4, 4, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    rgba[0, 0, :3] = (240, 140, 60)
    rgba[1, 1, :3] = (40, 30, 20)
    rgba[2, 2, :3] = (250, 232, 201)
    masks = color_masks(rgba)
    assert masks["hair"][0, 0]
    assert masks["dark"][1, 1]
    assert masks["cream"][2, 2]


def test_fill_region_only_touches_mask():
    rgba = np.zeros((4, 4, 4), dtype=np.uint8)
    mask = np.zeros((4, 4), dtype=bool)
    mask[1:3, 1:3] = True
    out = fill_region(rgba, mask, (1, 2, 3, 255))
    assert tuple(out[1, 1]) == (1, 2, 3, 255)
    assert out[0, 0, 3] == 0


def test_inpaint_neighbors_grows_surrounding_colors():
    rgba = np.zeros((6, 12, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    rgba[:, :6, :3] = (40, 35, 30)
    rgba[:, 6:, :3] = (250, 235, 215)
    hole = np.zeros((6, 12), dtype=bool)
    hole[2:4, 3] = True
    hole[2:4, 8] = True
    source = (rgba[..., 3] > 0) & ~hole
    out = inpaint_neighbors(rgba, hole, source)
    assert out[2, 3, 0] < 60
    assert out[3, 3, 0] < 60
    assert out[2, 8, 0] > 240
    assert out[3, 8, 0] > 240
    assert out[2, 3, 3] == 255


def test_fill_holes_keeps_exterior_open():
    mask = np.zeros((20, 20), dtype=bool)
    mask[4:16, 4:16] = True
    mask[8:12, 8:12] = False
    filled = fill_holes(mask)
    assert filled[9, 9]
    assert not filled[0, 0]
    assert not filled[19, 19]


def test_best_shift_recovers_translation():
    ref = np.zeros((20, 20), dtype=bool)
    ref[5:10, 6:12] = True
    target = np.zeros_like(ref)
    target[3:8, 7:13] = True
    assert best_shift(ref, target, max_shift=3) == (2, -1)


def test_composite_later_layer_wins_and_diff_metrics():
    red = np.zeros((2, 2, 4), dtype=np.uint8)
    red[..., 0] = 255
    red[..., 3] = 255
    green = np.zeros_like(red)
    green[..., 1] = 255
    green[..., 3] = 255
    out = composite({"red": red, "green": green}, ["red", "green"])
    assert tuple(out[0, 0]) == (0, 255, 0, 255)
    mean, coverage = diff_metrics(out, red)
    assert mean > 0
    assert coverage == 0


def test_casual_rig_assets_exist_and_check_passes():
    from pathlib import Path

    from tools.build_rig import check

    root = Path(__file__).resolve().parent.parent / "assets" / "rig" / "casual"
    for name in (
        "legs.png",
        "body.png",
        "left_arm.png",
        "side_hair.png",
        "head_idle.png",
        "head_blink.png",
        "head_happy.png",
        "arm_up.png",
        "rig.json",
    ):
        assert (root / name).is_file(), name
    assert check("casual") == 0


def test_maid_rig_assets_exist_and_check_passes():
    from pathlib import Path

    from tools.build_rig import check

    root = Path(__file__).resolve().parent.parent / "assets" / "rig" / "maid"
    for name in (
        "legs.png",
        "body.png",
        "left_arm.png",
        "side_hair.png",
        "head_idle.png",
        "head_blink.png",
        "head_happy.png",
        "arm_up.png",
        "rig.json",
    ):
        assert (root / name).is_file(), name
    assert check("maid") == 0


def test_all_outfit_rigs_exist_and_check_passes():
    from pathlib import Path

    from pet.outfits import ALL_OUTFITS
    from tools.build_rig import CONFIGS, check

    root = Path(__file__).resolve().parent.parent / "assets" / "rig"
    names = (
        "legs.png",
        "body.png",
        "left_arm.png",
        "side_hair.png",
        "head_idle.png",
        "head_blink.png",
        "head_happy.png",
        "arm_up.png",
        "rig.json",
    )
    for outfit in ALL_OUTFITS:
        assert outfit.id in CONFIGS, outfit.id
        for name in names:
            assert (root / outfit.id / name).is_file(), (outfit.id, name)
        assert check(outfit.id) == 0, outfit.id

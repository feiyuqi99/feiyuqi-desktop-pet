from __future__ import annotations

import numpy as np

from tools.build_rig import (
    best_shift,
    color_masks,
    composite,
    diff_metrics,
    fill_region,
    polygon_mask,
)


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

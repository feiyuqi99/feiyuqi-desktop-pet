from __future__ import annotations

from pathlib import Path

from pet.outfits import (
    ALL_OUTFITS,
    available_ids,
    available_outfits,
    has_assets,
    label,
)


def test_registry_has_twelve_unique_outfits():
    ids = [outfit.id for outfit in ALL_OUTFITS]
    labels = [outfit.label for outfit in ALL_OUTFITS]
    assert len(ids) == 12
    assert len(set(ids)) == 12
    assert len(set(labels)) == 12
    assert ids[:2] == ["maid", "casual"]
    assert set(ids[2:]) == {
        "jk",
        "pajama",
        "sport",
        "sweater",
        "yukata",
        "qipao",
        "santa",
        "raincoat",
        "trench",
        "witch",
    }
    assert label("jk") == "JK 水手服"
    assert label("unknown") == "unknown"


def test_available_outfits_filters_by_idle_asset(tmp_path):
    for outfit in ("maid", "jk"):
        folder = tmp_path / outfit
        folder.mkdir()
        (folder / "idle.png").write_bytes(b"")
    assert has_assets("maid", tmp_path)
    assert not has_assets("casual", tmp_path)
    assert available_ids(tmp_path) == ("maid", "jk")
    assert [outfit.label for outfit in available_outfits(tmp_path)] == [
        "女仆装",
        "JK 水手服",
    ]


def test_repo_has_assets_for_existing_outfits():
    root = Path(__file__).resolve().parent.parent / "assets" / "sprites"
    assert has_assets("maid", root)
    assert has_assets("casual", root)

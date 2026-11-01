from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SPRITE_DIR = Path(__file__).resolve().parent.parent / "assets" / "sprites"


@dataclass(frozen=True)
class Outfit:
    id: str
    label: str


ALL_OUTFITS: tuple[Outfit, ...] = (
    Outfit("maid", "女仆装"),
    Outfit("casual", "便服"),
    Outfit("jk", "JK 水手服"),
    Outfit("pajama", "居家睡衣"),
    Outfit("sport", "运动服"),
    Outfit("sweater", "宽松毛衣"),
    Outfit("yukata", "浴衣"),
    Outfit("qipao", "旗袍"),
    Outfit("santa", "圣诞装"),
    Outfit("raincoat", "雨衣"),
    Outfit("trench", "风衣围巾"),
    Outfit("witch", "魔女"),
)

_LABELS = {outfit.id: outfit.label for outfit in ALL_OUTFITS}


def label(outfit: str) -> str:
    return _LABELS.get(outfit, outfit)


def has_assets(outfit: str, root: Path = SPRITE_DIR) -> bool:
    return (root / outfit / "idle.png").is_file()


def available_outfits(root: Path = SPRITE_DIR) -> tuple[Outfit, ...]:
    return tuple(outfit for outfit in ALL_OUTFITS if has_assets(outfit.id, root))


def available_ids(root: Path = SPRITE_DIR) -> tuple[str, ...]:
    return tuple(outfit.id for outfit in available_outfits(root))

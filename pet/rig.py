from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

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

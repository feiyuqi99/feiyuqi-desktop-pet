from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = DATA_DIR / "config.json"
MEMORY_PATH = DATA_DIR / "memory.json"
LOG_PATH = DATA_DIR / "pet.log"

OUTFITS = ("maid", "casual")
CHATTINESS = ("quiet", "normal", "chatty")


@dataclass
class Settings:
    sit_reminder: bool = True
    hourly_chime: bool = True
    always_on_top: bool = True
    perception: bool = True
    chattiness: str = "normal"


@dataclass
class Pomodoro:
    phase: str = "idle"
    ends_at: float | None = None


@dataclass
class Config:
    version: int = 1
    x: int | None = None
    y: int | None = None
    home_x: int | None = None
    home_y: int | None = None
    outfit: str = "maid"
    mood: int = 70
    mood_updated_at: float = field(default_factory=time.time)
    quiet_until: float = 0.0
    settings: Settings = field(default_factory=Settings)
    pomodoro: Pomodoro = field(default_factory=Pomodoro)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        last_error: OSError | None = None
        for attempt in range(4):
            try:
                os.replace(temp, path)
                return
            except PermissionError as error:
                last_error = error
                time.sleep(0.08 * (attempt + 1))
        raise last_error  # type: ignore[misc]
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def backup_corrupt(path: Path) -> None:
    if not path.exists():
        return
    target = path.with_name(path.stem + ".bad" + path.suffix)
    try:
        os.replace(path, target)
    except OSError:
        pass


def _clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


def _load_settings(raw: Any) -> Settings:
    settings = Settings()
    if isinstance(raw, dict):
        for key in Settings.__dataclass_fields__:
            if key in raw:
                setattr(settings, key, raw[key])
    if settings.chattiness not in CHATTINESS:
        settings.chattiness = "normal"
    for key in ("sit_reminder", "hourly_chime", "always_on_top", "perception"):
        setattr(settings, key, bool(getattr(settings, key)))
    return settings


def _load_pomodoro(raw: Any) -> Pomodoro:
    pomodoro = Pomodoro()
    if isinstance(raw, dict):
        phase = raw.get("phase", "idle")
        if phase in ("idle", "focus", "break"):
            pomodoro.phase = phase
        ends_at = raw.get("ends_at")
        pomodoro.ends_at = float(ends_at) if isinstance(ends_at, (int, float)) else None
    if pomodoro.phase == "idle":
        pomodoro.ends_at = None
    return pomodoro


def load_config(path: Path = CONFIG_PATH) -> Config:
    config = Config()
    if not path.exists():
        return config
    try:
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raise ValueError("config root is not an object")
    except (OSError, ValueError, json.JSONDecodeError):
        backup_corrupt(path)
        return config

    if isinstance(raw.get("x"), int):
        config.x = raw["x"]
    if isinstance(raw.get("y"), int):
        config.y = raw["y"]
    if isinstance(raw.get("home_x"), int):
        config.home_x = raw["home_x"]
    if isinstance(raw.get("home_y"), int):
        config.home_y = raw["home_y"]
    if raw.get("outfit") in OUTFITS:
        config.outfit = raw["outfit"]
    if isinstance(raw.get("mood"), (int, float)):
        config.mood = _clamp(int(raw["mood"]))
    if isinstance(raw.get("mood_updated_at"), (int, float)):
        config.mood_updated_at = float(raw["mood_updated_at"])
    if isinstance(raw.get("quiet_until"), (int, float)):
        config.quiet_until = float(raw["quiet_until"])
    config.settings = _load_settings(raw.get("settings"))
    config.pomodoro = _load_pomodoro(raw.get("pomodoro"))
    return config


def save_config(config: Config, path: Path = CONFIG_PATH) -> None:
    atomic_write_json(path, asdict(config))

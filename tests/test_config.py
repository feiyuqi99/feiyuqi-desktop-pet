from __future__ import annotations

from pet.care import CareState
from pet.config import Config, Pomodoro, Settings, load_config, save_config


def test_defaults_when_missing(tmp_path):
    config = load_config(tmp_path / "config.json")
    assert config.outfit == "maid"
    assert config.mood == 70
    assert config.settings.chattiness == "normal"
    assert config.settings.care_greet is True
    assert config.settings.care_eyes is True
    assert config.settings.care_water is True
    assert config.settings.care_meal is True
    assert config.care == CareState()


def test_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    config = Config(
        x=100,
        y=200,
        home_x=300,
        home_y=400,
        outfit="casual",
        mood=42,
        settings=Settings(
            chattiness="chatty",
            perception=False,
            throwable=False,
            music=False,
            care_greet=False,
            care_eyes=False,
        ),
        pomodoro=Pomodoro(phase="focus", ends_at=12345.0),
        care=CareState(
            day="2026-10-31",
            greeted=["morning", "noon"],
            meals=["breakfast"],
        ),
    )
    save_config(config, path)
    loaded = load_config(path)
    assert loaded.x == 100
    assert loaded.y == 200
    assert loaded.home_x == 300
    assert loaded.home_y == 400
    assert loaded.outfit == "casual"
    assert loaded.mood == 42
    assert loaded.settings.chattiness == "chatty"
    assert loaded.settings.perception is False
    assert loaded.settings.throwable is False
    assert loaded.settings.music is False
    assert loaded.settings.care_greet is False
    assert loaded.settings.care_eyes is False
    assert loaded.settings.care_water is True
    assert loaded.settings.care_meal is True
    assert loaded.pomodoro.phase == "focus"
    assert loaded.pomodoro.ends_at == 12345.0
    assert loaded.care == CareState(
        day="2026-10-31",
        greeted=["morning", "noon"],
        meals=["breakfast"],
    )


def test_bad_care_state_falls_back(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        '{"settings": {"care_greet": false, "care_water": true},'
        ' "care": {"day": 5, "greeted": "morning", "meals": ["lunch", 3]}}',
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.settings.care_greet is False
    assert config.settings.care_eyes is True
    assert config.settings.care_water is True
    assert config.care.day == ""
    assert config.care.greeted == []
    assert config.care.meals == ["lunch"]


def test_corrupt_config_falls_back(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("not json at all", encoding="utf-8")
    config = load_config(path)
    assert config.outfit == "maid"
    assert (tmp_path / "config.bad.json").exists()


def test_invalid_values_are_clamped(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        '{"outfit": "banana", "mood": 999, "settings": {"chattiness": "loud"}, "pomodoro": {"phase": "focus"}}',
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.outfit == "maid"
    assert config.mood == 100
    assert config.settings.chattiness == "normal"
    assert config.pomodoro.ends_at is None

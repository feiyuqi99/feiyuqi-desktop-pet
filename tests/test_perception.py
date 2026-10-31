from __future__ import annotations

from datetime import datetime

from pet.perception import category_for, time_band


def ts(hour: int, minute: int = 0) -> float:
    return datetime(2026, 1, 5, hour, minute).timestamp()


def test_time_bands():
    assert time_band(ts(6, 0)) == "morning"
    assert time_band(ts(11, 29)) == "morning"
    assert time_band(ts(11, 30)) == "noon"
    assert time_band(ts(13, 29)) == "noon"
    assert time_band(ts(13, 30)) == "afternoon"
    assert time_band(ts(18, 0)) == "evening"
    assert time_band(ts(23, 0)) == "late"
    assert time_band(ts(2, 0)) == "night"


def test_category_mapping():
    assert category_for(r"C:\Program Files\Microsoft VS Code\Code.exe") == "coding"
    assert category_for(r"C:\...\Qoder.exe") == "coding"
    assert category_for(r"C:\...\Teams.exe") == "meeting"
    assert category_for(r"C:\...\chrome.exe") == "browser"
    assert category_for(r"C:\...\vlc.exe") == "video"
    assert category_for(r"C:\...\unknown.exe") == "other"
    assert category_for("") == "other"

from __future__ import annotations

from datetime import datetime, timedelta

from pet.memory import Memory, load_memory, save_memory


def test_touch_session_gap_and_days():
    memory = Memory()
    start = datetime(2026, 1, 1, 10, 0).timestamp()
    assert memory.is_new
    gap = memory.touch_session(start)
    assert gap == 0
    assert memory.first_seen == start
    assert memory.days_known == 1
    gap = memory.touch_session(start + 3600)
    assert gap == 3600
    assert memory.last_seen == start + 3600


def test_affection_clamp_and_relationship():
    memory = Memory()
    memory.bump_affection(20)
    assert memory.affection == 20
    assert memory.relationship == "familiar"
    memory.days_seen = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"]
    memory.bump_affection(100)
    assert memory.affection == 100
    assert memory.relationship == "close"


def test_note_line_trims():
    memory = Memory()
    for index in range(20):
        memory.note_line("click", f"line-{index}")
    assert len(memory.last_lines["click"]) == 12
    assert memory.last_lines["click"][-1] == "line-19"


def test_events_cap_and_streak():
    memory = Memory()
    start = datetime(2026, 1, 1, 23, 30).timestamp()
    for index in range(25):
        memory.record_event("late_night", start + index)
    assert len(memory.events) == 20
    memory.late_night_days = ["2026-01-04", "2026-01-05", "2026-01-06"]
    assert memory.late_night_streak(datetime(2026, 1, 7, 1, 0).timestamp()) == 3
    assert memory.late_night_streak(datetime(2026, 1, 8, 1, 0).timestamp()) == 0


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "memory.json"
    memory = Memory(pet_name="小橘", user_name="阿远", affection=42)
    memory.touch_session(1_700_000_000)
    save_memory(memory, path)
    loaded = load_memory(path)
    assert loaded.pet_name == "小橘"
    assert loaded.user_name == "阿远"
    assert loaded.affection == 42
    assert loaded.first_seen == 1_700_000_000


def test_corrupt_memory_falls_back(tmp_path):
    path = tmp_path / "memory.json"
    path.write_text("{not json", encoding="utf-8")
    memory = load_memory(path)
    assert memory.pet_name == "小橘"
    assert (tmp_path / "memory.bad.json").exists()

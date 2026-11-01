from __future__ import annotations

from collections import Counter, defaultdict

from pet.lines import FOLLOWUPS, L, LINES, Line, lines_for

MAX_LENGTH = 34
VALID_TAGS = {
    "morning",
    "noon",
    "afternoon",
    "evening",
    "late",
    "night",
    "coding",
    "meeting",
    "browser",
    "game",
    "video",
    "other",
    "new",
    "familiar",
    "close",
    "low",
    "normal",
    "happy",
    "weekend",
    "late_hours",
    "return",
    "long_absence",
}
REQUIRED_EVENTS = {
    "idle",
    "click",
    "pet",
    "affection",
    "greet",
    "face_poke",
    "coding",
    "talk",
    "high_five",
    "skirt",
    "feet",
    "hourly",
    "music",
    "greet_return",
    "double",
    "wake",
    "sit",
    "late_night",
    "greet_long",
    "drag_start",
    "drag_end",
    "wander_end",
    "annoyed",
    "land",
    "drag_fast",
    "drag_hold",
    "pomo_start",
    "pomo_break",
    "pomo_end",
    "outfit_casual",
    "late_streak",
    "meeting_end",
    "exit",
    "quiet",
    "greet_first",
    "pomo_break_end",
    "outfit_maid",
    "unknown",
    "care_eyes",
    "care_water",
    "music_start",
    "music_end",
    "pomo_stop",
    "anniversary_7",
    "anniversary_30",
    "anniversary_100",
    "name_ask",
    "rename",
    "perception_on",
    "chattiness_quiet",
    "chattiness_chatty",
    "memory_cleared",
    "care_morning",
    "care_afternoon",
    "care_evening",
    "care_breakfast",
    "care_lunch",
    "care_dinner",
    "care_both",
    "pomo_missed",
    "perception_off",
    "chattiness_normal",
    "care_noon",
    "action_stretch",
    "action_look",
    "action_wave",
    "action_yawn",
    "action_drink",
    "action_eat",
    "action_umbrella",
    "action_read",
    "outfit_change",
}


def test_library_reaches_about_a_thousand_new_lines():
    assert len(LINES) >= 1400


def test_every_event_is_covered_and_not_thin():
    counts = Counter(line.event for line in LINES)
    missing = REQUIRED_EVENTS - set(counts)
    assert not missing, missing
    thin = {event: count for event, count in counts.items() if count < 6}
    assert not thin, thin


def test_no_duplicate_text_within_an_event():
    by_event = defaultdict(set)
    duplicates = []
    for line in LINES:
        if line.text in by_event[line.event]:
            duplicates.append((line.event, line.text))
        by_event[line.event].add(line.text)
    assert not duplicates, duplicates


def test_texts_are_short_and_clean():
    for line in LINES:
        assert isinstance(line, Line)
        assert line.event
        assert line.text == line.text.strip(), line.text
        assert 0 < len(line.text) <= MAX_LENGTH, line.text


def test_tags_are_known_context_flags():
    unknown = {tag for line in LINES for tag in line.tags} - VALID_TAGS
    assert not unknown, unknown


def test_followups_and_helpers_still_work():
    assert len(FOLLOWUPS) >= 5
    assert lines_for("idle")
    assert L("测试台词", "idle").event == "idle"

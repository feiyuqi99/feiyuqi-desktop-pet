from __future__ import annotations

import math
import random

from pet.audio import MusicDetector

DT = 1 / 30


def feed(detector: MusicDetector, levels, start: float = 100.0):
    state = None
    for index, level in enumerate(levels):
        state = detector.feed(level, start + index * DT)
    return state


def beat_track(duration: float, bpm: float = 120.0, peak: float = 0.4, floor: float = 0.02):
    samples = []
    for index in range(int(duration / DT)):
        moment = index * DT
        phase = (moment * bpm / 60.0) % 1.0
        samples.append(peak if phase < 0.06 else floor)
    return samples


def test_silence_is_not_music():
    detector = MusicDetector()
    state = feed(detector, [0.03] * int(6 / DT))
    assert not state.active
    assert state.tempo == 0.0
    assert state.energy == 0.0


def test_steady_beats_activate_music():
    detector = MusicDetector()
    state = feed(detector, beat_track(8.0, bpm=120))
    assert state.active
    assert 108.0 <= state.tempo <= 132.0
    assert state.energy > 0.1


def test_slow_beats_activate_music():
    detector = MusicDetector()
    state = feed(detector, beat_track(10.0, bpm=70))
    assert state.active
    assert 62.0 <= state.tempo <= 78.0


def test_irregular_noise_is_not_music():
    detector = MusicDetector()
    rng = random.Random(4)
    state = feed(detector, [rng.uniform(0.02, 0.35) for _ in range(int(10 / DT))])
    assert not state.active


def test_music_stops_after_quiet():
    detector = MusicDetector()
    state = feed(detector, beat_track(6.0))
    assert state.active
    state = feed(detector, [0.02] * int(6 / DT), start=200.0)
    assert not state.active
    assert state.tempo == 0.0
    assert state.pulse == 0.0


def test_pulse_follows_beat():
    detector = MusicDetector()
    start = 100.0
    samples = beat_track(5.0)
    state = None
    for index, level in enumerate(samples):
        state = detector.feed(level, start + index * DT)
    assert state is not None
    peaks = []
    for offset in range(0, 30):
        moment = start + len(samples) * DT + offset * DT
        peaks.append(detector.feed(0.4 if offset == 0 else 0.02, moment).pulse)
    assert max(peaks) > 0.5
    assert peaks[-1] < peaks[0]

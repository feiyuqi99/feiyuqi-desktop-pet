from __future__ import annotations

import ctypes
import logging
import math
import threading
import time
from collections import deque
from ctypes import wintypes
from dataclasses import dataclass

log = logging.getLogger(__name__)

_CLSID_MM_DEVICE_ENUMERATOR = "{BCDE0395-E52F-467C-8E3D-C4579291692E}"
_IID_MM_DEVICE_ENUMERATOR = "{A95664D2-9614-4F35-A746-DE8DB63617E6}"
_IID_AUDIO_METER = "{C02216F6-8C67-4B5B-9D00-D008E73E0064}"
_IID_ENDPOINT_VOLUME = "{5CDF2C82-841E-4546-9722-0CF74078229A}"
_COINIT_MULTITHREADED = 0

_ole32 = ctypes.WinDLL("ole32")
HRESULT = ctypes.c_long


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


_ole32.CLSIDFromString.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(_GUID)]
_ole32.CLSIDFromString.restype = HRESULT
_ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
_ole32.CoInitializeEx.restype = HRESULT
_ole32.CoUninitialize.argtypes = []
_ole32.CoCreateInstance.argtypes = [
    ctypes.POINTER(_GUID),
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(_GUID),
    ctypes.POINTER(ctypes.c_void_p),
]
_ole32.CoCreateInstance.restype = HRESULT
_ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]


def _guid(text: str) -> _GUID:
    result = _GUID()
    _ole32.CLSIDFromString(ctypes.c_wchar_p(text), ctypes.byref(result))
    return result


def _vcall(ptr, index, restype, argtypes, *args):
    table = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
    func = ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(table[index])
    return func(ptr, *args)


def _release(ptr) -> None:
    if ptr:
        _vcall(ptr, 2, ctypes.c_ulong, [])


@dataclass(frozen=True)
class MusicState:
    active: bool = False
    level: float = 0.0
    energy: float = 0.0
    pulse: float = 0.0
    tempo: float = 0.0
    updated_at: float = 0.0


class MusicDetector:
    def __init__(self) -> None:
        self._baseline = 0.02
        self._previous = 0.0
        self._envelope = 0.0
        self._energy_env = 0.0
        self._flux_mean = 0.0
        self._flux_var = 0.0
        self._beat_at = -100.0
        self._beats: deque[float] = deque(maxlen=16)
        self._levels: deque[float] = deque(maxlen=120)
        self._loud_since: float | None = None
        self._last_loud = -100.0
        self._active = False
        self._rhythmic = False
        self._periodic_at = -100.0
        self._state = MusicState()

    def _is_periodic(self) -> bool:
        samples = list(self._levels)
        if len(samples) < 60:
            return False
        mean = sum(samples) / len(samples)
        centered = [value - mean for value in samples]
        total = sum(value * value for value in centered)
        if total < 1e-6:
            return False
        best = 0.0
        for lag in range(9, 43):
            if lag >= len(centered) - 10:
                break
            left = centered[:-lag]
            right = centered[lag:]
            numerator = sum(a * b for a, b in zip(left, right))
            left_energy = sum(a * a for a in left)
            right_energy = sum(b * b for b in right)
            if left_energy <= 0 or right_energy <= 0:
                continue
            score = numerator / math.sqrt(left_energy * right_energy)
            if score > best:
                best = score
        return best >= 0.5

    def feed(self, level: float, now: float) -> MusicState:
        level = max(0.0, min(1.0, level))
        if level < self._baseline + 0.06:
            self._baseline += (level - self._baseline) * 0.01
        self._baseline = max(0.004, min(0.12, self._baseline))

        self._envelope += (level - self._envelope) * 0.25
        rate = 0.3 if level > self._energy_env else 0.02
        self._energy_env += (level - self._energy_env) * rate
        self._levels.append(level)
        flux = max(0.0, level - self._previous)
        self._previous = level
        self._flux_mean += (flux - self._flux_mean) * 0.2
        self._flux_var += ((flux - self._flux_mean) ** 2 - self._flux_var) * 0.05

        loud = level > self._baseline + 0.04
        if loud:
            self._last_loud = now
            if self._loud_since is None:
                self._loud_since = now
        elif now - self._last_loud > 1.0:
            self._loud_since = None

        threshold = self._flux_mean + 1.6 * math.sqrt(max(0.0, self._flux_var)) + 0.012
        if loud and flux > threshold and now - self._beat_at >= 0.3:
            self._beat_at = now
            self._beats.append(now)
            while self._beats and now - self._beats[0] > 6.0:
                self._beats.popleft()

        recent = [moment for moment in self._beats if now - moment <= 4.0]
        intervals = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
        intervals = [gap for gap in intervals if 0.3 <= gap <= 1.4]

        if now - self._periodic_at >= 0.2:
            self._periodic_at = now
            self._rhythmic = self._is_periodic()

        if not self._active:
            if (
                self._rhythmic
                and len(recent) >= 3
                and self._loud_since is not None
                and now - self._loud_since >= 1.0
            ):
                self._active = True
        elif now - self._last_loud > 3.5:
            self._active = False
            self._loud_since = None
            self._beats.clear()
            self._beat_at = -100.0
            self._rhythmic = False
            recent = []
            intervals = []

        tempo = 0.0
        if self._active and len(intervals) >= 2:
            mean_gap = sum(intervals) / len(intervals)
            if mean_gap > 0:
                tempo = max(40.0, min(200.0, 60.0 / mean_gap))

        energy = max(0.0, min(1.0, (self._energy_env - self._baseline - 0.03) / 0.45))
        pulse = 0.0
        if self._active:
            since = now - self._beat_at
            if 0.0 <= since < 0.7:
                pulse = math.exp(-since / 0.18)

        self._state = MusicState(
            active=self._active,
            level=self._envelope,
            energy=energy,
            pulse=pulse,
            tempo=tempo,
            updated_at=now,
        )
        return self._state


class _PeakMeter:
    def __init__(self) -> None:
        self._com = False
        self._enumerator = ctypes.c_void_p()
        self._device = ctypes.c_void_p()
        self._meter = ctypes.c_void_p()
        self._volume = ctypes.c_void_p()
        self._volume_at = -100.0
        self._volume_value = 1.0
        self._muted = False
        hr = _ole32.CoInitializeEx(None, _COINIT_MULTITHREADED)
        if hr not in (0, 1):
            raise OSError(f"CoInitializeEx failed: {hr}")
        self._com = True
        try:
            hr = _ole32.CoCreateInstance(
                ctypes.byref(_guid(_CLSID_MM_DEVICE_ENUMERATOR)),
                None,
                1,
                ctypes.byref(_guid(_IID_MM_DEVICE_ENUMERATOR)),
                ctypes.byref(self._enumerator),
            )
            if hr != 0 or not self._enumerator:
                raise OSError(f"device enumerator failed: {hr}")
            hr = _vcall(
                self._enumerator,
                4,
                HRESULT,
                [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)],
                0,
                0,
                ctypes.byref(self._device),
            )
            if hr != 0 or not self._device:
                raise OSError(f"render device failed: {hr}")
            hr = _vcall(
                self._device,
                3,
                HRESULT,
                [_GUID, wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
                _guid(_IID_AUDIO_METER),
                1,
                None,
                ctypes.byref(self._meter),
            )
            if hr != 0 or not self._meter:
                raise OSError(f"audio meter failed: {hr}")
            hr = _vcall(
                self._device,
                3,
                HRESULT,
                [_GUID, wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
                _guid(_IID_ENDPOINT_VOLUME),
                1,
                None,
                ctypes.byref(self._volume),
            )
            if hr != 0:
                self._volume = ctypes.c_void_p()
        except Exception:
            self.close()
            raise

    def _refresh_volume(self) -> None:
        if not self._volume:
            return
        now = time.monotonic()
        if now - self._volume_at < 0.2:
            return
        self._volume_at = now
        level = ctypes.c_float(1.0)
        if (
            _vcall(
                self._volume,
                9,
                HRESULT,
                [ctypes.POINTER(ctypes.c_float)],
                ctypes.byref(level),
            )
            == 0
        ):
            self._volume_value = max(0.0, min(1.0, float(level.value)))
        mute = ctypes.c_int(0)
        if (
            _vcall(
                self._volume,
                15,
                HRESULT,
                [ctypes.POINTER(ctypes.c_int)],
                ctypes.byref(mute),
            )
            == 0
        ):
            self._muted = bool(mute.value)

    def peak(self) -> float:
        value = ctypes.c_float(0.0)
        hr = _vcall(
            self._meter,
            3,
            HRESULT,
            [ctypes.POINTER(ctypes.c_float)],
            ctypes.byref(value),
        )
        if hr != 0:
            return 0.0
        self._refresh_volume()
        if self._muted:
            return 0.0
        return min(1.0, float(value.value) / max(0.12, self._volume_value))

    def device_id(self) -> str:
        text = ctypes.c_wchar_p()
        hr = _vcall(
            self._device,
            5,
            HRESULT,
            [ctypes.POINTER(ctypes.c_wchar_p)],
            ctypes.byref(text),
        )
        if hr != 0 or not text.value:
            return ""
        value = text.value
        _ole32.CoTaskMemFree(ctypes.cast(text, ctypes.c_void_p))
        return value

    def close(self) -> None:
        _release(self._volume)
        self._volume = ctypes.c_void_p()
        _release(self._meter)
        self._meter = ctypes.c_void_p()
        _release(self._device)
        self._device = ctypes.c_void_p()
        _release(self._enumerator)
        self._enumerator = ctypes.c_void_p()
        if self._com:
            _ole32.CoUninitialize()
            self._com = False


class AudioMonitor:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = MusicState()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._failed = False

    def start(self) -> None:
        with self._lock:
            if self._failed:
                return
            thread = self._thread
            if thread is not None and thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="pet-audio", daemon=True)
            thread = self._thread
        thread.start()

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=0.4)
        with self._lock:
            self._thread = None
            self._state = MusicState()

    def snapshot(self) -> MusicState:
        with self._lock:
            return self._state

    def _run(self) -> None:
        try:
            meter = _PeakMeter()
        except Exception:
            log.warning("audio meter unavailable; music reactions disabled", exc_info=True)
            with self._lock:
                self._failed = True
            return
        detector = MusicDetector()
        interval = 1 / 30
        next_at = time.monotonic()
        meter_at = time.monotonic()
        device = meter.device_id()
        log.info("audio device: %s", device)
        try:
            while not self._stop.is_set():
                if time.monotonic() - meter_at >= 10.0:
                    meter_at = time.monotonic()
                    try:
                        fresh = _PeakMeter()
                    except Exception:
                        log.warning("audio meter refresh failed", exc_info=True)
                    else:
                        meter.close()
                        meter = fresh
                        current = meter.device_id()
                        if current != device:
                            device = current
                            log.info("audio device switched: %s", device)
                try:
                    level = meter.peak()
                except Exception:
                    level = 0.0
                state = detector.feed(level, time.time())
                with self._lock:
                    self._state = state
                next_at += interval
                delay = next_at - time.monotonic()
                if delay > 0:
                    self._stop.wait(delay)
                else:
                    next_at = time.monotonic()
        finally:
            meter.close()

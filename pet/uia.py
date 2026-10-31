from __future__ import annotations

import ctypes
import logging
import os
import threading
from ctypes import wintypes

from . import support

log = logging.getLogger(__name__)

InputRect = tuple[int, int, int, int, int]

_CLSID_UIAUTOMATION = "{FF48DBA4-60EF-4201-AA87-54103EEF594E}"
_IID_UIAUTOMATION = "{30CBE57D-D9D0-452A-AB13-7AC5AC4825EE}"
_UIA_CONTROL_TYPE = 30003
_UIA_EDIT = 50004
_UIA_BOUNDING_RECT = 30001
_UIA_IS_OFFSCREEN = 30022
_TREE_DESCENDANTS = 4
_COINIT_MULTITHREADED = 0
_VT_I4 = 3
_VT_BOOL = 11
_VT_ARRAY_R8 = 0x2005

_ole32 = ctypes.WinDLL("ole32")
_oleaut32 = ctypes.WinDLL("oleaut32")
_user32 = ctypes.WinDLL("user32", use_last_error=True)
HRESULT = ctypes.c_long


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class _VARIANT(ctypes.Structure):
    _fields_ = [
        ("vt", ctypes.c_ushort),
        ("r1", ctypes.c_ushort),
        ("r2", ctypes.c_ushort),
        ("r3", ctypes.c_ushort),
        ("data", ctypes.c_byte * 16),
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
_oleaut32.VariantClear.argtypes = [ctypes.POINTER(_VARIANT)]
_oleaut32.VariantClear.restype = HRESULT
_oleaut32.SafeArrayGetUBound.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint,
    ctypes.POINTER(ctypes.c_long),
]
_oleaut32.SafeArrayAccessData.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
_oleaut32.SafeArrayUnaccessData.argtypes = [ctypes.c_void_p]
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD
_user32.GetSystemMetrics.argtypes = [ctypes.c_int]
_user32.GetSystemMetrics.restype = ctypes.c_int


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


def _variant_i4(value: int) -> _VARIANT:
    variant = _VARIANT()
    variant.vt = _VT_I4
    ctypes.cast(ctypes.byref(variant, 8), ctypes.POINTER(ctypes.c_int))[0] = value
    return variant


def _property(element, prop: int) -> _VARIANT:
    variant = _VARIANT()
    _vcall(
        element,
        10,
        HRESULT,
        [ctypes.c_int, ctypes.POINTER(_VARIANT)],
        prop,
        ctypes.byref(variant),
    )
    return variant


def _element_rect(element) -> tuple[float, float, float, float] | None:
    variant = _property(element, _UIA_BOUNDING_RECT)
    if variant.vt != _VT_ARRAY_R8:
        _oleaut32.VariantClear(ctypes.byref(variant))
        return None
    array = ctypes.cast(ctypes.byref(variant, 8), ctypes.POINTER(ctypes.c_void_p))[0]
    try:
        count = ctypes.c_long()
        if _oleaut32.SafeArrayGetUBound(array, 1, ctypes.byref(count)) != 0:
            return None
        if count.value < 3:
            return None
        data_ptr = ctypes.c_void_p()
        if _oleaut32.SafeArrayAccessData(array, ctypes.byref(data_ptr)) != 0:
            return None
        try:
            data = ctypes.cast(data_ptr, ctypes.POINTER(ctypes.c_double))
            return data[0], data[1], data[2], data[3]
        finally:
            _oleaut32.SafeArrayUnaccessData(array)
    finally:
        _oleaut32.VariantClear(ctypes.byref(variant))


def _element_offscreen(element) -> bool:
    variant = _property(element, _UIA_IS_OFFSCREEN)
    try:
        if variant.vt != _VT_BOOL:
            return False
        return bool(ctypes.cast(ctypes.byref(variant, 8), ctypes.POINTER(ctypes.c_short))[0])
    finally:
        _oleaut32.VariantClear(ctypes.byref(variant))


def _window_pid(hwnd: int) -> int:
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


class _UiaClient:
    def __init__(self) -> None:
        self._com = False
        self._ui = ctypes.c_void_p()
        self._edits = ctypes.c_void_p()
        hr = _ole32.CoInitializeEx(None, _COINIT_MULTITHREADED)
        if hr not in (0, 1):
            raise OSError(f"CoInitializeEx failed: {hr}")
        self._com = True
        hr = _ole32.CoCreateInstance(
            ctypes.byref(_guid(_CLSID_UIAUTOMATION)),
            None,
            1,
            ctypes.byref(_guid(_IID_UIAUTOMATION)),
            ctypes.byref(self._ui),
        )
        if hr != 0 or not self._ui:
            self.close()
            raise OSError(f"CoCreateInstance failed: {hr}")
        condition = ctypes.c_void_p()
        hr = _vcall(
            self._ui,
            23,
            HRESULT,
            [ctypes.c_int, _VARIANT, ctypes.POINTER(ctypes.c_void_p)],
            _UIA_CONTROL_TYPE,
            _variant_i4(_UIA_EDIT),
            ctypes.byref(condition),
        )
        if hr != 0 or not condition:
            self.close()
            raise OSError(f"edit condition failed: {hr}")
        self._edits = condition

    def close(self) -> None:
        _release(self._edits)
        self._edits = ctypes.c_void_p()
        _release(self._ui)
        self._ui = ctypes.c_void_p()
        if self._com:
            _ole32.CoUninitialize()
            self._com = False

    def scan(
        self, excludes: frozenset[int], hosts: frozenset[int] | None = None
    ) -> list[InputRect]:
        vx = _user32.GetSystemMetrics(76)
        vy = _user32.GetSystemMetrics(77)
        vw = _user32.GetSystemMetrics(78)
        vh = _user32.GetSystemMetrics(79)
        if vw <= 0 or vh <= 0:
            vx, vy = 0, 0
            vw, vh = _user32.GetSystemMetrics(0), _user32.GetSystemMetrics(1)
        own_pid = os.getpid()
        seen: set[tuple[int, int, int, int]] = set()
        found: list[InputRect] = []
        for hwnd, raw in support._windows(excludes):
            if hosts is not None and hwnd not in hosts:
                continue
            if _window_pid(hwnd) == own_pid or support._cloaked(hwnd):
                continue
            left, top, right, bottom = raw
            if right <= vx or left >= vx + vw or bottom <= vy or top >= vy + vh:
                continue
            if right - left < 160 or bottom - top < 60:
                continue
            for rect in self._edits_of(hwnd, vx, vy, vw, vh):
                if rect in seen:
                    continue
                seen.add(rect)
                found.append((*rect, hwnd))
                if len(found) >= 64:
                    return found
        return found

    def _edits_of(
        self, hwnd: int, vx: int, vy: int, vw: int, vh: int
    ) -> list[tuple[int, int, int, int]]:
        scope = ctypes.c_void_p()
        hr = _vcall(
            self._ui,
            6,
            HRESULT,
            [wintypes.HWND, ctypes.POINTER(ctypes.c_void_p)],
            hwnd,
            ctypes.byref(scope),
        )
        if hr != 0 or not scope:
            return []
        try:
            array = ctypes.c_void_p()
            hr = _vcall(
                scope,
                6,
                HRESULT,
                [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
                _TREE_DESCENDANTS,
                self._edits,
                ctypes.byref(array),
            )
            if hr != 0 or not array:
                return []
            try:
                count = ctypes.c_int()
                _vcall(array, 3, HRESULT, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(count))
                rects: list[tuple[int, int, int, int]] = []
                for index in range(min(count.value, 24)):
                    element = ctypes.c_void_p()
                    hr = _vcall(
                        array,
                        4,
                        HRESULT,
                        [ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)],
                        index,
                        ctypes.byref(element),
                    )
                    if hr != 0 or not element:
                        continue
                    try:
                        rects.extend(self._valid_rect(element, vx, vy, vw, vh))
                    finally:
                        _release(element)
                return rects
            finally:
                _release(array)
        finally:
            _release(scope)

    def _valid_rect(
        self, element, vx: int, vy: int, vw: int, vh: int
    ) -> list[tuple[int, int, int, int]]:
        rect = _element_rect(element)
        if rect is None or _element_offscreen(element):
            return []
        left, top, width, height = (int(round(value)) for value in rect)
        if width < 120 or height < 16:
            return []
        right = left + width
        bottom = top + height
        left = max(left, vx)
        right = min(right, vx + vw)
        if left >= right or top < vy or top >= vy + vh:
            return []
        return [(left, top, right, bottom)]


class InputScanner:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rects: list[InputRect] = []
        self._excludes: frozenset[int] = frozenset()
        self._hosts: frozenset[int] | None = None
        self._dirty = False
        self._closed = False
        self._failed = False
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def request(
        self, excludes: frozenset[int] = frozenset(), host: int | None = None
    ) -> None:
        with self._lock:
            if self._closed or self._failed:
                return
            self._excludes = frozenset(excludes)
            self._hosts = None if host is None else frozenset({host})
            self._dirty = True
            thread = self._thread
            start = thread is None or not thread.is_alive()
        if start:
            thread = threading.Thread(target=self._run, name="pet-input-scan", daemon=True)
            with self._lock:
                self._thread = thread
            thread.start()
        self._wake.set()

    def snapshot(self) -> list[InputRect]:
        with self._lock:
            return list(self._rects)

    def close(self) -> None:
        with self._lock:
            self._closed = True
            thread = self._thread
        self._stop.set()
        self._wake.set()
        if thread is not None and thread.is_alive():
            thread.join(timeout=0.3)

    def _run(self) -> None:
        try:
            client = _UiaClient()
        except Exception:
            log.warning("ui automation unavailable; input bars disabled", exc_info=True)
            with self._lock:
                self._failed = True
            return
        try:
            while not self._stop.is_set():
                self._wake.wait(0.5)
                self._wake.clear()
                if self._stop.is_set():
                    break
                with self._lock:
                    if not self._dirty:
                        continue
                    self._dirty = False
                    excludes = self._excludes
                    hosts = self._hosts
                try:
                    rects = client.scan(excludes, hosts)
                except Exception:
                    log.exception("input scan failed")
                    continue
                with self._lock:
                    if self._closed:
                        break
                    if hosts is None:
                        self._rects = rects
                    else:
                        kept = [rect for rect in self._rects if rect[4] not in hosts]
                        self._rects = kept + rects
        finally:
            client.close()

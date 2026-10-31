from __future__ import annotations

import ctypes
from ctypes import wintypes

_user32 = ctypes.WinDLL("user32")
_dwmapi = ctypes.WinDLL("dwmapi")

DWMWA_EXTENDED_FRAME_BOUNDS = 9
DWMWA_CLOAKED = 14
GW_HWNDNEXT = 2

SHELL_CLASSES = {
    "Progman",
    "WorkerW",
    "Shell_TrayWnd",
    "Shell_SecondaryTrayWnd",
    "MultitaskingViewFrame",
    "ForegroundStaging",
    "Windows.UI.Core.CoreWindow",
}


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


_user32.GetTopWindow.argtypes = [wintypes.HWND]
_user32.GetTopWindow.restype = wintypes.HWND
_user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
_user32.GetWindow.restype = wintypes.HWND
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.IsWindowVisible.restype = wintypes.BOOL
_user32.IsIconic.argtypes = [wintypes.HWND]
_user32.IsIconic.restype = wintypes.BOOL
_user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(_RECT)]
_user32.GetWindowRect.restype = wintypes.BOOL
_user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetClassNameW.restype = ctypes.c_int
_dwmapi.DwmGetWindowAttribute.argtypes = [
    wintypes.HWND,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
]
_dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long


def _class_name(hwnd: int) -> str:
    buffer = ctypes.create_unicode_buffer(128)
    _user32.GetClassNameW(hwnd, buffer, 128)
    return buffer.value


def _cloaked(hwnd: int) -> bool:
    value = wintypes.DWORD(0)
    result = _dwmapi.DwmGetWindowAttribute(
        hwnd, DWMWA_CLOAKED, ctypes.byref(value), ctypes.sizeof(value)
    )
    return result == 0 and value.value != 0


def _raw_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    rect = _RECT()
    if not _user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    return rect.left, rect.top, rect.right, rect.bottom


def _visual_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    rect = _RECT()
    result = _dwmapi.DwmGetWindowAttribute(
        hwnd,
        DWMWA_EXTENDED_FRAME_BOUNDS,
        ctypes.byref(rect),
        ctypes.sizeof(rect),
    )
    if result == 0:
        return rect.left, rect.top, rect.right, rect.bottom
    return _raw_rect(hwnd)


def _windows(exclude: frozenset[int]):
    hwnd = _user32.GetTopWindow(None)
    while hwnd:
        if (
            hwnd not in exclude
            and _user32.IsWindowVisible(hwnd)
            and not _user32.IsIconic(hwnd)
            and _class_name(hwnd) not in SHELL_CLASSES
        ):
            rect = _raw_rect(hwnd)
            if rect is not None:
                yield hwnd, rect
        hwnd = _user32.GetWindow(hwnd, GW_HWNDNEXT)


def pick_surface(
    candidates: list[tuple[int, int, int, int]],
    x: int,
    feet_y: float,
    floor: float,
) -> int | None:
    best: int | None = None
    for left, top, right, _bottom in candidates:
        if left <= x < right and feet_y < top <= floor:
            if best is None or top < best:
                best = top
    return best


def surface_below(
    x: int, feet_y: float, floor: float, exclude: frozenset[int] = frozenset()
) -> int | None:
    windows: list[tuple[int, int, int, int]] = []
    for hwnd, raw in _windows(exclude):
        if _cloaked(hwnd):
            continue
        visual = _visual_rect(hwnd)
        windows.append(visual if visual is not None else raw)
    surfaces: list[tuple[int, int, int, int]] = []
    for index, rect in enumerate(windows):
        left, top, right, _bottom = rect
        if not (left <= x < right and feet_y < top <= floor):
            continue
        probe = top + 2
        covered = False
        for above_left, above_top, above_right, above_bottom in windows[:index]:
            if above_left <= x < above_right and above_top <= probe < above_bottom:
                covered = True
                break
        if not covered:
            surfaces.append(rect)
    return pick_surface(surfaces, x, feet_y, floor)


def support_at(
    x: int,
    feet_y: float,
    exclude: frozenset[int] = frozenset(),
    tolerance: int = 4,
) -> int | None:
    for hwnd, raw in _windows(exclude):
        left, top, right, bottom = raw
        if left <= x < right and top <= feet_y + 6 < bottom:
            if _cloaked(hwnd):
                continue
            visual = _visual_rect(hwnd)
            if visual is not None:
                left, top, right, bottom = visual
            if abs(top - feet_y) <= tolerance:
                return top
            return None
    return None

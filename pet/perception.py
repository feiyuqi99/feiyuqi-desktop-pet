from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
from dataclasses import dataclass
from datetime import datetime

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
MONITOR_DEFAULTTONEAREST = 2


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


SHELL_PROCESSES = {
    "explorer.exe",
    "progman.exe",
    "wallpaper32.exe",
    "wallpaper64.exe",
    "searchhost.exe",
    "shellexperiencehost.exe",
    "startmenuexperiencehost.exe",
}

EXACT_CATEGORY = {
    "code.exe": "coding",
    "code - insiders.exe": "coding",
    "qoder.exe": "coding",
    "cursor.exe": "coding",
    "pycharm64.exe": "coding",
    "pycharm.exe": "coding",
    "idea64.exe": "coding",
    "webstorm64.exe": "coding",
    "devenv.exe": "coding",
    "sublime_text.exe": "coding",
    "notepad++.exe": "coding",
    "windowsterminal.exe": "coding",
    "wt.exe": "coding",
    "cmd.exe": "coding",
    "powershell.exe": "coding",
    "pwsh.exe": "coding",
    "bash.exe": "coding",
    "teams.exe": "meeting",
    "ms-teams.exe": "meeting",
    "zoom.exe": "meeting",
    "wemeetapp.exe": "meeting",
    "feishu.exe": "meeting",
    "lark.exe": "meeting",
    "dingtalk.exe": "meeting",
    "chrome.exe": "browser",
    "msedge.exe": "browser",
    "firefox.exe": "browser",
    "brave.exe": "browser",
    "opera.exe": "browser",
    "360se.exe": "browser",
    "qqbrowser.exe": "browser",
    "vlc.exe": "video",
    "mpv.exe": "video",
    "potplayermini64.exe": "video",
    "potplayermini.exe": "video",
}

HINTS = (
    ("coding", ("code", "qoder", "pycharm", "idea", "webstorm", "devenv", "terminal", "powershell", "cmd", "bash")),
    ("meeting", ("teams", "zoom", "wemeet", "feishu", "lark", "dingtalk")),
    ("browser", ("chrome", "edge", "firefox", "brave", "opera", "browser")),
    ("video", ("vlc", "mpv", "potplayer")),
)


def category_for(process: str) -> str:
    name = process.strip().lower().rsplit("\\", 1)[-1]
    if not name:
        return "other"
    if name in EXACT_CATEGORY:
        return EXACT_CATEGORY[name]
    for category, hints in HINTS:
        if any(hint in name for hint in hints):
            return category
    return "other"


def time_band(now: float) -> str:
    moment = datetime.fromtimestamp(now)
    minutes = moment.hour * 60 + moment.minute
    if 6 * 60 <= minutes < 11 * 60 + 30:
        return "morning"
    if 11 * 60 + 30 <= minutes < 13 * 60 + 30:
        return "noon"
    if 13 * 60 + 30 <= minutes < 18 * 60:
        return "afternoon"
    if 18 * 60 <= minutes < 23 * 60:
        return "evening"
    if 23 * 60 <= minutes < 24 * 60:
        return "late"
    return "night"


@dataclass
class PerceptionState:
    activity: str = "other"
    idle_seconds: float = 0.0
    fullscreen: bool = False
    quiet: bool = False


class Perception:
    def __init__(self, enabled: bool = True, poll_interval: float = 2.0) -> None:
        self.enabled = enabled
        self.poll_interval = poll_interval
        self._last_poll = 0.0
        self._state = PerceptionState()
        self._user32 = ctypes.windll.user32
        self._kernel32 = ctypes.windll.kernel32
        self._user32.GetForegroundWindow.restype = wintypes.HWND
        self._user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self._user32.IsWindowVisible.argtypes = [wintypes.HWND]
        self._user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
        self._user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        self._user32.MonitorFromWindow.restype = wintypes.HMONITOR
        self._user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
        self._kernel32.GetTickCount.restype = wintypes.DWORD
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self._last_poll = 0.0

    def idle_seconds(self) -> float:
        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(info)
        if not self._user32.GetLastInputInfo(ctypes.byref(info)):
            return 0.0
        tick = self._kernel32.GetTickCount()
        return ((tick - info.dwTime) & 0xFFFFFFFF) / 1000.0

    def _is_fullscreen(self, hwnd: int) -> bool:
        if not self._user32.IsWindowVisible(hwnd):
            return False
        rect = RECT()
        if not self._user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return False
        monitor = self._user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(info)
        if not self._user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            return False
        screen = info.rcMonitor
        return (
            abs(rect.left - screen.left) <= 2
            and abs(rect.top - screen.top) <= 2
            and abs(rect.right - screen.right) <= 2
            and abs(rect.bottom - screen.bottom) <= 2
        )

    def _foreground(self) -> tuple[str, bool]:
        hwnd = self._user32.GetForegroundWindow()
        if not hwnd:
            return "", False
        pid = wintypes.DWORD()
        self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process = ""
        handle = self._kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if handle:
            try:
                buffer = ctypes.create_unicode_buffer(1024)
                size = wintypes.DWORD(1024)
                if self._kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                    process = buffer.value
            finally:
                self._kernel32.CloseHandle(handle)
        name = process.rsplit("\\", 1)[-1].lower()
        if name in SHELL_PROCESSES:
            return process, False
        return process, self._is_fullscreen(hwnd)

    def poll(self, now: float, manual_quiet: bool = False) -> PerceptionState:
        idle = self.idle_seconds()
        if not self.enabled:
            self._state = PerceptionState(activity="other", idle_seconds=idle, fullscreen=False, quiet=manual_quiet)
            return self._state
        if now - self._last_poll < self.poll_interval:
            self._state.idle_seconds = idle
            self._state.quiet = manual_quiet or self._state.fullscreen or self._state.activity == "meeting"
            return self._state
        self._last_poll = now
        try:
            process, fullscreen = self._foreground()
        except Exception:
            process, fullscreen = "", False
        activity = category_for(process)
        if fullscreen:
            if activity == "other":
                activity = "game"
            elif activity == "browser":
                activity = "video"
        quiet = manual_quiet or fullscreen or activity == "meeting"
        self._state = PerceptionState(
            activity=activity, idle_seconds=idle, fullscreen=fullscreen, quiet=quiet
        )
        return self._state

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import sys

DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_BORDER_COLOR = 34
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMWCP_DONOTROUND = 1
DWMWA_COLOR_NONE = 0xFFFFFFFE
DWMSBT_NONE = 1


def apply_clean_window(hwnd: int) -> None:
    if sys.platform != "win32" or not hwnd:
        return
    try:
        dwmapi = ctypes.windll.dwmapi
    except Exception:
        return

    def set_attr(attribute: int, value: int) -> None:
        data = wintypes.DWORD(value)
        try:
            dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd), wintypes.DWORD(attribute), ctypes.byref(data), ctypes.sizeof(data)
            )
        except Exception:
            pass

    set_attr(DWMWA_BORDER_COLOR, DWMWA_COLOR_NONE)
    set_attr(DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_DONOTROUND)
    set_attr(DWMWA_SYSTEMBACKDROP_TYPE, DWMSBT_NONE)

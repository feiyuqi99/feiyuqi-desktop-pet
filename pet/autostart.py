from __future__ import annotations

import logging
import sys
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "XiaoJuDesktopPet"
MAIN = Path(__file__).resolve().parent.parent / "main.py"


def _pythonw() -> Path:
    executable = Path(sys.executable)
    if executable.name.lower() == "python.exe":
        candidate = executable.with_name("pythonw.exe")
        if candidate.is_file():
            return candidate
    return executable


def command() -> str:
    return f'"{_pythonw()}" "{MAIN}"'


def _read_value() -> str | None:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, VALUE_NAME)
            return str(value)
    except OSError:
        return None


def _write_value(value: str | None) -> bool:
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if value is None:
                try:
                    winreg.DeleteValue(key, VALUE_NAME)
                except FileNotFoundError:
                    pass
            else:
                winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, value)
        return True
    except OSError as exc:
        logging.warning("autostart update failed: %s", exc)
        return False


def is_enabled() -> bool:
    return _read_value() is not None


def set_enabled(enabled: bool) -> bool:
    return _write_value(command() if enabled else None)


def sync(enabled: bool) -> bool:
    current = _read_value()
    if enabled:
        if current == command():
            return True
        return _write_value(command())
    if current is None:
        return True
    return _write_value(None)

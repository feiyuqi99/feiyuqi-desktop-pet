from __future__ import annotations

from pathlib import Path

import pet.autostart as autostart


def test_command_quotes_executable_and_main(monkeypatch):
    monkeypatch.setattr(autostart, "MAIN", Path(r"D:\桌宠\main.py"))
    monkeypatch.setattr(autostart.sys, "executable", r"C:\Python\pythonw.exe")
    assert autostart.command() == '"C:\\Python\\pythonw.exe" "D:\\桌宠\\main.py"'


def test_command_prefers_pythonw(tmp_path, monkeypatch):
    python = tmp_path / "python.exe"
    pythonw = tmp_path / "pythonw.exe"
    python.write_bytes(b"")
    pythonw.write_bytes(b"")
    monkeypatch.setattr(autostart.sys, "executable", str(python))
    monkeypatch.setattr(autostart, "MAIN", tmp_path / "main.py")
    assert str(pythonw) in autostart.command()


def test_enable_writes_command_and_disable_removes(monkeypatch):
    writes: list[str | None] = []
    monkeypatch.setattr(
        autostart, "_write_value", lambda value: writes.append(value) or True
    )
    assert autostart.set_enabled(True)
    assert writes[-1] == autostart.command()
    assert autostart.set_enabled(False)
    assert writes[-1] is None


def test_is_enabled_reads_registry(monkeypatch):
    monkeypatch.setattr(autostart, "_read_value", lambda: "value")
    assert autostart.is_enabled()
    monkeypatch.setattr(autostart, "_read_value", lambda: None)
    assert not autostart.is_enabled()


def test_sync_repairs_missing_and_stale(monkeypatch):
    writes: list[str | None] = []
    monkeypatch.setattr(
        autostart, "_write_value", lambda value: writes.append(value) or True
    )
    monkeypatch.setattr(autostart, "_read_value", lambda: None)
    assert autostart.sync(True)
    assert writes == [autostart.command()]
    writes.clear()
    assert autostart.sync(False)
    assert writes == []

    monkeypatch.setattr(autostart, "_read_value", lambda: "stale")
    writes.clear()
    assert autostart.sync(True)
    assert writes == [autostart.command()]
    writes.clear()
    assert autostart.sync(False)
    assert writes == [None]

    monkeypatch.setattr(autostart, "_read_value", lambda: autostart.command())
    writes.clear()
    assert autostart.sync(True)
    assert writes == []

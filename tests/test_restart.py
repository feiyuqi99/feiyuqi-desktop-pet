from __future__ import annotations

import os
import subprocess
import sys

import pet.restart as restart


def test_pid_alive_for_self_and_dead_child():
    assert restart.pid_alive(os.getpid()) is True
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    assert restart.pid_alive(child.pid) is False


def test_wait_for_exit_returns_once_parent_gone():
    calls = []

    def alive(pid):
        calls.append(pid)
        return len(calls) < 3

    assert restart.wait_for_exit(123, timeout=1.0, poll=0.0, alive=alive) is True
    assert len(calls) == 3


def test_wait_for_exit_times_out_while_parent_lives():
    assert (
        restart.wait_for_exit(123, timeout=0.05, poll=0.01, alive=lambda pid: True)
        is False
    )


def test_spawn_uses_pythonw_main_and_wait_pid(monkeypatch, tmp_path):
    captured = {}

    class FakePopen:
        def __init__(self, args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs

    monkeypatch.setattr(restart.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(restart.autostart, "MAIN", tmp_path / "main.py")
    monkeypatch.setattr(
        restart.autostart, "_pythonw", lambda: tmp_path / "pythonw.exe"
    )
    assert restart.spawn(4242) is True
    args = captured["args"]
    assert args[0].endswith("pythonw.exe")
    assert args[1].endswith("main.py")
    assert args[2:] == ["--wait-pid", "4242"]
    assert captured["kwargs"]["cwd"] == str(tmp_path)


def test_spawn_returns_false_on_oserror(monkeypatch):
    def boom(*a, **k):
        raise OSError("nope")

    monkeypatch.setattr(restart.subprocess, "Popen", boom)
    assert restart.spawn(1) is False


def test_restart_saves_spawns_and_quits(monkeypatch):
    from pet.app import PetApp

    app = PetApp.__new__(PetApp)
    events = []
    app._save_state_sync = lambda: events.append("save")
    app.bubble = type("B", (), {"hide": lambda self: events.append("bubble")})()
    app.window = type("W", (), {"hide": lambda self: events.append("window")})()
    app.tray = type("T", (), {"hide": lambda self: events.append("tray")})()
    app.qt_app = type("Q", (), {"quit": lambda self: events.append("quit")})()
    monkeypatch.setattr(restart, "spawn", lambda pid: events.append(("spawn", pid)) or True)
    app._restart()
    assert events[0] == "save"
    assert ("spawn", os.getpid()) in events
    assert events[-1] == "quit"


def test_restart_keeps_running_if_spawn_fails(monkeypatch):
    from pet.app import PetApp

    app = PetApp.__new__(PetApp)
    events = []
    app._save_state_sync = lambda: events.append("save")
    app.bubble = type("B", (), {"hide": lambda self: events.append("bubble")})()
    app.window = type("W", (), {"hide": lambda self: events.append("window")})()
    app.tray = type("T", (), {"hide": lambda self: events.append("tray")})()
    app.qt_app = type("Q", (), {"quit": lambda self: events.append("quit")})()
    monkeypatch.setattr(restart, "spawn", lambda pid: False)
    app._restart()
    assert "quit" not in events
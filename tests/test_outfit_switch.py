from __future__ import annotations

from types import SimpleNamespace

from pet.app import PetApp


def _stub_app(record):
    app = PetApp.__new__(PetApp)
    app.config = SimpleNamespace(outfit="jk")
    app.window = SimpleNamespace(set_outfit=lambda outfit: None)
    app.behavior = SimpleNamespace(
        express=lambda name, now, seconds: record.append(name)
    )
    app._speak = lambda *a, **k: None
    app._context = lambda now: None
    app._save_state = lambda: None
    return app


def test_switching_outfit_does_not_close_an_eye():
    record = []
    app = _stub_app(record)
    app._set_outfit("maid")
    assert record == ["sparkle"]

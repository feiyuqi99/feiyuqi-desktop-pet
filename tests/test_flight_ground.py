from __future__ import annotations

from types import SimpleNamespace

import pytest

import pet.app as app_module
from pet.app import FEET_Y, PetApp
from pet.behavior import Behavior


class FakeWindow:
    def __init__(self) -> None:
        self.x_pos = 1000.0
        self.y_pos = 1100.0
        self.moves = 0

    def x(self) -> int:
        return int(self.x_pos)

    def y(self) -> int:
        return int(self.y_pos)

    def width(self) -> int:
        return 248

    def height(self) -> int:
        return 216

    def move(self, x: int, y: int) -> None:
        self.moves += 1
        self.x_pos, self.y_pos = float(x), float(y)


@pytest.fixture
def floor_pet(monkeypatch):
    app = PetApp.__new__(PetApp)
    app.config = SimpleNamespace(
        settings=SimpleNamespace(throwable=True), mood=70, mood_updated_at=0.0
    )
    app.behavior = Behavior()
    app.window = FakeWindow()
    app.memory = SimpleNamespace(add_interaction=lambda: None, total_interactions=0)
    geometry = SimpleNamespace(
        left=lambda: 0, top=lambda: 0, right=lambda: 2560, bottom=lambda: 1440
    )
    app._screen_geometry = lambda: geometry
    app._inputs = lambda: []
    app._exclude_hwnds = lambda: frozenset()
    app._surface_below = lambda *a, **k: None
    app._request_scan = lambda *a, **k: None
    app._context = lambda now: None
    app._save_state = lambda: None
    app._speak = lambda *a, **k: None
    monkeypatch.setattr(app_module.support, "support_at", lambda *a, **k: None)
    monkeypatch.setattr(app_module.support, "input_host_at", lambda *a, **k: None)
    return app, geometry


def test_floor_slide_lands_once_instead_of_retriggering(floor_pet):
    app, geometry = floor_pet
    lands = []
    original = app.behavior.land

    def counting_land(now):
        lands.append(now)
        return original(now)

    app.behavior.land = counting_land
    app._on_drag_finished(900.0, 0.0)
    now = 1000.0
    for index in range(180):
        now += 1 / 60
        app._step_flight(1 / 60, now, geometry)
        if not app._flying and index > 10:
            break
    assert len(lands) == 1, lands
    assert app._grounded
    assert app.window.y() == 1225


def test_slide_on_a_real_surface_still_lands_once(floor_pet, monkeypatch):
    app, geometry = floor_pet
    top = 1225.0 + FEET_Y
    monkeypatch.setattr(
        app_module.support, "support_at", lambda *a, **k: top
    )
    lands = []
    original = app.behavior.land

    def counting_land(now):
        lands.append(now)
        return original(now)

    app.behavior.land = counting_land
    app._on_drag_finished(900.0, 0.0)
    now = 1000.0
    for index in range(180):
        now += 1 / 60
        app._step_flight(1 / 60, now, geometry)
        if not app._flying and index > 10:
            break
    assert len(lands) == 1, lands
    assert app._grounded
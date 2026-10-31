from __future__ import annotations

import logging
import random
import sys
import threading
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QIODevice, QObject, QPoint, QTimer, Qt
from PySide6.QtGui import QActionGroup, QFont, QGuiApplication, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu, QMessageBox, QSystemTrayIcon

from .animation import FEET_Y, SpriteLibrary
from .behavior import Behavior, BehaviorContext
from .bubble import BubbleManager
from .companion import Alert, Companion
from .config import (
    CONFIG_PATH,
    LOG_PATH,
    MEMORY_PATH,
    atomic_write_json,
    load_config,
)
from .dialogue import DialogueContext, DialogueEngine, Speech
from .lines import LINES
from .memory import Memory, load_memory
from .mood import change, decay, label as mood_label
from .perception import Perception, PerceptionState, time_band
from .persona import pet_name
from .window import PetWindow
from .uia import InputScanner
from . import support

ROOT = Path(__file__).resolve().parent.parent
TRAY_ICON = ROOT / "assets" / "icons" / "tray.png"
SINGLE_NAME = "ClaudePetInstance"

PART_MOOD = {
    "head": 3,
    "face": 1,
    "body": 2,
    "hand": 2,
    "skirt": -4,
    "feet": 1,
}

MENU_STYLE = """
QMenu {
    background: #F0EEE6;
    border: 1px solid #D97757;
    padding: 4px;
}
QMenu::item {
    padding: 6px 22px 6px 18px;
    color: #3D3929;
}
QMenu::item:selected {
    background: #E8D8CC;
}
QMenu::item:disabled {
    color: #9A9488;
}
QMenu::separator {
    height: 1px;
    background: #D9CFC3;
    margin: 4px 8px;
}
"""


class PetApp(QObject):
    def __init__(self, qt_app: QApplication) -> None:
        super().__init__()
        self.qt_app = qt_app
        self.aborted = False
        self._server: QLocalServer | None = None
        if not self._acquire_single_instance():
            self.aborted = True
            return

        self.config = load_config()
        self.memory = load_memory()
        self._was_new = self.memory.is_new
        now = time.time()
        self._startup_gap = self.memory.touch_session(now)
        if self._was_new:
            self.memory.mark_greeted(now)
        elif not self.memory.was_greeted_today(now):
            self.memory.bump_affection(1)
            self.memory.mark_greeted(now)
            self.memory.record_event("daily", now)
        self.config.mood, self.config.mood_updated_at = decay(
            self.config.mood, self.config.mood_updated_at, now
        )

        self._started_at = now
        self._last_tick = now
        self._last_idle_try = 0.0
        self._last_greet_try = 0.0
        self._last_anniversary = 0.0
        self._last_observe = 0.0
        self._last_tooltip = 0.0
        self._last_save = now
        self._followup_token = 0
        self._first_greeted = False
        self._error_shown = False
        self._pstate = PerceptionState()
        self._flying = False
        self._vx = 0.0
        self._vy = 0.0
        self._grounded = False
        self._fall_target = 0.0
        self._support_check_at = 0.0
        self._scanner = InputScanner()
        self._scan_at = 0.0
        self._input_host = 0
        self._save_lock = threading.Lock()

        self.sprites = SpriteLibrary()
        self.sprites.preload()
        self.window = PetWindow(self.sprites, self.build_context_menu)
        self.window.set_outfit(self.config.outfit)
        self.window.clicked.connect(self._on_clicked)
        self.window.double_clicked.connect(self._on_double_clicked)
        self.window.drag_started.connect(self._on_drag_started)
        self.window.drag_finished.connect(self._on_drag_finished)
        self.window.interacted.connect(self._on_interacted)

        self.bubble = BubbleManager()
        self.dialogue = DialogueEngine(LINES, self.memory)
        self.behavior = Behavior()
        self.perception = Perception(enabled=self.config.settings.perception)
        self.companion = Companion(
            now,
            sit_enabled=self.config.settings.sit_reminder,
            hourly_enabled=self.config.settings.hourly_chime,
            phase=self.config.pomodoro.phase,
            ends_at=self.config.pomodoro.ends_at,
        )
        self._restored_alert = self.companion.restore(now)
        if self._restored_alert is not None:
            self.config.pomodoro.phase = self.companion.phase
            self.config.pomodoro.ends_at = self.companion.ends_at

        self._place_window()
        self.window.show_pet()
        self._request_scan(time.time())

        self.tray = QSystemTrayIcon(QIcon(str(TRAY_ICON)), self.qt_app)
        self._tray_menu = self._build_tray_menu()
        self.tray.setContextMenu(self._tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()
        self._update_tooltip()

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._tick)
        self._tick_timer.start(33)

        QTimer.singleShot(700, self._startup_greeting)
        if self._restored_alert is not None:
            QTimer.singleShot(1800, self._show_restored_alert)
        self.qt_app.aboutToQuit.connect(self._on_quit)
        logging.info("pet started; new=%s gap=%.0fs", self._was_new, self._startup_gap)
        if not self._was_new:
            self._save_state()

    def _acquire_single_instance(self) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(SINGLE_NAME, QIODevice.WriteOnly)
        if socket.waitForConnected(250):
            socket.write(b"show")
            socket.waitForBytesWritten(250)
            socket.disconnectFromServer()
            return False
        QLocalServer.removeServer(SINGLE_NAME)
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_new_connection)
        if not self._server.listen(SINGLE_NAME):
            logging.warning("single instance server failed: %s", self._server.errorString())
        return True

    def _on_new_connection(self) -> None:
        if self._server is None:
            return
        while self._server.hasPendingConnections():
            connection = self._server.nextPendingConnection()
            if connection is not None:
                connection.waitForReadyRead(50)
                connection.readAll()
                connection.disconnectFromServer()
                connection.deleteLater()
        self.window.show_pet()
        self.window.raise_()
        logging.info("second instance request: show")

    def _place_window(self) -> None:
        screen = None
        if self.config.x is not None and self.config.y is not None:
            screen = QGuiApplication.screenAt(
                QPoint(self.config.x + self.window.width() // 2, self.config.y + self.window.height() // 2)
            )
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        geometry = screen.availableGeometry()
        if self.config.x is None or self.config.y is None:
            x = geometry.right() - self.window.width() - 24
            y = geometry.bottom() - self.window.height() - 12
        else:
            x = max(geometry.left(), min(self.config.x, geometry.right() - self.window.width()))
            y = max(geometry.top(), min(self.config.y, geometry.bottom() - self.window.height()))
        self.window.move(x, y)
        self.config.x = x
        self.config.y = y
        if self.config.home_x is None or self.config.home_y is None:
            self.config.home_x = x
            self.config.home_y = y

    def _screen_geometry(self):
        screen = QGuiApplication.screenAt(self.window.frameGeometry().center())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        return screen.availableGeometry()

    def _context(self, now: float) -> DialogueContext:
        self._pstate = self.perception.poll(now, manual_quiet=now < self.config.quiet_until)
        gap = self._startup_gap if now - self._started_at < 3.0 else 0.0
        return DialogueContext(
            now=now,
            time_band=time_band(now),
            activity=self._pstate.activity,
            idle_seconds=self._pstate.idle_seconds,
            quiet=self._pstate.quiet or now < self.config.quiet_until,
            mood=self.config.mood,
            relationship=self.memory.relationship,
            chattiness=self.config.settings.chattiness,
            gap=gap,
        )

    def _tick(self) -> None:
        try:
            now = time.time()
            dt = max(0.0, min(0.12, now - self._last_tick))
            self._last_tick = now
            self.config.mood, self.config.mood_updated_at = decay(
                self.config.mood, self.config.mood_updated_at, now
            )
            ctx = self._context(now)
            geometry = self._screen_geometry()
            if self.behavior.mode == "drag" or self._flying:
                self._request_scan(now, 0.8)
            elif self._input_host:
                self._request_scan(now, 1.5, self._input_host)
            if self.behavior.mode == "drag":
                vx, vy = self.window.drag_velocity()
                self.behavior.set_drag_motion(vx, vy)
            behavior_ctx = BehaviorContext(
                now=now,
                time_band=ctx.time_band,
                activity=ctx.activity,
                idle_seconds=ctx.idle_seconds,
                quiet=ctx.quiet or not self.window.isVisible(),
                mood=self.config.mood,
                gap=0.0,
                pet_x=self.window.x(),
                screen_left=geometry.left(),
                screen_right=geometry.right() - self.window.width(),
            )
            state = self.behavior.tick(behavior_ctx)
            if state.move_speed and self.window.isVisible():
                x = self.window.x() + int(round(state.move_speed * dt))
                x = max(geometry.left(), min(x, geometry.right() - self.window.width()))
                self.window.move(x, self.window.y())
            if self._flying and self.window.isVisible():
                self._step_flight(dt, now, geometry)
            self._check_support(now, geometry)
            self.window.apply_state(state)
            if self.window.isVisible():
                self.bubble.follow(self.window.frameGeometry(), geometry)
            elif self.bubble.busy or self.bubble.bubble.isVisible():
                self.bubble.hide()

            for action in self.behavior.drain():
                if action.kind == "speak":
                    held = action.event == "drag_hold" and not ctx.quiet
                    self._speak(action.event, ctx, force=held, priority=held)

            for alert in self.companion.tick(now):
                self._alert_speak(alert, ctx)

            if not self._first_greeted and not ctx.quiet and now - self._last_greet_try > 5:
                self._last_greet_try = now
                self._startup_greeting()

            if now - self._last_observe >= 60:
                self._last_observe = now
                self.memory.observe(ctx.activity, now)

            if now - self._last_idle_try >= 30:
                self._last_idle_try = now
                self._maybe_unsolicited(ctx)

            if now - self._last_anniversary >= 60:
                self._last_anniversary = now
                self._maybe_anniversary(ctx)

            if now - self._last_tooltip >= 5:
                self._last_tooltip = now
                self._update_tooltip()

            if now - self._last_save >= 60:
                self._last_save = now
                self._save_state()

            interval = 16 if self._flying else 33
            if self._tick_timer.interval() != interval:
                self._tick_timer.setInterval(interval)
        except Exception:
            logging.exception("tick failed")
            if not self._error_shown:
                self._error_shown = True
                self._direct_bubble("……我好像卡住了。")

    def _startup_greeting(self) -> None:
        if self._first_greeted:
            return
        now = time.time()
        ctx = self._context(now)
        if ctx.quiet:
            return
        if self._was_new:
            speech = self.dialogue.maybe_speak("greet_first", ctx, allow_silence=False)
            self._first_greeted = True
            if speech is not None:
                self._handle_speech(speech, 5200)
                if self.config.settings.perception:
                    notice = self.dialogue.maybe_speak(
                        "perception_on", ctx, force=True, allow_silence=False
                    )
                    if notice is not None:
                        self._handle_speech(notice, 6500)
                self.memory.record_event("first_meeting", now)
            self._save_state()
            return
        event = (
            "greet_long"
            if self._startup_gap >= 86400
            else "greet_return"
            if self._startup_gap >= 1800
            else "greet"
        )
        speech = self.dialogue.maybe_speak(event, ctx, allow_silence=False)
        self._first_greeted = True
        if speech is not None:
            self._handle_speech(speech, 4200)
            self.memory.record_event("startup", now)
            self._save_state()

    def _show_restored_alert(self) -> None:
        if self._restored_alert is None:
            return
        alert = self._restored_alert
        self._restored_alert = None
        self._alert_speak(alert, self._context(time.time()))

    def _maybe_unsolicited(self, ctx: DialogueContext) -> None:
        if not self._first_greeted or not self.window.isVisible() or ctx.quiet:
            return
        if self.behavior.mode not in ("idle", "wander", "pet", "poke"):
            return
        if ctx.idle_seconds > 300:
            return
        hour = datetime.fromtimestamp(ctx.now).hour
        event = "idle"
        if hour >= 23 or hour < 2:
            event = "late_night"
        elif self.memory.late_night_streak(ctx.now) >= 3 and not self.memory.has_event(
            "late_streak", 1, ctx.now
        ):
            event = "late_streak"
        elif (
            (self.memory.relationship != "new" or self.memory.affection >= 12)
            and ctx.mood >= 55
            and random.random() < 0.15
        ):
            event = "affection"
        elif ctx.activity == "coding":
            event = "coding"
        self._speak(event, ctx)

    def _maybe_anniversary(self, ctx: DialogueContext) -> None:
        if not self._first_greeted:
            return
        days = self.memory.days_known
        if days not in (7, 30, 100):
            return
        event = f"anniversary_{days}"
        if ctx.quiet or self.memory.has_event(event, 3650, ctx.now):
            return
        self._speak(event, ctx)

    def _speak(
        self,
        event: str,
        ctx: DialogueContext,
        force: bool = False,
        hold: int = 4200,
        priority: bool = False,
    ):
        speech = self.dialogue.maybe_speak(event, ctx, force=force)
        if speech is None:
            return None
        self._handle_speech(speech, hold, priority)
        if event == "late_streak":
            self.memory.record_event("late_streak", ctx.now)
        if event.startswith("anniversary_"):
            self.memory.record_event(event, ctx.now)
        return speech

    def _handle_speech(self, speech: Speech, hold: int = 4200, priority: bool = False) -> None:
        if not self.window.isVisible():
            return
        self.bubble.enqueue(speech.text, hold, speech.delay_ms, priority)
        if speech.followup:
            token = self._followup_token
            QTimer.singleShot(
                speech.delay_ms + 1700,
                lambda: self._followup(speech.followup, token),
            )

    def _followup(self, text: str | None, token: int) -> None:
        if text is None or token != self._followup_token:
            return
        if not self.window.isVisible() or self._is_quiet():
            return
        self.bubble.enqueue(text, 3200)

    def _alert_speak(self, alert: Alert, ctx: DialogueContext) -> None:
        speech = self.dialogue.alert(alert.event, ctx)
        if speech is not None:
            self._handle_speech(speech, 6200, priority=True)
        if alert.kind in ("pomo_end", "pomo_break_end", "pomo_missed"):
            self._beep()
            if not self.window.isVisible():
                message = speech.text if speech is not None else "时间到了。"
                self.tray.showMessage(
                    "小橘", message, QSystemTrayIcon.Information, 6000
                )
        if alert.kind == "pomo_end":
            self.config.mood = change(self.config.mood, 8)
            self.config.mood_updated_at = ctx.now
            self.memory.bump_affection(3)
        if alert.kind.startswith("pomo"):
            self.config.pomodoro.phase = self.companion.phase
            self.config.pomodoro.ends_at = self.companion.ends_at
            self._save_state()

    def _is_quiet(self) -> bool:
        return self._pstate.quiet or time.time() < self.config.quiet_until

    def _beep(self) -> None:
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

    def _on_interacted(self) -> None:
        self._followup_token += 1
        now = time.time()
        self.behavior.interrupt()
        self.behavior.last_input = now
        self.behavior.next_wander = now + 30

    def _on_clicked(self, part: str) -> None:
        now = time.time()
        if self.behavior.mode == "annoyed" and now < self.behavior.annoyed_until:
            return
        self._on_interacted()
        self.behavior.on_click(now, part)
        self.memory.add_interaction()
        self._bump_affection()
        self.config.mood = change(self.config.mood, PART_MOOD.get(part, 2))
        self.config.mood_updated_at = now
        ctx = self._context(now)
        for action in self.behavior.drain():
            if action.kind == "speak":
                self._speak(action.event, ctx)
        self._maybe_name_ask(ctx)

    def _on_double_clicked(self) -> None:
        now = time.time()
        if self.behavior.mode == "annoyed" and now < self.behavior.annoyed_until:
            return
        self._on_interacted()
        self.behavior.on_double_click(now)
        self.memory.add_interaction()
        self._bump_affection()
        self.config.mood = change(self.config.mood, 5)
        self.config.mood_updated_at = now
        ctx = self._context(now)
        for action in self.behavior.drain():
            if action.kind == "speak":
                self._speak(action.event, ctx)

    def _on_drag_started(self) -> None:
        now = time.time()
        self._flying = False
        self._grounded = False
        self._input_host = 0
        self._vx = 0.0
        self._vy = 0.0
        self._on_interacted()
        self.behavior.on_drag_start(now)
        self._request_scan(now)
        ctx = self._context(now)
        for action in self.behavior.drain():
            if action.kind == "speak":
                self._speak(action.event, ctx)

    def _on_drag_finished(self, vx: float, vy: float) -> None:
        now = time.time()
        self.behavior.on_drag_end(now, vx)
        self.memory.add_interaction()
        self._bump_affection()
        if abs(vx) > 1500:
            self.config.mood = change(self.config.mood, -2)
            self.config.mood_updated_at = now
        geometry = self._screen_geometry()
        feet = self.window.y() + FEET_Y
        floor_feet = self._feet_floor(geometry)
        center = self.window.x() + self.window.width() // 2
        inputs = self._inputs()
        top = support.support_at(center, feet, self._exclude_hwnds(), inputs=inputs)
        if top is not None:
            target = float(top)
        else:
            surface = self._surface_below(feet, floor_feet, inputs)
            target = floor_feet if surface is None else float(surface)
        calm = abs(vx) < 80 and abs(vy) < 80
        if calm and top is not None:
            self.window.move(self.window.x(), int(round(target - FEET_Y)))
            self._flying = False
            self._grounded = False
            self._input_host = support.input_host_at(center, top, inputs) or 0
            self._vx = 0.0
            self._vy = 0.0
            self.behavior.land(now)
        else:
            self._flying = True
            self._grounded = False
            self._input_host = 0
            self._vx = max(-1800.0, min(1800.0, vx))
            self._vy = max(-1600.0, min(1600.0, vy))
            self._fall_target = target
            self.behavior.start_fall(now)
        self._support_check_at = now + 0.4
        self._request_scan(now)
        ctx = self._context(now)
        for action in self.behavior.drain():
            if action.kind == "speak":
                self._speak(action.event, ctx)
        self._save_state()

    def _feet_floor(self, geometry) -> float:
        return geometry.bottom() - (self.window.height() - FEET_Y) + 1

    def _exclude_hwnds(self) -> frozenset[int]:
        handles = {int(self.window.winId())}
        if self.bubble.bubble.isVisible():
            handles.add(int(self.bubble.bubble.winId()))
        return frozenset(handles)

    def _request_scan(self, now: float, interval: float = 0.0, host: int | None = None) -> None:
        if now - self._scan_at < interval:
            return
        self._scan_at = now
        self._scanner.request(self._exclude_hwnds(), host)

    def _inputs(self) -> list[tuple[int, int, int, int, int]]:
        return self._scanner.snapshot()

    def _surface_below(
        self,
        feet: float,
        floor_feet: float,
        inputs: list[tuple[int, int, int, int, int]] | None = None,
    ) -> int | None:
        center = self.window.x() + self.window.width() // 2
        if inputs is None:
            inputs = self._inputs()
        return support.surface_below(
            center, feet + 1, floor_feet, self._exclude_hwnds(), inputs
        )

    def _begin_fall(self, now: float, feet: float, floor_feet: float) -> None:
        surface = self._surface_below(feet, floor_feet)
        self._fall_target = floor_feet if surface is None else float(surface)
        self._flying = True
        self._grounded = False
        self._vy = 0.0
        self.behavior.start_fall(now)

    def _step_flight(self, dt: float, now: float, geometry) -> None:
        dt = min(dt, 0.05)
        x = float(self.window.x())
        y = float(self.window.y())

        if self._vx:
            x += self._vx * dt
            left = float(geometry.left())
            right = float(geometry.right() - self.window.width())
            if x < left:
                x = left
                self._vx = -self._vx * 0.45
            elif x > right:
                x = right
                self._vx = -self._vx * 0.45
            decay = 5.0 if self._grounded else 0.5
            self._vx *= max(0.0, 1.0 - decay * dt)
            if abs(self._vx) < 12.0:
                self._vx = 0.0

        if self._grounded:
            lost = False
            if now >= self._support_check_at:
                self._support_check_at = now + 0.12
                feet = y + FEET_Y
                center = int(round(x)) + self.window.width() // 2
                inputs = self._inputs()
                top = support.support_at(
                    center, feet, self._exclude_hwnds(), inputs=inputs
                )
                host = support.input_host_at(center, top, inputs) if top is not None else None
                self._input_host = host or 0
                if top is None:
                    lost = True
                    self._grounded = False
                    floor_feet = self._feet_floor(geometry)
                    surface = self._surface_below(feet, floor_feet, inputs)
                    self._fall_target = floor_feet if surface is None else float(surface)
                    self.behavior.start_fall(now)
            if not lost and not self._vx:
                self._flying = False
                return
            self.window.move(int(round(x)), int(round(y)))
            return

        previous = self._vy
        self._vy = min(1800.0, self._vy + 2400.0 * dt)
        if previous < 0.0 <= self._vy:
            surface = self._surface_below(y + FEET_Y, self._feet_floor(geometry))
            if surface is not None:
                self._fall_target = float(surface)
        y += self._vy * dt
        if y < geometry.top():
            y = geometry.top()
            self._vy = -self._vy * 0.35
        target_y = self._fall_target - FEET_Y
        if y >= target_y and self._vy > 0:
            y = target_y
            if self._vy > 520.0:
                self._vy = -self._vy * 0.32
                self.behavior.bounce(now)
            else:
                self._vy = 0.0
                self._grounded = True
                self.behavior.land(now)
                self._support_check_at = now + 0.12
                if not self._vx:
                    self._flying = False
        self.window.move(int(round(x)), int(round(y)))

    def _check_support(self, now: float, geometry) -> None:
        if not self.window.isVisible() or self._flying or self.behavior.mode == "drag":
            return
        if now < self._support_check_at:
            return
        self._support_check_at = now + 0.5
        feet = self.window.y() + FEET_Y
        floor_feet = self._feet_floor(geometry)
        if feet >= floor_feet - 2:
            self._input_host = 0
            return
        center = self.window.x() + self.window.width() // 2
        inputs = self._inputs()
        top = support.support_at(
            center,
            feet,
            self._exclude_hwnds(),
            inputs=inputs,
        )
        if top is None:
            self._input_host = 0
            self._begin_fall(now, feet, floor_feet)
        else:
            self._input_host = support.input_host_at(center, top, inputs) or 0

    def _bump_affection(self) -> None:
        if self.memory.total_interactions > 0 and self.memory.total_interactions % 15 == 0:
            self.memory.bump_affection(1)

    def _maybe_name_ask(self, ctx: DialogueContext) -> None:
        if ctx.quiet or self.memory.user_name:
            return
        if self.memory.has_event("name_asked", 3650, ctx.now):
            return
        if self.memory.days_known < 3 and self.memory.total_interactions < 20:
            return
        speech = self.dialogue.alert("name_ask", ctx)
        if speech is not None:
            self._handle_speech(speech, 6500)
            self.memory.record_event("name_asked", ctx.now)

    def _direct_bubble(self, text: str) -> None:
        if self.window.isVisible():
            self.bubble.enqueue(text, 3000)

    def _update_tooltip(self) -> None:
        text = f"{pet_name(self.memory)} · {mood_label(self.config.mood)} · 认识第 {self.memory.days_known} 天"
        if self.companion.phase != "idle":
            remaining = self.companion.remaining(time.time())
            minutes, seconds = divmod(remaining, 60)
            phase = "专注" if self.companion.phase == "focus" else "休息"
            text += f" · {phase} {minutes:02d}:{seconds:02d}"
        self.tray.setToolTip(text)

    def _save_state(self) -> None:
        self._sync_position()
        self._save_snapshots(asdict(self.config), asdict(self.memory))

    def _save_state_sync(self) -> None:
        self._sync_position()
        with self._save_lock:
            atomic_write_json(CONFIG_PATH, asdict(self.config))
            atomic_write_json(MEMORY_PATH, asdict(self.memory))

    def _sync_position(self) -> None:
        self.config.x = self.window.x()
        self.config.y = self.window.y()
        self.config.pomodoro.phase = self.companion.phase
        self.config.pomodoro.ends_at = self.companion.ends_at

    def _save_snapshots(self, config: dict, memory: dict) -> None:
        if not self._save_lock.acquire(blocking=False):
            return

        def work() -> None:
            try:
                atomic_write_json(CONFIG_PATH, config)
                atomic_write_json(MEMORY_PATH, memory)
            except Exception:
                logging.exception("async save failed")
            finally:
                self._save_lock.release()

        threading.Thread(target=work, daemon=True).start()

    def _on_quit(self) -> None:
        try:
            self._save_state_sync()
        except Exception:
            logging.exception("save failed on quit")
        try:
            self._scanner.close()
        except Exception:
            logging.exception("scanner close failed")
        logging.info("pet quit")

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self._toggle_visibility()

    def _toggle_visibility(self) -> None:
        if self.window.isVisible():
            self._flying = False
            self._grounded = False
            self._vx = 0.0
            self._vy = 0.0
            self.window.hide()
            self.bubble.hide()
        else:
            self.window.show_pet()
            self.window.raise_()

    def _style_menu(self, menu: QMenu) -> None:
        menu.setStyleSheet(MENU_STYLE)

    def _all_actions(self, menu: QMenu):
        for action in menu.actions():
            submenu = action.menu()
            if submenu is not None:
                yield from self._all_actions(submenu)
            else:
                yield action

    def _build_tray_menu(self) -> QMenu:
        menu = QMenu()
        self._style_menu(menu)
        self._populate_menu(menu, full=True)
        menu.aboutToShow.connect(self._sync_menu)
        return menu

    def build_context_menu(self):
        menu = QMenu(self.window)
        self._style_menu(menu)
        self._populate_menu(menu, full=False)
        return menu

    def _populate_menu(self, menu: QMenu, full: bool) -> None:
        action = menu.addAction("摸摸头")
        action.triggered.connect(lambda: self._on_clicked("head"))
        action = menu.addAction("说句话")
        action.triggered.connect(lambda: self._on_clicked("body"))

        outfit_menu = menu.addMenu("换衣服")
        self._style_menu(outfit_menu)
        outfit_group = QActionGroup(outfit_menu)
        outfit_group.setExclusive(True)
        for label, value in (("女仆装", "maid"), ("便服", "casual")):
            item = outfit_menu.addAction(label)
            item.setCheckable(True)
            item.setChecked(self.config.outfit == value)
            item.setData(f"outfit:{value}")
            outfit_group.addAction(item)
            item.triggered.connect(lambda checked=False, value=value: self._set_outfit(value))

        pomo_menu = menu.addMenu("一起专注")
        self._style_menu(pomo_menu)
        info = pomo_menu.addAction(self._pomo_info_text())
        info.setEnabled(False)
        info.setData("pomo_info")
        pomo_menu.addSeparator()
        item = pomo_menu.addAction("开始专注")
        item.triggered.connect(self._start_focus)
        item = pomo_menu.addAction("休息五分钟")
        item.triggered.connect(self._start_break)
        item = pomo_menu.addAction("停止")
        item.triggered.connect(self._stop_pomodoro)

        action = menu.addAction("安静一会儿（30 分钟）")
        action.triggered.connect(self._quiet_30)
        action = menu.addAction("给我起个名字")
        action.triggered.connect(self._rename)
        action = menu.addAction("记住这个位置")
        action.triggered.connect(self._set_home)
        action = menu.addAction("回到原位")
        action.triggered.connect(self._go_home)

        if full:
            menu.addSeparator()
            action = menu.addAction("久坐提醒")
            action.setCheckable(True)
            action.setChecked(self.config.settings.sit_reminder)
            action.setData("sit")
            action.triggered.connect(lambda checked=False: self._set_sit(checked))

            action = menu.addAction("整点报时")
            action.setCheckable(True)
            action.setChecked(self.config.settings.hourly_chime)
            action.setData("hourly")
            action.triggered.connect(lambda checked=False: self._set_hourly(checked))

            action = menu.addAction("环境感知")
            action.setCheckable(True)
            action.setChecked(self.config.settings.perception)
            action.setData("perception")
            action.triggered.connect(lambda checked=False: self._set_perception(checked))

            action = menu.addAction("始终置顶")
            action.setCheckable(True)
            action.setChecked(self.config.settings.always_on_top)
            action.setData("always_top")
            action.triggered.connect(lambda checked=False: self._set_always_top(checked))

            chat_menu = menu.addMenu("话多程度")
            self._style_menu(chat_menu)
            chat_group = QActionGroup(chat_menu)
            chat_group.setExclusive(True)
            for label, value in (("安静", "quiet"), ("正常", "normal"), ("话痨", "chatty")):
                item = chat_menu.addAction(label)
                item.setCheckable(True)
                item.setChecked(self.config.settings.chattiness == value)
                item.setData(f"chattiness:{value}")
                chat_group.addAction(item)
                item.triggered.connect(lambda checked=False, value=value: self._set_chattiness(value))

            action = menu.addAction("清空记忆")
            action.triggered.connect(self._clear_memory)

        menu.addSeparator()
        action = menu.addAction("隐藏" if self.window.isVisible() else "显示")
        action.setData("toggle")
        action.triggered.connect(self._toggle_visibility)
        action = menu.addAction("先去睡了")
        action.triggered.connect(self._exit)

    def _sync_menu(self) -> None:
        for action in self._all_actions(self._tray_menu):
            data = action.data()
            if data == "sit":
                action.setChecked(self.config.settings.sit_reminder)
            elif data == "hourly":
                action.setChecked(self.config.settings.hourly_chime)
            elif data == "perception":
                action.setChecked(self.config.settings.perception)
            elif data == "always_top":
                action.setChecked(self.config.settings.always_on_top)
            elif data == "toggle":
                action.setText("隐藏" if self.window.isVisible() else "显示")
            elif isinstance(data, str) and data.startswith("outfit:"):
                action.setChecked(self.config.outfit == data.split(":", 1)[1])
            elif isinstance(data, str) and data.startswith("chattiness:"):
                action.setChecked(self.config.settings.chattiness == data.split(":", 1)[1])
            elif data == "pomo_info":
                action.setText(self._pomo_info_text())

    def _pomo_info_text(self) -> str:
        if self.companion.phase == "idle":
            return "空闲"
        remaining = self.companion.remaining(time.time())
        minutes, seconds = divmod(remaining, 60)
        phase = "专注" if self.companion.phase == "focus" else "休息"
        return f"{phase} · {minutes:02d}:{seconds:02d}"

    def _set_outfit(self, outfit: str) -> None:
        if outfit not in ("maid", "casual") or outfit == self.config.outfit:
            return
        self.config.outfit = outfit
        self.window.set_outfit(outfit)
        event = "outfit_maid" if outfit == "maid" else "outfit_casual"
        self._speak(event, self._context(time.time()), force=True)
        self._save_state()

    def _start_focus(self) -> None:
        now = time.time()
        alert = self.companion.start_focus(now)
        self._alert_speak(alert, self._context(now))
        self._save_state()

    def _start_break(self) -> None:
        now = time.time()
        alert = self.companion.start_break(now)
        self._alert_speak(alert, self._context(now))
        self._save_state()

    def _stop_pomodoro(self) -> None:
        now = time.time()
        self.companion.stop()
        self._alert_speak(Alert("pomo_stop", "pomo_stop"), self._context(now))
        self._save_state()

    def _set_sit(self, checked: bool) -> None:
        self.config.settings.sit_reminder = checked
        self.companion.sit_enabled = checked
        if checked:
            self.companion.reset_sit(time.time())
        self._save_state()
        self._direct_bubble("好，我会记得提醒你。" if checked else "好，那我不提醒了。")

    def _set_hourly(self, checked: bool) -> None:
        self.config.settings.hourly_chime = checked
        self.companion.hourly_enabled = checked
        self._save_state()
        self._direct_bubble("整点我会说一声。" if checked else "好，不报时了。")

    def _set_perception(self, checked: bool) -> None:
        self.config.settings.perception = checked
        self.perception.set_enabled(checked)
        self._save_state()
        event = "perception_on" if checked else "perception_off"
        self._speak(event, self._context(time.time()), force=True)

    def _set_always_top(self, checked: bool) -> None:
        self.config.settings.always_on_top = checked
        self.window.set_always_on_top(checked)
        self._save_state()

    def _set_chattiness(self, value: str) -> None:
        if value not in ("quiet", "normal", "chatty"):
            return
        self.config.settings.chattiness = value
        self._save_state()
        self._speak(f"chattiness_{value}", self._context(time.time()), force=True)

    def _quiet_30(self) -> None:
        self.config.quiet_until = time.time() + 30 * 60
        self._save_state()
        self._speak("quiet", self._context(time.time()), force=True)

    def _set_home(self) -> None:
        self.config.home_x = self.window.x()
        self.config.home_y = self.window.y()
        self._save_state()
        self._direct_bubble("好，这里就是家。")

    def _go_home(self) -> None:
        geometry = self._screen_geometry()
        home_x = self.config.home_x
        home_y = self.config.home_y
        if home_x is None or home_y is None:
            home_x = geometry.right() - self.window.width() - 24
            home_y = geometry.bottom() - self.window.height() - 12
        x = max(geometry.left(), min(home_x, geometry.right() - self.window.width()))
        y = max(geometry.top(), min(home_y, geometry.bottom() - self.window.height()))
        self._flying = False
        self._grounded = False
        self._input_host = 0
        self._vx = 0.0
        self._vy = 0.0
        self.window.move(x, y)
        self._support_check_at = 0.0
        self._direct_bubble("回来了。")

    def _rename(self) -> None:
        text, ok = QInputDialog.getText(
            self.window, "给我起个名字", "你想叫我什么？", text=self.memory.pet_name
        )
        if not ok:
            return
        name = text.strip()[:12]
        if not name:
            return
        self.memory.pet_name = name
        self.window.setWindowTitle(name)
        self._save_state()
        self._speak("rename", self._context(time.time()), force=True)
        self._update_tooltip()

    def _clear_memory(self) -> None:
        answer = QMessageBox.question(
            self.window,
            "清空记忆",
            "要清空我们认识以来的记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        old_name = self.memory.pet_name
        now = time.time()
        self.memory = Memory(pet_name=old_name)
        self.memory.touch_session(now)
        self.memory.mark_greeted(now)
        self.dialogue = DialogueEngine(LINES, self.memory)
        self._was_new = False
        self._first_greeted = True
        self._save_state()
        self._speak("memory_cleared", self._context(now), force=True)
        self._update_tooltip()

    def _exit(self) -> None:
        self._speak("exit", self._context(time.time()), force=True, hold=2400)
        QTimer.singleShot(3000, self._finish_exit)

    def _finish_exit(self) -> None:
        self._save_state_sync()
        self.bubble.hide()
        self.window.hide()
        self.tray.hide()
        self.qt_app.quit()


def configure_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        encoding="utf-8",
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    configure_logging()
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("ClaudePet")
    app.setFont(QFont("Microsoft YaHei UI", 9))

    def excepthook(exc_type, exc_value, exc_tb):
        logging.error("uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

    sys.excepthook = excepthook
    pet = PetApp(app)
    if pet.aborted:
        return 0
    return app.exec()

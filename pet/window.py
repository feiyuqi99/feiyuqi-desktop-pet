from __future__ import annotations

import math
import time
from collections import deque
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPainter
from PySide6.QtWidgets import QWidget

from .animation import (
    DRAW_SIZE,
    FEET_X,
    FEET_Y,
    HEAD_BOTTOM,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    SpriteLibrary,
)
from .behavior import PetState
from .win_effects import apply_clean_window

ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "icons" / "pet.ico"


class PetWindow(QWidget):
    clicked = Signal(bool)
    double_clicked = Signal()
    drag_started = Signal()
    drag_finished = Signal(float)
    interacted = Signal()

    def __init__(self, sprites: SpriteLibrary, menu_factory=None) -> None:
        super().__init__(
            None,
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.NoDropShadowWindowHint,
        )
        self.sprites = sprites
        self.menu_factory = menu_factory
        self.state = PetState()
        self.outfit = "maid"
        self._hover_tilt = 0.0
        self._dragging = False
        self._double = False
        self._pending_head = False
        self._press_global = QPoint()
        self._drag_offset = QPoint()
        self._moves: deque[tuple[float, QPoint]] = deque()

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowTitle("小橘")
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._emit_click)

    def apply_state(self, state: PetState) -> None:
        self.state = state
        self.update()

    def set_outfit(self, outfit: str) -> None:
        self.outfit = outfit
        self.update()

    def set_always_on_top(self, enabled: bool) -> None:
        visible = self.isVisible()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        if visible:
            self.show()
            self.raise_()

    def show_pet(self) -> None:
        self.show()
        self.raise_()

    def drag_tilt_value(self) -> float:
        if not self._dragging:
            return 0.0
        now = time.monotonic()
        while self._moves and now - self._moves[0][0] > 0.15:
            self._moves.popleft()
        if len(self._moves) < 2:
            return 0.0
        t0, p0 = self._moves[0]
        t1, p1 = self._moves[-1]
        dt = max(0.001, t1 - t0)
        velocity = (p1.x() - p0.x()) / dt
        return max(-10.0, min(10.0, -velocity * 0.02))

    def _drag_speed(self) -> float:
        now = time.monotonic()
        while self._moves and now - self._moves[0][0] > 0.15:
            self._moves.popleft()
        if len(self._moves) < 2:
            return 0.0
        t0, p0 = self._moves[0]
        t1, p1 = self._moves[-1]
        dt = max(0.001, t1 - t0)
        return (p1.x() - p0.x()) / dt

    def _emit_click(self) -> None:
        self.clicked.emit(self._pending_head)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._click_timer.stop()
            self._double = False
            self._press_global = event.globalPosition().toPoint()
            self._drag_offset = self._press_global - self.pos()
            self._dragging = False
            self._moves.clear()
            self._moves.append((time.monotonic(), self._press_global))
            self.interacted.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton:
            global_pos = event.globalPosition().toPoint()
            if not self._dragging:
                delta = global_pos - self._press_global
                if math.hypot(delta.x(), delta.y()) > 5:
                    self._dragging = True
                    self._hover_tilt = 0.0
                    self.setCursor(Qt.ClosedHandCursor)
                    self.drag_started.emit()
            if self._dragging:
                target = global_pos - self._drag_offset
                screen = QGuiApplication.screenAt(global_pos) or QGuiApplication.primaryScreen()
                geometry = screen.availableGeometry()
                x = max(geometry.left(), min(target.x(), geometry.right() - self.width()))
                y = max(geometry.top(), min(target.y(), geometry.bottom() - self.height()))
                self.move(x, y)
                self._moves.append((time.monotonic(), global_pos))
                while self._moves and time.monotonic() - self._moves[0][0] > 0.15:
                    self._moves.popleft()
                self.update()
                event.accept()
                return
        else:
            self._hover_tilt = max(
                -2.5, min(2.5, (event.position().x() - WINDOW_WIDTH / 2) / (WINDOW_WIDTH / 2) * 2.5)
            )
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            if self._dragging:
                speed = self._drag_speed()
                self._dragging = False
                self.setCursor(Qt.ArrowCursor)
                self.drag_finished.emit(speed)
            elif self._double:
                self._double = False
            else:
                self._pending_head = event.position().y() < HEAD_BOTTOM
                self._click_timer.start(220)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._click_timer.stop()
            self._double = True
            self.double_clicked.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:
        self.interacted.emit()
        if self.menu_factory is not None:
            menu = self.menu_factory()
            if menu is not None:
                menu.exec(event.globalPos())
            event.accept()
            return
        super().contextMenuEvent(event)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover_tilt = 0.0
        self.update()
        super().leaveEvent(event)

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        apply_clean_window(int(self.winId()))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 30))
        painter.drawEllipse(QRectF(140, 292, 80, 12))

        pixmap = self.sprites.get(self.outfit, self.state.frame)
        painter.save()
        painter.translate(FEET_X, FEET_Y + self.state.bob)
        painter.rotate(self.state.tilt + self._hover_tilt)
        painter.scale(self.state.facing * self.state.scale, self.state.scale)
        painter.drawPixmap(
            QRectF(-DRAW_SIZE / 2, -FEET_Y, DRAW_SIZE, DRAW_SIZE),
            pixmap,
            QRectF(0, 0, pixmap.width(), pixmap.height()),
        )
        painter.restore()

        if self.state.zzz:
            now = time.monotonic()
            painter.setFont(QFont("Microsoft YaHei UI", 13, QFont.Bold))
            for index in range(3):
                phase = (now * 0.45 + index * 0.33) % 1.0
                alpha = int(170 * (1.0 - phase))
                painter.setPen(QColor(90, 80, 60, alpha))
                x = 248 + index * 9 + math.sin(now * 2.0 + index) * 3
                y = 76 - phase * 34 - index * 6
                painter.drawText(QPointF(x, y), "z")

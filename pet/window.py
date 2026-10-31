from __future__ import annotations

import math
import time
from collections import deque
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

from .animation import (
    DISPLAY_SCALE,
    FEET_X,
    FEET_Y,
    SPRITE_FEET_X,
    SPRITE_FEET_Y,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    SpriteLibrary,
    part_at,
)
from .behavior import PetState
from .win_effects import apply_clean_window

ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "icons" / "pet.ico"


class PetWindow(QWidget):
    clicked = Signal(str)
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
        self._pending_part = "body"
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

    def part_at_position(self, pos: QPointF) -> str | None:
        y = pos.y() - self.state.hop
        sx = int(round(SPRITE_FEET_X + (pos.x() - FEET_X) / DISPLAY_SCALE))
        sy = int(round(SPRITE_FEET_Y + (y - FEET_Y) / DISPLAY_SCALE))
        if self.sprites.alpha_at(self.outfit, "idle", sx, sy) < 24:
            return None
        return part_at(sx, sy)

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
        self.clicked.emit(self._pending_part)

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
                part = self.part_at_position(event.position())
                if part is not None:
                    self._pending_part = part
                    self._click_timer.start(220)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            if self.part_at_position(event.position()) is None:
                event.accept()
                return
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

        state = self.state
        lift = min(0.5, abs(state.hop) / 70.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, int(30 * (1.0 - lift * 0.6))))
        painter.drawEllipse(
            QRectF(
                FEET_X - 27 * (1.0 - lift * 0.4),
                FEET_Y - 5,
                54 * (1.0 - lift * 0.4),
                8,
            )
        )

        pixmap = self.sprites.get(self.outfit, state.frame)
        painter.save()
        painter.translate(FEET_X, FEET_Y + state.bob + state.hop)
        painter.rotate(state.tilt + self._hover_tilt)
        painter.scale(
            state.facing * state.scale * state.squash_x,
            state.scale * state.squash_y,
        )
        painter.scale(DISPLAY_SCALE, DISPLAY_SCALE)
        painter.translate(-SPRITE_FEET_X, -SPRITE_FEET_Y)
        painter.drawPixmap(0, 0, pixmap)
        self._draw_expression(painter, state)
        painter.restore()

        if state.zzz:
            now = time.monotonic()
            painter.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
            for index in range(3):
                phase = (now * 0.45 + index * 0.33) % 1.0
                alpha = int(170 * (1.0 - phase))
                painter.setPen(QColor(90, 80, 60, alpha))
                x = 172 + index * 7 + math.sin(now * 2.0 + index) * 2
                y = 58 - phase * 30 - index * 5
                painter.drawText(QPointF(x, y), "z")

    def _draw_expression(self, painter: QPainter, state: PetState) -> None:
        expression = state.expression
        if expression == "neutral" or expression == "sleepy":
            return
        now = time.monotonic()
        if expression == "blush":
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(240, 110, 132, 140))
            painter.drawEllipse(QRectF(176, 199, 40, 17))
            painter.drawEllipse(QRectF(296, 199, 40, 17))
        elif expression == "heart":
            for index in range(3):
                phase = (now * 0.7 + index * 0.33) % 1.0
                x = 262 + index * 11 + math.sin(now * 3.0 + index) * 4
                y = 48 - phase * 38
                self._heart(
                    painter,
                    x,
                    y,
                    26.0 * (1.0 - phase * 0.35),
                    int(235 * (1.0 - phase * 0.8)),
                )
        elif expression == "annoyed":
            pen = QPen(QColor(214, 79, 60, 235), 6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(186, 52), QPointF(208, 74))
            painter.drawLine(QPointF(208, 52), QPointF(186, 74))
            painter.drawLine(QPointF(180, 42), QPointF(214, 42))
            painter.drawLine(QPointF(180, 84), QPointF(214, 84))
        elif expression == "surprised":
            painter.setPen(QColor(255, 248, 238, 240))
            painter.setFont(QFont("Microsoft YaHei UI", 34, QFont.Bold))
            painter.drawText(QPointF(296, 46), "!")
        elif expression == "sparkle":
            for index in range(3):
                phase = (now * 0.9 + index * 0.33) % 1.0
                x = (248, 190, 318)[index] + math.sin(now * 2.4 + index) * 5
                y = (46, 72, 54)[index] - phase * 10
                self._sparkle(
                    painter,
                    x,
                    y,
                    22.0 * (1.0 - phase * 0.25),
                    int(235 * (1.0 - phase * 0.5)),
                )

    def _heart(self, painter: QPainter, x: float, y: float, size: float, alpha: int) -> None:
        painter.save()
        painter.translate(x, y)
        painter.scale(size / 12.0, size / 12.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(232, 106, 122, alpha))
        path = QPainterPath()
        path.moveTo(0, 4)
        path.cubicTo(-7, -4, -14, 3, 0, 12)
        path.cubicTo(14, 3, 7, -4, 0, 4)
        painter.drawPath(path)
        painter.restore()

    def _sparkle(self, painter: QPainter, x: float, y: float, size: float, alpha: int) -> None:
        painter.save()
        painter.translate(x, y)
        painter.scale(size / 10.0, size / 10.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(233, 185, 73, alpha))
        path = QPainterPath()
        path.moveTo(0, -10)
        path.quadTo(2, -2, 10, 0)
        path.quadTo(2, 2, 0, 10)
        path.quadTo(-2, 2, -10, 0)
        path.quadTo(-2, -2, 0, -10)
        painter.drawPath(path)
        painter.restore()

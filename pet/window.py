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
    DRAW_SIZE,
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
from .rig import RigLibrary, Spring
from .win_effects import apply_clean_window

ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "icons" / "pet.ico"


class PetWindow(QWidget):
    clicked = Signal(str)
    double_clicked = Signal()
    drag_started = Signal()
    drag_finished = Signal(float, float)
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
        self._hover_target = 0.0
        self._hover_spring = Spring()
        self._dragging = False
        self._double = False
        self._pending_part = "body"
        self._press_global = QPoint()
        self._drag_offset = QPoint()
        self._moves: deque[tuple[float, QPoint]] = deque()
        self._rig_library = RigLibrary()
        self._rig = self._rig_library.get(self.outfit)
        self._last_paint = time.monotonic()

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

    def step_hover(self, dt: float) -> float:
        self._hover_tilt = self._hover_spring.step(
            dt, self._hover_target, stiffness=60.0, damping=12.0, limit=2.5
        )
        return self._hover_tilt

    def set_outfit(self, outfit: str) -> None:
        self.outfit = outfit
        self._rig = self._rig_library.get(outfit)
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

    def drag_velocity(self) -> tuple[float, float]:
        now = time.monotonic()
        while self._moves and now - self._moves[0][0] > 0.15:
            self._moves.popleft()
        if len(self._moves) < 2:
            return 0.0, 0.0
        t0, p0 = self._moves[0]
        t1, p1 = self._moves[-1]
        dt = max(0.001, t1 - t0)
        return (p1.x() - p0.x()) / dt, (p1.y() - p0.y()) / dt

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
                    self._hover_target = 0.0
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
            self._hover_target = max(
                -2.5, min(2.5, (event.position().x() - WINDOW_WIDTH / 2) / (WINDOW_WIDTH / 2) * 2.5)
            )
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            if self._dragging:
                vx, vy = self.drag_velocity()
                self._dragging = False
                self.setCursor(Qt.ArrowCursor)
                self.drag_finished.emit(vx, vy)
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
        self._hover_target = 0.0
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

        now = time.monotonic()
        dt = max(0.0, min(0.05, now - self._last_paint))
        self._last_paint = now
        rotation = state.tilt + self.step_hover(dt)

        painter.save()
        painter.translate(FEET_X, FEET_Y + state.bob + state.hop)
        painter.rotate(rotation)
        painter.scale(
            state.facing * state.scale * state.squash_x,
            state.scale * state.squash_y,
        )
        if self._rig is not None:
            self._rig.draw(
                painter,
                state,
                now,
                dt,
                lambda target: self._draw_overlays(target, state),
                base_rotation=rotation,
            )
        else:
            pixmap = self.sprites.get(self.outfit, state.frame)
            painter.drawPixmap(
                QRectF(-DRAW_SIZE / 2, -FEET_Y, DRAW_SIZE, DRAW_SIZE),
                pixmap,
                QRectF(0, 0, pixmap.width(), pixmap.height()),
            )
            painter.scale(DISPLAY_SCALE, DISPLAY_SCALE)
            painter.translate(-SPRITE_FEET_X, -SPRITE_FEET_Y)
            self._draw_overlays(painter, state)
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

        if state.note:
            now = time.monotonic()
            painter.setFont(QFont("Microsoft YaHei UI", 13, QFont.Bold))
            for index in range(2):
                phase = (now * 0.35 + index * 0.5) % 1.0
                alpha = int(205 * (1.0 - phase * 0.7))
                painter.setPen(QColor(217, 119, 87, alpha))
                x = 194 + index * 18 + math.sin(now * 1.6 + index * 1.7) * 4
                y = 62 - phase * 34 - index * 3
                painter.drawText(QPointF(x, y), "♪")

    def _draw_overlays(self, painter: QPainter, state: PetState) -> None:
        self._draw_expression(painter, state)
        if state.action == "yawn":
            painter.save()
            painter.setPen(QPen(QColor(150, 80, 55, 230), 2))
            painter.setBrush(QColor(120, 55, 45, 230))
            painter.drawEllipse(QRectF(249, 215, 17, 19))
            painter.setBrush(QColor(230, 150, 140, 230))
            painter.drawEllipse(QRectF(253, 224, 9, 7))
            painter.restore()
        self._draw_prop(painter, state)
        if state.action == "wave":
            painter.save()
            painter.setPen(QPen(QColor(250, 230, 210, 180), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(QRectF(112, 218, 28, 28), 60 * 16, 60 * 16)
            painter.drawArc(QRectF(104, 208, 28, 28), 60 * 16, 60 * 16)
            painter.restore()

    def _hand_anchor(self) -> tuple[float, float]:
        if self._rig is not None:
            return self._rig.hand
        return (150.0, 200.0)

    def _draw_prop(self, painter: QPainter, state: PetState) -> None:
        prop = state.prop
        if not prop:
            return
        now = time.monotonic()
        bob = math.sin(now * 2.3) * 1.5
        outline = QPen(QColor(120, 70, 40, 230), 2.4)
        outline.setCapStyle(Qt.RoundCap)
        painter.save()
        painter.setPen(outline)
        if prop == "drink":
            painter.translate(188, 292 + bob)
            painter.rotate(-8)
            painter.setBrush(QColor(247, 238, 220, 255))
            painter.drawRoundedRect(QRectF(0, 0, 32, 38), 6, 6)
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(QRectF(24, 10, 18, 18), -80 * 16, 200 * 16)
            painter.setPen(QPen(QColor(220, 210, 190, 200), 2))
            painter.drawLine(QPointF(5, 6), QPointF(27, 6))
            painter.setPen(QPen(QColor(250, 250, 250, 180), 2))
            for index in range(2):
                path = QPainterPath()
                path.moveTo(8 + index * 10, -6)
                path.cubicTo(
                    2 + index * 10,
                    -14,
                    14 + index * 10,
                    -18,
                    8 + index * 10,
                    -26,
                )
                painter.drawPath(path)
        elif prop == "eat":
            painter.translate(188, 300 + bob)
            painter.setPen(outline)
            painter.setBrush(QColor(214, 160, 92, 255))
            painter.drawEllipse(QRectF(-16, -16, 32, 32))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(110, 65, 40, 255))
            for dx, dy in ((-6, -5), (5, -3), (0, 6), (-8, 4), (7, 6)):
                painter.drawEllipse(QRectF(dx - 2, dy - 2, 4, 4))
            painter.setPen(outline)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(-16, -16, 32, 32))
        elif prop == "read":
            painter.translate(198, 286 + bob)
            painter.setPen(outline)
            painter.setBrush(QColor(250, 240, 220, 255))
            left = QPainterPath()
            left.moveTo(-34, -10)
            left.lineTo(0, -4)
            left.lineTo(0, 22)
            left.lineTo(-34, 16)
            left.closeSubpath()
            right = QPainterPath()
            right.moveTo(34, -10)
            right.lineTo(0, -4)
            right.lineTo(0, 22)
            right.lineTo(34, 16)
            right.closeSubpath()
            painter.drawPath(left)
            painter.drawPath(right)
            painter.setPen(QPen(QColor(190, 150, 110, 200), 1.5))
            for index in range(3):
                painter.drawLine(
                    QPointF(-28, -4 + index * 5), QPointF(-6, index * 5)
                )
                painter.drawLine(
                    QPointF(6, index * 5), QPointF(28, -4 + index * 5)
                )
            painter.setPen(outline)
            painter.drawLine(QPointF(0, -4), QPointF(0, 22))
        elif prop == "umbrella":
            hand_x, hand_y = self._hand_anchor()
            top_x, top_y = hand_x - 20, 70
            painter.setPen(QPen(QColor(110, 75, 50, 235), 5))
            painter.drawLine(QPointF(hand_x, hand_y - 6), QPointF(top_x + 8, top_y + 16))
            painter.setBrush(Qt.NoBrush)
            handle = QPainterPath()
            handle.moveTo(hand_x, hand_y - 6)
            handle.cubicTo(hand_x - 8, hand_y + 8, hand_x - 18, hand_y + 6, hand_x - 16, hand_y - 4)
            painter.drawPath(handle)
            painter.translate(top_x, top_y)
            painter.setPen(QPen(QColor(120, 60, 50, 235), 3))
            painter.setBrush(QColor(214, 96, 88, 245))
            canopy = QPainterPath()
            canopy.moveTo(-94, 0)
            canopy.cubicTo(-70, -64, 70, -64, 94, 0)
            for index in range(6, 0, -1):
                x = -94 + index * 31.3
                canopy.quadTo(x - 15, 12, x - 31.3, 0)
            canopy.closeSubpath()
            painter.drawPath(canopy)
            painter.setPen(QPen(QColor(160, 60, 55, 200), 2))
            for x in (-62, -31, 0, 31, 62):
                painter.drawLine(QPointF(0, -54), QPointF(x, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(120, 190, 245, 200))
            for dx, dy in ((-80, 24), (60, 30), (90, 10)):
                painter.drawEllipse(QRectF(dx, dy, 5, 9))
        painter.restore()

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
        elif expression == "wink":
            if state.frame == "idle":
                wink = self.sprites.wink_patch(self.outfit)
                if wink is not None:
                    patch, x, y = wink
                    painter.drawImage(QPointF(x, y), patch)
            self._sparkle(painter, 312, 172, 13.0, 220)
        elif expression == "tears":
            self._drop(painter, 232, 232, 11, QColor(120, 200, 255, 230))
            self._drop(painter, 284, 232, 11, QColor(120, 200, 255, 230))
            self._drop(painter, 300, 218, 7, QColor(160, 220, 255, 200))
            pen = QPen(QColor(150, 80, 55, 220), 3)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(252, 240), QPointF(258, 237))
            painter.drawLine(QPointF(258, 237), QPointF(264, 241))
        elif expression == "pout":
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(240, 110, 132, 155))
            painter.drawEllipse(QRectF(193, 209, 42, 20))
            painter.drawEllipse(QRectF(277, 209, 42, 20))
            pen = QPen(QColor(150, 80, 70, 235), 3)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(QColor(206, 116, 108, 235))
            painter.drawEllipse(QRectF(250, 229, 12, 9))
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(QPointF(246, 226), QPointF(242, 224))
            painter.drawLine(QPointF(266, 226), QPointF(270, 224))
        elif expression == "confused":
            painter.save()
            path = QPainterPath()
            path.moveTo(308, 50)
            path.cubicTo(308, 38, 328, 36, 332, 49)
            path.cubicTo(334, 58, 320, 60, 320, 68)
            pen = QPen(QColor(255, 248, 238, 245), 10)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 248, 238, 245))
            painter.drawEllipse(QRectF(314.5, 77, 11, 11))
            pen = QPen(QColor(120, 70, 40, 245), 4.6)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(path)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(120, 70, 40, 245))
            painter.drawEllipse(QRectF(317, 79.5, 6, 6))
            painter.restore()
        elif expression == "shy":
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(240, 110, 132, 165))
            painter.drawEllipse(QRectF(180, 203, 38, 18))
            painter.drawEllipse(QRectF(294, 203, 38, 18))
            pen = QPen(QColor(255, 245, 235, 235), 3.4)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            for side in (-1, 1):
                base_x = 330 if side > 0 else 176
                for index in range(2):
                    offset = index * 13
                    painter.drawLine(
                        QPointF(base_x + side * offset, 154 + offset),
                        QPointF(base_x + side * (offset + 12), 142 + offset),
                    )
        elif expression == "dizzy":
            for x, y in ((215, 200), (288, 199)):
                self._spiral(painter, x, y, 26, QColor(255, 250, 240, 235), width=7.0)
                self._spiral(painter, x, y, 26, QColor(95, 55, 25, 245))
            for index, (x, y) in enumerate(((224, 66), (286, 52), (322, 96))):
                phase = (now * 0.8 + index * 0.3) % 1.0
                alpha = int(230 * (1.0 - phase * 0.5))
                self._sparkle(
                    painter,
                    x,
                    y - phase * 8,
                    15.0,
                    alpha,
                    QColor(255, 250, 240, alpha),
                )
        elif expression == "sweat":
            self._drop(painter, 314, 174, 15, QColor(120, 200, 255, 235))
            self._drop(painter, 300, 192, 8, QColor(160, 220, 255, 210))
            painter.setPen(QPen(QColor(255, 255, 255, 210), 2))
            painter.drawLine(QPointF(310, 168), QPointF(313, 176))
        elif expression == "expect":
            for x in (215, 288):
                self._sparkle(
                    painter,
                    x,
                    200,
                    28.0,
                    235,
                    QColor(255, 250, 240, 240),
                )
                self._sparkle(painter, x, 200, 19.0, 245)
            pen = QPen(QColor(150, 80, 55, 220), 3)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            path = QPainterPath()
            path.moveTo(252, 238)
            path.quadTo(258, 245, 264, 238)
            painter.drawPath(path)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(240, 110, 132, 120))
            painter.drawEllipse(QRectF(196, 212, 30, 15))
            painter.drawEllipse(QRectF(292, 212, 30, 15))

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

    def _sparkle(
        self,
        painter: QPainter,
        x: float,
        y: float,
        size: float,
        alpha: int,
        color: QColor | None = None,
    ) -> None:
        painter.save()
        painter.translate(x, y)
        painter.scale(size / 10.0, size / 10.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color or QColor(233, 185, 73, alpha))
        path = QPainterPath()
        path.moveTo(0, -10)
        path.quadTo(2, -2, 10, 0)
        path.quadTo(2, 2, 0, 10)
        path.quadTo(-2, 2, -10, 0)
        path.quadTo(-2, -2, 0, -10)
        painter.drawPath(path)
        painter.restore()

    def _drop(self, painter: QPainter, x: float, y: float, size: float, color: QColor) -> None:
        painter.save()
        painter.translate(x, y)
        painter.scale(size / 10.0, size / 10.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        path = QPainterPath()
        path.moveTo(0, -10)
        path.cubicTo(7, -1, 8, 6, 0, 9)
        path.cubicTo(-8, 6, -7, -1, 0, -10)
        painter.drawPath(path)
        painter.restore()

    def _spiral(
        self,
        painter: QPainter,
        x: float,
        y: float,
        size: float,
        color: QColor,
        width: float = 2.6,
    ) -> None:
        painter.save()
        painter.translate(x, y)
        painter.scale(size / 20.0, size / 20.0)
        pen = QPen(color, width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        path = QPainterPath()
        for index in range(0, 26):
            angle = index * 0.62
            radius = 0.7 + index * 0.32
            point = QPointF(math.cos(angle) * radius, math.sin(angle) * radius)
            if index == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        painter.drawPath(path)
        painter.restore()

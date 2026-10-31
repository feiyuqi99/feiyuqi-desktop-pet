from __future__ import annotations

import math
from collections import deque

from PySide6.QtCore import QEasingCurve, QObject, QPropertyAnimation, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QAbstractTextDocumentLayout,
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPainterPath,
    QPen,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextOption,
)
from PySide6.QtWidgets import QWidget

from .win_effects import apply_clean_window

BG = "#F0EEE6"
BORDER = "#D97757"
TEXT = "#3D3929"
FONT_FAMILY = "Microsoft YaHei UI"
MAX_TEXT_WIDTH = 236.0
PADDING_X = 12.0
PADDING_Y = 10.0
RADIUS = 12.0
TAIL = 8.0
BORDER_WIDTH = 1.5


class SpeechBubble(QWidget):
    finished = Signal()

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
            | Qt.NoDropShadowWindowHint,
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.NoFocus)

        self._font = QFont(FONT_FAMILY)
        self._font.setPointSizeF(10.5)
        self._metrics = QFontMetricsF(self._font)
        self._doc = QTextDocument(self)
        self._doc.setDefaultFont(self._font)
        self._doc.setDocumentMargin(0.0)
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self._doc.setDefaultTextOption(option)

        self._full_text = ""
        self._visible = 0
        self._hold_ms = 4000
        self._tail_down = True
        self._text_w = 0.0
        self._text_h = 0.0
        self._body_rect = QRectF()
        self._text_rect = QRectF()
        self._fading_out = False

        self._type_timer = QTimer(self)
        self._type_timer.setSingleShot(True)
        self._type_timer.timeout.connect(self._type_tick)
        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.timeout.connect(self._fade_out)

        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self._fade.finished.connect(self._on_fade_finished)

    def show_message(self, text: str, hold_ms: int = 4000) -> None:
        self._type_timer.stop()
        self._hold_timer.stop()
        self._fade.stop()
        self._fading_out = False
        self._full_text = text.strip()
        self._visible = 0
        self._hold_ms = max(1200, hold_ms)
        self._tail_down = True
        self._compute_layout()
        self._recalc_rects()
        self._doc.setPlainText("")
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self._fade.setDuration(180)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.start()
        self._visible = 1
        self._set_visible_text()
        self._type_timer.start(self._interval_for(self._full_text[0]))

    def _compute_layout(self) -> None:
        self._doc.setTextWidth(MAX_TEXT_WIDTH)
        self._doc.setPlainText(self._full_text)
        ideal = self._doc.idealWidth()
        self._text_w = min(MAX_TEXT_WIDTH, max(48.0, ideal))
        self._doc.setTextWidth(self._text_w)
        self._text_h = max(self._metrics.height(), self._doc.size().height())
        width = math.ceil(self._text_w + PADDING_X * 2 + 2)
        height = math.ceil(self._text_h + PADDING_Y * 2 + TAIL + 2)
        self.setFixedSize(width, height)
        self._recalc_rects()

    def _recalc_rects(self) -> None:
        width = self.width()
        height = self.height()
        if self._tail_down:
            self._body_rect = QRectF(1, 1, width - 2, height - TAIL - 2)
            self._text_rect = QRectF(PADDING_X + 1, PADDING_Y + 1, self._text_w, self._text_h)
        else:
            self._body_rect = QRectF(1, TAIL + 1, width - 2, height - TAIL - 2)
            self._text_rect = QRectF(
                PADDING_X + 1, TAIL + PADDING_Y + 1, self._text_w, self._text_h
            )

    def _set_visible_text(self) -> None:
        self._doc.setPlainText(self._full_text[: self._visible])
        cursor = QTextCursor(self._doc)
        cursor.select(QTextCursor.Document)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(TEXT))
        cursor.mergeCharFormat(fmt)
        self.update()

    def _interval_for(self, char: str) -> int:
        if char in "，、；：":
            return 120
        if char in "。！？…":
            return 220
        return 28

    def _type_tick(self) -> None:
        if self._visible >= len(self._full_text):
            self._hold_timer.start(self._hold_ms)
            return
        char = self._full_text[self._visible]
        self._visible += 1
        self._set_visible_text()
        self._type_timer.start(self._interval_for(char))

    def _fade_out(self) -> None:
        self._fading_out = True
        self._fade.stop()
        self._fade.setDuration(220)
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        self._fade.start()

    def _on_fade_finished(self) -> None:
        if not self._fading_out:
            return
        self._fading_out = False
        self.hide()
        self.finished.emit()

    def set_tail_down(self, down: bool) -> None:
        if self._tail_down == down:
            return
        self._tail_down = down
        self._recalc_rects()
        self.update()

    def move_to(self, pet_rect, screen_rect) -> None:
        width = self.width()
        height = self.height()
        margin = 8
        x = pet_rect.center().x() - width // 2
        x = max(screen_rect.left() + margin, min(x, screen_rect.right() - width - margin))

        above = pet_rect.top() + 18 - height
        if above >= screen_rect.top() + margin:
            y = above
            self.set_tail_down(True)
        else:
            y = pet_rect.top() + 304 + 6
            self.set_tail_down(False)
            if y + height > screen_rect.bottom() - margin:
                y = max(screen_rect.top() + margin, pet_rect.top() + 18 - height)
                self.set_tail_down(True)
        self.move(int(x), int(y))

    def hide_now(self) -> None:
        self._type_timer.stop()
        self._hold_timer.stop()
        self._fade.stop()
        self._fading_out = False
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
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setPen(QPen(QColor(BORDER), BORDER_WIDTH))
        painter.setBrush(QColor(BG))

        width = self.width()
        height = self.height()
        cx = width / 2
        if self._tail_down:
            base_y = height - TAIL - 1
            tail = QPainterPath()
            tail.moveTo(cx - 7, base_y)
            tail.lineTo(cx + 7, base_y)
            tail.lineTo(cx, height - 1)
            tail.closeSubpath()
        else:
            base_y = TAIL + 1
            tail = QPainterPath()
            tail.moveTo(cx - 7, base_y)
            tail.lineTo(cx + 7, base_y)
            tail.lineTo(cx, 1)
            tail.closeSubpath()
        painter.drawPath(tail)
        painter.drawRoundedRect(self._body_rect, RADIUS, RADIUS)

        painter.save()
        painter.translate(self._text_rect.topLeft())
        context = QAbstractTextDocumentLayout.PaintContext()
        context.clip = QRectF(0, 0, self._text_w, self._text_h)
        self._doc.documentLayout().draw(painter, context)
        painter.restore()


class BubbleManager(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.bubble = SpeechBubble()
        self.bubble.finished.connect(self._on_finished)
        self._queue: deque[tuple[str, int]] = deque()
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def enqueue(self, text: str, hold_ms: int = 4000, delay_ms: int = 0, priority: bool = False) -> None:
        if delay_ms > 0:
            QTimer.singleShot(delay_ms, lambda: self._enqueue(text, hold_ms, priority))
        else:
            self._enqueue(text, hold_ms, priority)

    def _enqueue(self, text: str, hold_ms: int, priority: bool = False) -> None:
        if priority:
            self._queue.clear()
            self._play(text, hold_ms)
            return
        if self._busy:
            self._queue.append((text, hold_ms))
            return
        self._play(text, hold_ms)

    def _play(self, text: str, hold_ms: int) -> None:
        self._busy = True
        self.bubble.show_message(text, hold_ms)

    def _on_finished(self) -> None:
        self._busy = False
        if self._queue:
            QTimer.singleShot(140, self._next)

    def _next(self) -> None:
        if self._busy or not self._queue:
            return
        text, hold_ms = self._queue.popleft()
        self._play(text, hold_ms)

    def clear_queue(self) -> None:
        self._queue.clear()

    def hide(self) -> None:
        self._queue.clear()
        self._busy = False
        self.bubble.hide_now()

    def follow(self, pet_rect, screen_rect) -> None:
        if self.bubble.isVisible():
            self.bubble.move_to(pet_rect, screen_rect)

from __future__ import annotations

from .core import L, Line
from .companion import COMPANION_LINES
from .daily import COMPLIMENTS, DAILY_LINES, FOLLOWUPS
from .interactions import INTERACTION_LINES
from .system import SYSTEM_LINES

LINES: list[Line] = [
    *INTERACTION_LINES,
    *DAILY_LINES,
    *COMPANION_LINES,
    *SYSTEM_LINES,
]


def lines_for(event: str) -> list[Line]:
    return [line for line in LINES if line.event == event]

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Line:
    text: str
    event: str
    tags: frozenset[str] = frozenset()
    weight: float = 1.0


def L(text: str, event: str, *tags: str, weight: float = 1.0) -> Line:
    return Line(text, event, frozenset(tags), weight)

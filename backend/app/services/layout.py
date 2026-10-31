"""Words and lines: the common structure produced by both PDF text extraction and OCR."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Word:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float
    conf: float | None = None  # OCR confidence 0-100; None for digital text
    page: int = 1

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def height(self) -> float:
        return self.bottom - self.top


@dataclass
class Line:
    words: list[Word]
    page: int
    text: str = field(init=False)

    def __post_init__(self) -> None:
        self.text = " ".join(w.text for w in self.words)

    @property
    def top(self) -> float:
        return min(w.top for w in self.words)

    @property
    def bottom(self) -> float:
        return max(w.bottom for w in self.words)

    @property
    def min_conf(self) -> float | None:
        confs = [w.conf for w in self.words if w.conf is not None]
        return min(confs) if confs else None


def group_lines(words: list[Word], page: int) -> list[Line]:
    if not words:
        return []
    heights = sorted(w.height for w in words)
    tol = max(2.0, 0.6 * heights[len(heights) // 2])
    ordered = sorted(words, key=lambda w: (w.top + w.bottom) / 2)
    groups: list[list[Word]] = []
    cur = [ordered[0]]
    total = (ordered[0].top + ordered[0].bottom) / 2
    for w in ordered[1:]:
        c = (w.top + w.bottom) / 2
        if abs(c - total / len(cur)) <= tol:
            cur.append(w)
            total += c
        else:
            groups.append(cur)
            cur, total = [w], c
    groups.append(cur)
    lines = [Line(sorted(g, key=lambda w: w.x0), page) for g in groups]
    return sorted(lines, key=lambda ln: ln.top)

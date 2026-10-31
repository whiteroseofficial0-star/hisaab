"""Date parsing. Numeric dates are read as DD/MM/YYYY (Indian and most non-US statements)."""
from __future__ import annotations

import re
from datetime import date

_ABBR = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
_FULL = ["january", "february", "march", "april", "may", "june", "july", "august",
         "september", "october", "november", "december"]
MONTHS = {m: i for i, m in enumerate(_ABBR, 1)}
_MONTH_NAMES = set(_ABBR) | set(_FULL) | {"sept"}

_NUM = re.compile(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4}|\d{2})")
_YMD = re.compile(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})")
_NAMED = re.compile(r"(\d{1,2})[\-\s.]*([A-Za-z]{3,9})[\-\s,.]*(\d{4}|\d{2})")

DATE_IN_TEXT = re.compile(
    r"\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2}"
    r"|\d{1,2}[\-\s]+[A-Za-z]{3,9}[\-\s,]+\d{2,4}"
)


def _mk(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def parse_date(text: str) -> date | None:
    s = text.strip().rstrip(",")
    m = _YMD.fullmatch(s)
    if m:
        return _mk(int(m[1]), int(m[2]), int(m[3]))
    m = _NUM.fullmatch(s)
    if m:
        y = int(m[3]) + (2000 if len(m[3]) == 2 else 0)
        return _mk(y, int(m[2]), int(m[1]))
    m = _NAMED.fullmatch(s)
    if m and m[2].lower() in _MONTH_NAMES:
        y = int(m[3]) + (2000 if len(m[3]) == 2 else 0)
        return _mk(y, MONTHS[m[2].lower()[:3]], int(m[1]))
    return None


def take_date(tokens: list[str], i: int) -> tuple[date, int] | None:
    """Try to read a date starting at tokens[i]; returns (date, tokens consumed)."""
    for n in (1, 3):
        chunk = tokens[i:i + n]
        if len(chunk) == n:
            d = parse_date(" ".join(chunk))
            if d:
                return d, n
    return None


def to_iso(d: date | None) -> str | None:
    return d.isoformat() if d else None


def coerce_iso(value) -> str | None:
    """Accept ISO strings or common formats; raise ValueError if not a date."""
    if value in (None, ""):
        return None
    s = str(value).strip()
    d = parse_date(s)
    if d is None:
        raise ValueError(f"Not a valid date: {s[:30]}")
    return d.isoformat()

"""Number parsing helpers. Nothing here guesses: unparseable input returns None or raises."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_BANK_AMT = re.compile(r"^(\()?(-)?(\d[\d,]*)\.(\d{2})(\))?(Cr|Dr)?$", re.I)
_CURRENCY = re.compile(r"^[₹$€£]|^(?:rs\.?|inr|usd|eur|gbp)\s*", re.I)
_LAST_NUMBER = re.compile(r"(?<![\w.])-?\(?\d[\d,]*(?:\.\d+)?\)?(?![\w])")


def parse_bank_amount(text: str) -> tuple[Decimal, bool, str | None] | None:
    """Strict amount token: needs two decimals, e.g. 1,23,456.78 / 500.00Dr / (250.00).

    Returns (absolute value, negative?, 'Cr'|'Dr'|None)."""
    m = _BANK_AMT.match(text.strip())
    if not m:
        return None
    try:
        value = Decimal(m[3].replace(",", "") + "." + m[4])
    except InvalidOperation:
        return None
    negative = bool(m[1] or m[2])
    side = m[6].capitalize() if m[6] else None
    return value, negative, side


def to_float(d: Decimal | None) -> float | None:
    return None if d is None else float(round(d, 2))


def parse_number(text: str | None) -> float | None:
    """Lenient parser for invoice/receipt cells: '1,234.50', '₹ 99', '(12.00)'. None if not numeric."""
    if text is None:
        return None
    s = _CURRENCY.sub("", str(text).strip()).strip()
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")") or s.startswith("-")
    s = s.strip("()-").replace(",", "").strip()
    if not re.fullmatch(r"\d+(?:\.\d+)?", s):
        return None
    v = float(s)
    return -v if neg else v


def last_amount_in(text: str) -> float | None:
    """Last numeric value on a line (prefers decimals), used for 'Total  1,234.00' style lines."""
    decimals = re.findall(r"(?<![\w.])\(?-?\d[\d,]*\.\d{1,2}\)?(?![\w])", text)
    pool = decimals or _LAST_NUMBER.findall(text)
    return parse_number(pool[-1]) if pool else None


def coerce_number(value) -> float | None:
    """For user edits: None/'' -> None; numbers and numeric strings -> float; else ValueError."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("Not a number")
    if isinstance(value, (int, float)):
        return float(value)
    n = parse_number(str(value))
    if n is None:
        raise ValueError(f"Not a valid number: {str(value)[:30]}")
    return n

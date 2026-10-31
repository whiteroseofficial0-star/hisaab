"""Bank statement parsing: transaction rows, metadata and reconciliation checks.

Works on words/lines from either PDF text or OCR. Nothing is guessed: when a debit/credit
direction cannot be established the amount is left unassigned and the row is flagged.
"""
from __future__ import annotations

import re
import uuid
from datetime import date
from decimal import Decimal

from app.core.errors import ExtractionError
from app.services.document_service import PageContent
from app.services.layout import Line, Word
from app.utils.dates import DATE_IN_TEXT, parse_date, take_date, to_iso
from app.utils.numbers import parse_bank_amount, to_float

LOW_CONF = 65.0
TOLERANCE = Decimal("0.01")

FLAG_MESSAGES = {
    "low_ocr_confidence": "OCR was not confident about this row; compare it with the original.",
    "missing_amount": "No debit or credit amount could be assigned; check the source text.",
    "both_debit_credit": "Both debit and credit are filled; normally only one applies.",
    "invalid_date": "Date is missing or not a valid date.",
    "balance_mismatch": "Balance does not equal previous balance + credit - debit.",
    "possible_duplicate": "Another row has the same date, description and amounts.",
}

DEBIT_WORDS = {"debit", "debits", "withdrawal", "withdrawals", "withdrawn", "dr"}
CREDIT_WORDS = {"credit", "credits", "deposit", "deposits", "deposited", "cr"}
SKIP_LINE = re.compile(
    r"page\s*\d+\s*(of|/)\s*\d+|computer[\s-]*generated|statement\s+of\s+account|registered\s+office"
    r"|customer\s+care|toll[\s-]*free|www\.|carried\s+forward|brought\s+forward|end\s+of\s+statement"
    r"|^\s*total\b|opening\s+balance|closing\s+balance",
    re.I,
)
KNOWN_BANKS = [
    "State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank",
    "Punjab National Bank", "Bank of Baroda", "Canara Bank", "Union Bank of India", "IDFC FIRST Bank",
    "Yes Bank", "IndusInd Bank", "Bank of India", "Indian Bank", "Federal Bank",
]


# ---------------------------------------------------------------- tokens and columns
def _tokens(line: Line) -> list[tuple[str, Word]]:
    toks: list[tuple[str, Word]] = []
    for w in line.words:
        t = w.text
        if toks and t.lower().strip(".") in ("cr", "dr") and parse_bank_amount(toks[-1][0]):
            toks[-1] = (toks[-1][0] + t.strip("."), toks[-1][1])
        else:
            toks.append((t, w))
    return toks


def detect_columns(line: Line) -> dict[str, tuple[float, float]] | None:
    lows = [w.text.lower().strip(".:,/") for w in line.words]
    if not any("date" in t or t in ("txn", "tran") for t in lows):
        return None
    if any(parse_bank_amount(w.text) for w in line.words):
        return None
    cols: dict[str, tuple[float, float]] = {}
    for w, t in zip(line.words, lows):
        if t in DEBIT_WORDS and "debit" not in cols:
            cols["debit"] = (w.x0, w.x1)
        elif t in CREDIT_WORDS and "credit" not in cols:
            cols["credit"] = (w.x0, w.x1)
        elif t in ("balance", "bal"):
            cols["balance"] = (w.x0, w.x1)
    return cols if len(cols) >= 2 else None


def _nearest_column(w: Word, cols: dict[str, tuple[float, float]]) -> str:
    def dist(c):
        x0, x1 = c
        return min(abs(w.cx - (x0 + x1) / 2), abs(w.x1 - x1), abs(w.x0 - x0))
    return min(cols, key=lambda k: dist(cols[k]))


# ---------------------------------------------------------------- metadata
def extract_metadata(pages: list[PageContent]) -> dict:
    lines = [ln for pc in pages[:2] for ln in pc.lines]
    text_lines = [ln.text for ln in lines]
    full = "\n".join(text_lines)
    meta: dict = {"bank_name": None, "account_holder": None, "account_number_masked": None,
                  "period_from": None, "period_to": None, "opening_balance": None,
                  "closing_balance": None, "currency": None}
    for bank in KNOWN_BANKS:
        if re.search(re.escape(bank), full, re.I):
            meta["bank_name"] = bank
            break
    if not meta["bank_name"]:
        for t in text_lines[:10]:
            if re.search(r"\bbank\b", t, re.I) and len(t) <= 70:
                meta["bank_name"] = t.strip()
                break
    m = re.search(r"(?:account\s*(?:holder|name)|customer\s*name|name)\s*[:\-]\s*(.{2,60})", full, re.I)
    if m:
        meta["account_holder"] = m[1].split("  ")[0].strip()
    m = re.search(r"(?:a/c|account)\s*(?:no\.?|number|num)?\s*[:\-]?\s*([0-9Xx*\-]{6,})", full, re.I)
    if m:
        digits = re.sub(r"\D", "", m[1])
        meta["account_number_masked"] = "X" * max(len(m[1]) - 4, 4) + digits[-4:] if len(digits) >= 4 else None
    m = re.search(rf"(?:statement\s*period|period|from)\s*[:\-]?\s*({DATE_IN_TEXT.pattern})\s*(?:to|-|–|through)\s*({DATE_IN_TEXT.pattern})",
                  full, re.I)
    if m:
        a, b = parse_date(m[1]), parse_date(m[2])
        meta["period_from"], meta["period_to"] = (to_iso(a) or m[1]), (to_iso(b) or m[2])
    for key, label in (("opening_balance", r"opening\s+balance"), ("closing_balance", r"closing\s+balance")):
        m = re.search(label + r"[^\d\-(]*(\(?-?[\d,]+\.\d{2}\)?)\s*(Cr|Dr)?", full, re.I)
        if m:
            amt = parse_bank_amount(m[1])
            if amt:
                val, neg, _ = amt
                if neg or (m[2] and m[2].lower() == "dr"):
                    val = -val
                meta[key] = to_float(val)
    if re.search(r"₹|\bINR\b|\bRs\.?\b", full):
        meta["currency"] = "INR"
    elif re.search(r"\bUSD\b|\$", full):
        meta["currency"] = "USD"
    elif re.search(r"\bEUR\b|€", full):
        meta["currency"] = "EUR"
    elif re.search(r"\bGBP\b|£", full):
        meta["currency"] = "GBP"
    return meta


# ---------------------------------------------------------------- row parsing
def _new_row(page: int, d: date, vd: date | None, desc: str, amounts, conf, source_text) -> dict:
    return {"page": page, "date": to_iso(d), "value_date": to_iso(vd), "desc": [desc] if desc else [],
            "amounts": list(amounts), "conf": conf, "source": [source_text]}


def _finalize(raw: dict, cols, prev_balance: Decimal | None, currency) -> tuple[dict, Decimal | None]:
    desc = re.sub(r"\s+", " ", " ".join(raw["desc"])).strip()
    debit = credit = balance = None
    amounts = raw["amounts"]  # list of (Decimal, negative, side, Word)
    if amounts:
        assigned: dict[str, tuple] = {}
        if cols:
            for a in amounts:
                assigned.setdefault(_nearest_column(a[3], cols), []).append(a)  # type: ignore[arg-type]
            if all(len(v) == 1 for v in assigned.values()):
                for k, v in assigned.items():
                    val, neg, side, _ = v[0]
                    if k == "balance":
                        balance = -val if (neg or side == "Dr") else val
                    elif k == "debit":
                        debit = val
                    else:
                        credit = val
            else:
                assigned = {}
        if not cols or not assigned:
            vals = [(a[0], a[1], a[2]) for a in amounts]
            if len(vals) >= 3:
                debit, credit = vals[0][0], vals[1][0]
                bal = vals[-1]
                balance = -bal[0] if (bal[1] or bal[2] == "Dr") else bal[0]
            elif len(vals) == 2:
                txn, bal = vals
                balance = -bal[0] if (bal[1] or bal[2] == "Dr") else bal[0]
                if txn[2] == "Cr":
                    credit = txn[0]
                elif txn[2] == "Dr":
                    debit = txn[0]
                elif prev_balance is not None:
                    if abs(prev_balance + txn[0] - balance) <= TOLERANCE:
                        credit = txn[0]
                    elif abs(prev_balance - txn[0] - balance) <= TOLERANCE:
                        debit = txn[0]
            elif len(vals) == 1:
                if vals[0][2] == "Cr":
                    credit = vals[0][0]
                elif vals[0][2] == "Dr":
                    debit = vals[0][0]
        if debit == 0 and credit:
            debit = None
        if credit == 0 and debit:
            credit = None
    reference = None
    long_numbers = re.findall(r"\b\d{9,18}\b", desc)
    if long_numbers:
        reference = long_numbers[-1]  # reference columns sit to the right of the narration
    cheque = None
    m = re.search(r"(?:CHQ|CHEQUE|CHK)[\s.:#NOno]*?(\d{6,9})", desc, re.I)
    if m:
        cheque = m[1]
        if reference == cheque:
            reference = None
    flags = []
    if raw["conf"] is not None and raw["conf"] < LOW_CONF:
        flags.append("low_ocr_confidence")
    row = {
        "id": uuid.uuid4().hex[:10],
        "date": raw["date"], "value_date": raw["value_date"], "description": desc,
        "reference": reference, "cheque_no": cheque,
        "debit": to_float(debit), "credit": to_float(credit), "balance": to_float(balance),
        "currency": currency, "page": raw["page"],
        "source_text": " / ".join(raw["source"])[:500],
        "ocr_confidence": None if raw["conf"] is None else round(raw["conf"], 1),
        "flags": flags,
    }
    return row, (balance if balance is not None else prev_balance)


def parse_transactions(pages: list[PageContent], opening_balance: float | None, currency: str | None):
    rows: list[dict] = []
    warnings: list[str] = []
    cols = None
    prev_balance = Decimal(str(opening_balance)) if opening_balance is not None else None
    current = None
    cont_count = 0
    last_page_with_loose = set()

    def close():
        nonlocal current, prev_balance
        if current is not None:
            row, prev_balance = _finalize(current, cols_at_row[0], prev_balance, currency)
            rows.append(row)
            current = None

    cols_at_row = [None]
    for pc in pages:
        header_seen = False
        prev_bottom = None
        for line in pc.lines:
            if not line.words:
                continue
            hdr = detect_columns(line)
            if hdr:
                cols = hdr
                header_seen = True
                continue
            if SKIP_LINE.search(line.text):
                continue
            toks = _tokens(line)
            texts = [t for t, _ in toks]
            got = take_date(texts, 0)
            na = 0
            while na < 3 and len(toks) - 1 - na >= (got[1] if got else 0) and parse_bank_amount(toks[-1 - na][0]):
                na += 1
            amts = []
            for t, w in toks[len(toks) - na:]:
                p = parse_bank_amount(t)
                amts.append((p[0], p[1], p[2], w))
            if got:
                close()
                d, used = got
                i = used
                vd = None
                second = take_date(texts, i)
                if second and len(toks) - na > i + second[1]:
                    vd, used2 = second
                    i += used2
                mid = texts[i:len(toks) - na]
                if len(mid) > 1 and vd is None:
                    last = take_date(mid, len(mid) - 1)
                    if last:
                        vd = last[0]
                        mid = mid[:-1]
                cols_at_row[0] = cols
                current = _new_row(pc.page, d, vd, " ".join(mid), amts, line.min_conf, line.text)
                cont_count = 0
                prev_bottom = line.bottom
            elif current is not None:
                lh = max(line.bottom - line.top, 1.0)
                if prev_bottom is None:
                    allowed = header_seen
                else:
                    allowed = (line.top - prev_bottom) <= 2.0 * lh
                if not allowed:
                    continue
                mid = texts[:len(toks) - na]
                if amts and not current["amounts"]:
                    current["amounts"] = amts
                    current["desc"].append(" ".join(mid))
                    current["source"].append(line.text)
                elif not amts and cont_count < 4:
                    current["desc"].append(" ".join(texts))
                    current["source"].append(line.text)
                    cont_count += 1
                elif amts:
                    last_page_with_loose.add(pc.page)
                    continue
                else:
                    continue
                if line.min_conf is not None and current["conf"] is not None:
                    current["conf"] = min(current["conf"], line.min_conf)
                prev_bottom = line.bottom
    close()
    for p in sorted(last_page_with_loose):
        warnings.append(f"Page {p}: some lines with amounts but no date were not imported; compare with the original.")
    return rows, warnings


# ---------------------------------------------------------------- validation (also used after user edits)
def validate_transactions(rows: list[dict], metadata: dict) -> tuple[list[dict], list[str], dict]:
    def D(x):
        return Decimal(str(x)) if x is not None else None

    warnings: list[str] = []
    keep = {"low_ocr_confidence"}
    for r in rows:
        r["flags"] = [f for f in r.get("flags", []) if f in keep]
    seen: dict[tuple, list[dict]] = {}
    prev_bal = D(metadata.get("opening_balance"))
    mismatches = 0
    with_bal = 0
    for r in rows:
        if not r.get("date") or parse_date(r["date"]) is None:
            r["flags"].append("invalid_date")
        if r.get("debit") is None and r.get("credit") is None:
            r["flags"].append("missing_amount")
        if r.get("debit") and r.get("credit"):
            r["flags"].append("both_debit_credit")
        bal = D(r.get("balance"))
        if bal is not None:
            with_bal += 1
            if prev_bal is not None:
                expected = prev_bal + (D(r.get("credit")) or 0) - (D(r.get("debit")) or 0)
                if abs(expected - bal) > TOLERANCE:
                    r["flags"].append("balance_mismatch")
                    mismatches += 1
            prev_bal = bal
        key = (r.get("date"), (r.get("description") or "").strip().lower(), r.get("debit"), r.get("credit"))
        seen.setdefault(key, []).append(r)
    for group in seen.values():
        if len(group) > 1:
            for r in group:
                r["flags"].append("possible_duplicate")
    total_debit = sum((D(r.get("debit")) or Decimal(0) for r in rows), Decimal(0))
    total_credit = sum((D(r.get("credit")) or Decimal(0) for r in rows), Decimal(0))
    opening, closing = D(metadata.get("opening_balance")), D(metadata.get("closing_balance"))
    computed = None
    if opening is not None:
        computed = opening + total_credit - total_debit
        if closing is not None and abs(computed - closing) > TOLERANCE:
            warnings.append(
                "Opening balance + credits - debits does not equal the closing balance. "
                "Banks use different conventions (holds, reversals, reverse chronological order), "
                "so check the flagged rows and the original statement.")
    last_bal = next((D(r["balance"]) for r in reversed(rows) if r.get("balance") is not None), None)
    if closing is not None and last_bal is not None and abs(last_bal - closing) > TOLERANCE:
        warnings.append("The last running balance differs from the closing balance shown in the statement header.")
    if mismatches and with_bal and mismatches >= max(3, with_bal // 2):
        warnings.append(
            f"The running balance does not follow row order for {mismatches} of {with_bal} rows. "
            "The statement may be in reverse chronological order, or debit/credit columns were assigned wrongly.")
    summary = {
        "transaction_count": len(rows),
        "total_debit": to_float(total_debit), "total_credit": to_float(total_credit),
        "net": to_float(total_credit - total_debit),
        "opening_balance": metadata.get("opening_balance"), "closing_balance": metadata.get("closing_balance"),
        "computed_closing_balance": to_float(computed) if computed is not None else None,
        "rows_needing_review": sum(1 for r in rows if r["flags"]),
    }
    return rows, warnings, summary


def extract_bank_statement(pages: list[PageContent]) -> dict:
    page_warnings = [pc.warning for pc in pages if pc.warning]
    metadata = extract_metadata(pages)
    rows, parse_warnings = parse_transactions(pages, metadata.get("opening_balance"), metadata.get("currency"))
    if not rows:
        detail = " ".join(page_warnings)
        raise ExtractionError(
            "no_transactions_found",
            "No transaction rows were found. The statement layout may not be supported, or the scan quality is too low. "
            + detail)
    rows, val_warnings, summary = validate_transactions(rows, metadata)
    return {
        "tool": "bank_statement",
        "metadata": metadata,
        "transactions": rows,
        "summary": summary,
        "warnings": page_warnings + parse_warnings + val_warnings,
        "extraction": {"pages": [{"page": pc.page, "method": pc.method} for pc in pages],
                       "ocr_used": any(pc.method == "ocr" and pc.words for pc in pages)},
        "flag_messages": FLAG_MESSAGES,
    }

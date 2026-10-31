"""Validate and re-validate user-edited results (PATCH). Only known fields are accepted."""
from __future__ import annotations

import uuid

from app.core.errors import AppError
from app.services import bank_statement_service as bank
from app.services import invoice_service as inv
from app.services import receipt_service as rec
from app.utils.dates import coerce_iso
from app.utils.numbers import coerce_number

MAX_ROWS = 20000
MAX_TEXT = 1000


def _text(v, field: str) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    if len(s) > MAX_TEXT:
        raise AppError("value_too_long", f"'{field}' is too long.", 422)
    return s or None


def _num(v, field: str):
    try:
        return coerce_number(v)
    except ValueError:
        raise AppError("invalid_number", f"'{field}' must be a number.", 422)


def _date(v, field: str):
    try:
        return coerce_iso(v)
    except ValueError:
        raise AppError("invalid_date", f"'{field}' must be a valid date (DD/MM/YYYY or YYYY-MM-DD).", 422)


def _rows(payload, key) -> list[dict]:
    rows = payload.get(key)
    if not isinstance(rows, list) or len(rows) > MAX_ROWS or not all(isinstance(r, dict) for r in rows):
        raise AppError("invalid_payload", f"'{key}' must be a list of objects.", 422)
    return rows


def _id(r) -> str:
    rid = str(r.get("id") or "")
    return rid[:32] if rid else uuid.uuid4().hex[:10]


def apply_patch(current: dict, payload: dict) -> dict:
    tool = current["tool"]
    result = dict(current)
    if tool == "bank_statement":
        meta = dict(current["metadata"])
        for k, v in (payload.get("metadata") or {}).items():
            if k in meta:
                if k in ("opening_balance", "closing_balance"):
                    meta[k] = _num(v, k)
                elif k in ("period_from", "period_to"):
                    meta[k] = _date(v, k)
                else:
                    meta[k] = _text(v, k)
        old = {r["id"]: r for r in current["transactions"]}
        rows = []
        for r in _rows(payload, "transactions"):
            rid = _id(r)
            prev = old.get(rid, {})
            rows.append({
                "id": rid, "date": _date(r.get("date"), "date"), "value_date": _date(r.get("value_date"), "value_date"),
                "description": _text(r.get("description"), "description") or "",
                "reference": _text(r.get("reference"), "reference"), "cheque_no": _text(r.get("cheque_no"), "cheque_no"),
                "debit": _num(r.get("debit"), "debit"), "credit": _num(r.get("credit"), "credit"),
                "balance": _num(r.get("balance"), "balance"), "currency": _text(r.get("currency"), "currency"),
                "page": int(r["page"]) if isinstance(r.get("page"), (int, float)) else prev.get("page"),
                "source_text": prev.get("source_text", ""), "ocr_confidence": prev.get("ocr_confidence"),
                "flags": prev.get("flags", []),
            })
        rows, warnings, summary = bank.validate_transactions(rows, meta)
        result.update(metadata=meta, transactions=rows, summary=summary,
                      warnings=[w for w in current["warnings"] if w.startswith("Page ")] + warnings)
    elif tool == "invoice":
        raw = payload.get("fields")
        if not isinstance(raw, dict):
            raise AppError("invalid_payload", "'fields' must be an object.", 422)
        fields = {}
        for k in inv.FIELD_KEYS:
            v = raw.get(k)
            fields[k] = (_date(v, k) if k in inv.DATE_FIELDS else _num(v, k) if k in inv.NUMBER_FIELDS else _text(v, k))
        items = []
        for r in _rows(payload, "line_items"):
            it = {"id": _id(r)}
            for k in inv.ITEM_KEYS:
                it[k] = _num(r.get(k), k) if k in inv.ITEM_NUMBERS else _text(r.get(k), k)
            items.append(it)
        w, calc = inv.validate_invoice(fields, items)
        keep = [x for x in current["warnings"] if "inferred from page layout" in x or "order of appearance" in x]
        result.update(fields=fields, line_items=items, calculated=calc, warnings=keep + w)
    elif tool == "receipt":
        receipts = []
        old = {r["id"]: r for r in current["receipts"]}
        items_in = _rows(payload, "line_items")
        items = []
        for r in items_in:
            items.append({"id": _id(r), "receipt_id": _text(r.get("receipt_id"), "receipt_id"),
                          "description": _text(r.get("description"), "description"),
                          "quantity": _num(r.get("quantity"), "quantity"), "unit_price": _num(r.get("unit_price"), "unit_price"),
                          "amount": _num(r.get("amount"), "amount")})
        for r in _rows(payload, "receipts"):
            rid = _id(r)
            prev = old.get(rid, {})
            row = {"id": rid, "source_file": prev.get("source_file") or _text(r.get("source_file"), "source_file"),
                   "ocr_confidence": prev.get("ocr_confidence")}
            for k in rec.RECEIPT_KEYS:
                v = r.get(k)
                row[k] = (_date(v, k) if k == "date" else _num(v, k) if k in ("subtotal", "tax", "discount", "total")
                          else _text(v, k))
            row["flags"] = [f for f in prev.get("flags", []) if f == "low_ocr_confidence"]
            row["flags"] += rec.validate_receipt(row, [i for i in items if i["receipt_id"] == rid])
            receipts.append(row)
        result.update(receipts=receipts, line_items=items)
    elif tool == "tables":
        tables = []
        old = {t["id"]: t for t in current["tables"]}
        for t in _rows(payload, "tables"):
            cols, rows = t.get("columns"), t.get("rows")
            if (not isinstance(cols, list) or not isinstance(rows, list) or len(cols) > 200 or len(rows) > MAX_ROWS
                    or not all(isinstance(r, list) for r in rows)):
                raise AppError("invalid_payload", "Each table needs 'columns' and 'rows'.", 422)
            tid = _id(t)
            tables.append({
                "id": tid, "page": old.get(tid, {}).get("page"), "method": old.get(tid, {}).get("method", "text"),
                "name": _text(t.get("name"), "name") or "Table", "selected": bool(t.get("selected", True)),
                "columns": [(_text(c, "column") or f"Column {i}") for i, c in enumerate(cols, 1)],
                "rows": [[(_text(c, "cell") or "") for c in r][:len(cols)] + [""] * max(0, len(cols) - len(r)) for r in rows],
                "warnings": old.get(tid, {}).get("warnings", []),
            })
        result["tables"] = tables
    return result

"""Receipt / expense bill extraction. One result row per receipt plus optional line items."""
from __future__ import annotations

import re
import uuid

from app.core.errors import ExtractionError
from app.services import ocr_service
from app.services.document_service import PageContent
from app.services.invoice_service import GSTIN_RE, _detect_currency
from app.utils.dates import DATE_IN_TEXT, parse_date, to_iso
from app.utils.numbers import last_amount_in, parse_number

LOW_CONF = 65.0
# An amount token, with or without a currency symbol ("$19.90", "1,234.00", "(5.00)").
NUM_TOKEN = re.compile(r"[\u20b9$€£]?\s?\(?-?[\d,]+(?:\.\d{1,2})?\)?")
# The trailing amount is removed to leave a row's label ("Note: Sub Total: $69.40" -> "note: sub total").
TRAILING_AMOUNT = re.compile(r"\(?[\u20b9$€£]?\s?-?[\d,]+\.\d{1,2}\)?\s*$")
SUMMARY = re.compile(r"^(sub\s*-?\s*total|total|grand\s*total|amount\s*(paid|due|payable)|net\s*(amount|payable)|balance|"
                     r"tax|gst|cgst|sgst|igst|vat|discount|savings|round|change|cash|tendered)\b", re.I)
# Same labels, but anywhere in the text before the amount ("Note: Sub Total:", "Amount Total:").
SUMMARY_LABEL = re.compile(r"sub\s*-?\s*total|subtotal|\b(total|tax|gst|cgst|sgst|igst|vat|discount|savings|rebate|balance|change|cash|tendered|round\s*-?\s*off)\b", re.I)
PAYMENT = [("UPI", r"\bupi\b|gpay|google\s*pay|phonepe|paytm"), ("Card", r"visa|master\s*card|rupay|amex|debit\s*card|credit\s*card|\bcard\b"),
           ("Cash", r"\bcash\b"), ("Net banking", r"net\s*banking|netbanking")]
RECEIPT_KEYS = ["merchant", "receipt_number", "date", "time", "description", "subtotal", "tax", "discount",
                "total", "currency", "payment_method", "tax_id"]
ITEM_KEYS = ["description", "quantity", "unit_price", "amount"]


def _items(lines) -> list[dict]:
    items = []
    for ln in lines:
        t = ln.text.strip()
        # A summary line needs an amount: the table header ("No. Description ... Total") has none.
        if SUMMARY.match(t) or (SUMMARY_LABEL.search(TRAILING_AMOUNT.sub("", t)) and last_amount_in(t) is not None):
            break
        if re.search(r"bill\s*no|receipt|invoice|date|gstin|tel|phone|www|@|^-+$|^=+$", t, re.I):
            continue
        toks = [x for x in t.split() if x not in ("x", "X", "@")]
        nums = []
        while toks and NUM_TOKEN.fullmatch(toks[-1]) and len(nums) < 3:
            nums.insert(0, toks.pop())
        if not nums or not toks or "." not in nums[-1]:
            continue
        # Leading row number ("1 Men's Classic Tee ...") is not part of the description.
        if len(toks) > 1 and toks[0].isdigit() and len(toks[0]) <= 3:
            toks.pop(0)
        vals = [parse_number(n) for n in nums]
        item = {"id": uuid.uuid4().hex[:10], "description": " ".join(toks), "quantity": None, "unit_price": None, "amount": vals[-1]}
        if len(vals) == 3:
            item["quantity"], item["unit_price"] = vals[0], vals[1]
        elif len(vals) == 2:
            if "." not in nums[0]:
                item["quantity"] = vals[0]
            else:
                item["unit_price"] = vals[0]
        items.append(item)
    return items


def validate_receipt(row: dict, items: list[dict]) -> list[str]:
    flags = []
    if row.get("total") is None:
        flags.append("missing_total")
    if not row.get("date"):
        flags.append("missing_date")
    sub, tax, disc, tot = row.get("subtotal"), row.get("tax"), row.get("discount") or 0, row.get("total")
    if None not in (sub, tax, tot) and abs(sub - disc + tax - tot) > 0.01:
        flags.append("totals_mismatch")
    if items and sub is not None and abs(sum(i.get("amount") or 0 for i in items) - sub) > 0.01:
        flags.append("items_do_not_match_subtotal")
    return flags


RECEIPT_FLAG_MESSAGES = {
    "missing_total": "Total amount was not found.",
    "missing_date": "Date was not found.",
    "totals_mismatch": "Subtotal - discount + tax does not equal the total.",
    "items_do_not_match_subtotal": "Line items do not add up to the subtotal.",
    "low_ocr_confidence": "OCR was not confident about part of this receipt; compare it with the original.",
}


def extract_receipt(pages: list[PageContent], source_file: str) -> tuple[dict, list[dict]]:
    lines = [ln for pc in pages for ln in pc.lines]
    if not lines:
        hint = f" {ocr_service.OCR_SETUP_HINT}" if any(pc.ocr_unavailable for pc in pages) else ""
        raise ExtractionError("no_text_found", "No readable text was found in this receipt." + hint)
    text = "\n".join(ln.text for ln in lines)
    rid = uuid.uuid4().hex[:10]
    row = {k: None for k in RECEIPT_KEYS}
    row.update(id=rid, source_file=source_file, flags=[], ocr_confidence=None)
    for ln in lines[:6]:
        t = ln.text.strip()
        if len(re.findall(r"[A-Za-z]", t)) >= 3 and not re.search(r"receipt|invoice|tax|bill|gstin|welcome|date|tel|phone|www|@", t, re.I):
            row["merchant"] = t
            break
    # Needs an explicit marker ("no", "number", "#") so "Receipt Date:" is never read as a number.
    m = re.search(r"(?:bill|receipt|invoice|order|inv)\s*(?:no\.?|number|#)\s*[:#\-]*\s*#?\s*([A-Z0-9][A-Z0-9\-/]*)", text, re.I)
    row["receipt_number"] = m[1] if m else None
    for dm in DATE_IN_TEXT.finditer(text):
        d = parse_date(dm[0])
        if d:
            row["date"] = to_iso(d)
            break
    tm = re.search(r"\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)", text)
    row["time"] = tm[1].strip() if tm else None
    row["currency"] = _detect_currency(text)
    g = GSTIN_RE.search(text)
    if g:
        row["tax_id"] = g[0]
    else:
        m = re.search(r"(?:vat|tin|trn|tax\s*id)\s*(?:no\.?|number)?\s*[:\-]?\s*([A-Z0-9\-]{6,})", text, re.I)
        row["tax_id"] = m[1] if m else None
    low = text.lower()
    for name, rx in PAYMENT:
        if re.search(rx, low):
            row["payment_method"] = name
            break
    tax_lines, total_tax = [], None
    for ln in lines:
        t = ln.text.strip()
        amt = last_amount_in(t)
        if amt is None:
            continue
        # Match the label, not the start of the line: "Note: Sub Total:", "Amount Total:" etc.
        label = TRAILING_AMOUNT.sub("", t).lower()
        if not label.strip(" :$\u20b9"):
            continue
        if re.search(r"sub\s*-?\s*total|subtotal", label):
            row["subtotal"] = amt
        elif re.search(r"total\s*(tax|gst)|tax\s*total", label):
            total_tax = amt
        elif re.search(r"\b(cgst|sgst|igst|gst|vat|tax)\b", label):
            tax_lines.append(amt)
        elif re.search(r"discount|savings|rebate", label):
            row["discount"] = amt
        elif re.search(r"grand\s*total|\btotal\b|amount\s*(paid|due|payable)|net\s*(amount|payable)|balance\s*due", label):
            row["total"] = amt
    row["tax"] = total_tax if total_tax is not None else (round(sum(tax_lines), 2) if tax_lines else None)
    items = _items(lines)
    for it in items:
        it["receipt_id"] = rid
    if items:
        row["description"] = "; ".join(i["description"] for i in items[:3])
    confs = [ln.min_conf for ln in lines if ln.min_conf is not None]
    if confs:
        row["ocr_confidence"] = round(min(confs), 1)
        if row["ocr_confidence"] < LOW_CONF:
            row["flags"].append("low_ocr_confidence")
    row["flags"] += validate_receipt(row, items)
    if row["total"] is None and row["merchant"] is None:
        hint = f" {ocr_service.OCR_SETUP_HINT}" if any(pc.ocr_unavailable for pc in pages) else ""
        raise ExtractionError("no_receipt_fields_found", "Could not find receipt details in this file." + hint)
    return row, items

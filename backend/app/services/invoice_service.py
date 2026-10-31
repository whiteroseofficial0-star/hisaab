"""Invoice field and line-item extraction (generic invoices and Indian GST invoices)."""
from __future__ import annotations

import re
import uuid

from app.core.errors import ExtractionError
from app.services.document_service import PageContent
from app.services.layout import Line
from app.utils.dates import DATE_IN_TEXT, parse_date, to_iso
from app.utils.numbers import last_amount_in, parse_number

LOW_CONF = 65.0
GSTIN_RE = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")

FIELD_KEYS = [
    "supplier_name", "supplier_address", "supplier_tax_id", "customer_name", "customer_address",
    "customer_tax_id", "invoice_number", "invoice_date", "due_date", "po_number", "currency",
    "subtotal", "discount", "taxable_amount", "cgst", "sgst", "igst", "other_taxes",
    "shipping", "round_off", "grand_total", "payment_terms",
]
DATE_FIELDS = {"invoice_date", "due_date"}
TEXT_FIELDS = {"supplier_name", "supplier_address", "supplier_tax_id", "customer_name", "customer_address",
               "customer_tax_id", "invoice_number", "po_number", "currency", "payment_terms"}
NUMBER_FIELDS = set(FIELD_KEYS) - DATE_FIELDS - TEXT_FIELDS
ITEM_KEYS = ["description", "hsn_sac", "quantity", "unit", "unit_price", "discount", "tax_rate", "tax_amount", "line_total"]
ITEM_NUMBERS = {"quantity", "unit_price", "discount", "tax_rate", "tax_amount", "line_total"}

_HEADER_RULES = [
    ("hsn_sac", r"hsn|sac"),
    ("tax_amount", r"(tax|gst|cgst|sgst|igst)\s*(amt|amount)"),
    ("tax_rate", r"(tax|gst|cgst|sgst|igst).*(%|rate)|^%$"),
    ("discount", r"disc"),
    ("unit_price", r"unit\s*price|rate|price|unit\s*cost"),
    ("quantity", r"\bqty\b|quantity"),
    ("unit", r"\bunit\b|uom"),
    ("description", r"desc|item|particular|product|detail|service"),
    ("line_total", r"amount|total|value"),
]
TOTAL_LABELS = [  # order matters: first match wins
    ("subtotal", r"^(?:sub\s*-?\s*total|total\s*before\s*tax)"),
    ("taxable_amount", r"^taxable\s*(?:value|amount)"),
    ("discount", r"^(?:total\s*)?discount"),
    ("cgst", r"^cgst"),
    ("sgst", r"^sgst"),
    ("igst", r"^igst"),
    ("other_taxes", r"^(?:cess|vat|other\s*tax)"),
    ("shipping", r"^(?:shipping|freight|delivery|packing|handling)"),
    ("round_off", r"^round(?:ing)?[\s\-]*off"),
    ("grand_total", r"^(?:grand\s*total|invoice\s*total|total\s*amount|amount\s*(?:due|payable)|net\s*payable|balance\s*due|total)\b"),
]
NOT_GRAND = re.compile(r"^total\s*(?:tax|gst|qty|quantity|in\s*words|discount|before)", re.I)


def _new_id() -> str:
    return uuid.uuid4().hex[:10]


def _find(lines: list[Line], pattern: str, value: str, skip_prefix: str | None = None):
    rx = re.compile(rf"(?:{pattern})\s*[:#\-]?\s*({value})", re.I)
    for ln in lines:
        for m in rx.finditer(ln.text):
            if skip_prefix and ln.text[max(0, m.start() - len(skip_prefix) - 1):m.start()].lower().strip().endswith(skip_prefix):
                continue
            return m.group(1).strip(), ln
    return None, None


def _detect_currency(text: str) -> str | None:
    if re.search(r"₹|\bINR\b|\bRs\.?\s*\d", text):
        return "INR"
    if re.search(r"\$|\bUSD\b", text):
        return "USD"
    if re.search(r"€|\bEUR\b", text):
        return "EUR"
    if re.search(r"£|\bGBP\b", text):
        return "GBP"
    return None


def _block_after(lines: list[Line], label_rx: str, limit: int = 4) -> list[str]:
    for i, ln in enumerate(lines):
        if re.match(label_rx, ln.text.strip(), re.I):
            out = []
            inline = re.sub(label_rx, "", ln.text.strip(), flags=re.I).strip(" :-")
            if inline:
                out.append(inline)
            for nxt in lines[i + 1:i + 1 + limit]:
                if GSTIN_RE.search(nxt.text) or re.match(r"(gstin|invoice|date|no\b|#|sl|description)", nxt.text.strip(), re.I):
                    break
                out.append(nxt.text.strip())
            return out
    return []


def _parse_header(row: list[str]) -> dict[int, str] | None:
    mapping: dict[int, str] = {}
    for i, cell in enumerate(row):
        c = (cell or "").lower().strip()
        for key, rx in _HEADER_RULES:
            if re.search(rx, c) and key not in mapping.values():
                mapping[i] = key
                break
    return mapping if "description" in mapping.values() and len(mapping) >= 3 else None


def _items_from_tables(pages: list[PageContent]) -> list[dict]:
    items: list[dict] = []
    for pc in pages:
        for table in pc.tables:
            for hi, row in enumerate(table):
                mapping = _parse_header(row)
                if not mapping:
                    continue
                for r in table[hi + 1:]:
                    desc_i = next(i for i, k in mapping.items() if k == "description")
                    desc = (r[desc_i] if desc_i < len(r) else "").strip()
                    if not desc or re.match(r"(sub\s*)?total|grand", desc, re.I):
                        continue
                    item = {k: None for k in ITEM_KEYS}
                    for i, k in mapping.items():
                        if i < len(r):
                            v = r[i].strip()
                            item[k] = parse_number(v) if k in ITEM_NUMBERS else (v or None)
                    item["description"] = desc
                    item["id"] = _new_id()
                    items.append(item)
                break
    return items


def _items_from_lines(lines: list[Line]) -> list[dict]:
    start = next((i for i, ln in enumerate(lines)
                  if re.search(r"description|item|particulars", ln.text, re.I)
                  and re.search(r"qty|quantity|amount|rate|price", ln.text, re.I)), None)
    if start is None:
        return []
    items = []
    for ln in lines[start + 1:]:
        if re.match(r"(sub\s*total|total|grand|taxable|cgst|sgst|igst)", ln.text.strip(), re.I):
            break
        toks = ln.text.split()
        nums = []
        while toks and re.fullmatch(r"[\d,]+(?:\.\d+)?", toks[-1]) and len(nums) < 3:
            nums.insert(0, toks.pop())
        if len(nums) < 2 or not toks:
            continue
        if re.fullmatch(r"\d{1,3}[.)]?", toks[0]) and len(toks) > 1:
            toks = toks[1:]
        hsn = None
        if len(toks) > 1 and re.fullmatch(r"\d{4,8}", toks[-1]):
            hsn = toks.pop()
        item = {k: None for k in ITEM_KEYS}
        item.update(description=" ".join(toks), hsn_sac=hsn, id=_new_id())
        vals = [parse_number(n) for n in nums]
        if len(vals) == 3:
            item["quantity"], item["unit_price"], item["line_total"] = vals
        else:
            item["unit_price"], item["line_total"] = vals
        items.append(item)
    return items


def validate_invoice(fields: dict, items: list[dict]) -> tuple[list[str], dict]:
    warnings: list[str] = []
    for key, label in (("invoice_number", "invoice number"), ("invoice_date", "invoice date"), ("grand_total", "grand total")):
        if fields.get(key) in (None, ""):
            warnings.append(f"The {label} was not found; please fill it in.")
    line_sum = round(sum((i.get("line_total") or 0) for i in items), 2) if items else None
    f = lambda k: fields.get(k) or 0  # noqa: E731
    subtotal = fields.get("subtotal")
    if line_sum is not None and subtotal is not None and abs(line_sum - subtotal) > 0.01:
        warnings.append(f"Line item totals add up to {line_sum:,.2f} but the subtotal is {subtotal:,.2f}.")
    base = fields.get("taxable_amount")
    if base is None and subtotal is not None:
        base = subtotal - f("discount")
    computed = None
    if base is not None:
        computed = round(base + f("cgst") + f("sgst") + f("igst") + f("other_taxes") + f("shipping") + f("round_off"), 2)
        gt = fields.get("grand_total")
        if gt is not None and abs(computed - gt) > 0.01:
            warnings.append(
                f"Subtotal, taxes and charges add up to {computed:,.2f} but the grand total is {gt:,.2f}. "
                "Check each amount against the original (some invoices list tax-inclusive prices).")
    for it in items:
        q, p, t = it.get("quantity"), it.get("unit_price"), it.get("line_total")
        if None not in (q, p, t) and it.get("tax_amount") is None and it.get("discount") is None and abs(q * p - t) > 0.01:
            warnings.append(f"Line '{(it.get('description') or '')[:30]}': quantity x price is not equal to the line total.")
    return warnings, {"line_items_total": line_sum, "computed_grand_total": computed}


def extract_invoice(pages: list[PageContent]) -> dict:
    lines = [ln for pc in pages for ln in pc.lines]
    text = "\n".join(ln.text for ln in lines)
    fields: dict = {k: None for k in FIELD_KEYS}
    conf: dict[str, float] = {}
    warnings: list[str] = [pc.warning for pc in pages if pc.warning]

    def put(key, val, ln=None):
        if val not in (None, ""):
            fields[key] = val
            if ln is not None and ln.min_conf is not None:
                conf[key] = round(ln.min_conf, 1)

    val, ln = _find(lines, r"invoice\s*(?:no\.?|number|num|#)|bill\s*no\.?", r"[A-Z0-9][A-Z0-9\-/]{2,}")
    put("invoice_number", val, ln)
    for key, label, skip in (("invoice_date", r"invoice\s*date|date\s*of\s*issue|inv\.?\s*date|date", "due"),
                             ("due_date", r"due\s*date|payment\s*due|due\s*on", None)):
        val, ln = _find(lines, label, DATE_IN_TEXT.pattern, skip)
        if val:
            d = parse_date(val)
            put(key, to_iso(d) if d else val, ln)
    val, ln = _find(lines, r"p\.?o\.?\s*(?:no\.?|number|#)|purchase\s*order(?:\s*(?:no\.?|number|#))?", r"[A-Z0-9][A-Z0-9\-/]+")
    put("po_number", val, ln)
    val, ln = _find(lines, r"payment\s*terms?|terms", r".+")
    put("payment_terms", val, ln)
    put("currency", _detect_currency(text))

    gstins = [(m.group(0), m.start()) for m in GSTIN_RE.finditer(text)]
    cust_pos = next((m.start() for m in re.finditer(r"bill(?:ed)?\s*to|customer|buyer|sold\s*to", text, re.I)), None)
    for g, pos in gstins:
        if cust_pos is not None and pos > cust_pos and not fields["customer_tax_id"]:
            fields["customer_tax_id"] = g
        elif not fields["supplier_tax_id"] and (cust_pos is None or pos < cust_pos):
            fields["supplier_tax_id"] = g
    if gstins and cust_pos is None and len(gstins) > 1:
        fields["customer_tax_id"] = gstins[1][0]
        warnings.append("Supplier and customer tax IDs were assigned by order of appearance; please verify.")
    if not fields["supplier_tax_id"]:
        val, ln = _find(lines, r"(?:vat|tin|trn|ein|tax\s*id)\s*(?:no\.?|number)?", r"[A-Z0-9\-]{6,}")
        put("supplier_tax_id", val, ln)

    cust = _block_after(lines, r"(bill(?:ed)?\s*to|customer|buyer|sold\s*to)\s*:?")
    if cust:
        fields["customer_name"] = cust[0]
        fields["customer_address"] = ", ".join(cust[1:]) or None
    head: list[str] = []
    for ln in lines[:8]:
        t = ln.text.strip()
        if re.search(r"invoice|gstin|date|bill\s*to|p\.?o\.?\b|tax\s*id", t, re.I):
            if head:
                break
            continue
        head.append(t)
    if head:
        fields["supplier_name"] = head[0]
        fields["supplier_address"] = ", ".join(head[1:3]) or None
    if fields["supplier_name"] or fields["customer_name"]:
        warnings.append("Supplier and customer names/addresses are inferred from page layout; please verify.")

    seen: dict[str, tuple[float, Line]] = {}
    for ln in lines:
        t = ln.text.strip()
        low = t.lower()
        for key, rx in TOTAL_LABELS:
            if re.match(rx, low):
                if key == "grand_total" and NOT_GRAND.match(low):
                    break
                amt = last_amount_in(t)
                if amt is not None:
                    seen[key] = (amt, ln)
                break
    for key, (amt, ln) in seen.items():
        put(key, amt, ln)

    items = _items_from_tables(pages) or _items_from_lines(lines)
    if not items:
        warnings.append("No line items were detected; add them manually if the invoice has them.")
    found = [k for k, v in fields.items() if v not in (None, "") and k != "currency"]
    if len(found) < 2 and not items:
        raise ExtractionError(
            "no_invoice_fields_found",
            "Could not find invoice details in this document. It may not be an invoice, or the scan quality is too low.")
    w, calc = validate_invoice(fields, items)
    return {
        "tool": "invoice", "fields": fields, "line_items": items, "calculated": calc,
        "warnings": warnings + w, "field_confidence": conf, "low_confidence_threshold": LOW_CONF,
        "extraction": {"pages": [{"page": pc.page, "method": pc.method} for pc in pages]},
    }

"""Excel and CSV generation from the user's *edited* result. All document text is untrusted."""
from __future__ import annotations

import csv
import io
import re
import zipfile
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.core.errors import AppError
from app.utils.dates import parse_date

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
CSV_MIME = "text/csv; charset=utf-8"
ZIP_MIME = "application/zip"
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
HEADER_FILL = PatternFill("solid", fgColor="4F46E5")
NUM_FMT = "#,##0.00"
DATE_FMT = "dd/mm/yyyy"


def clean_text(v) -> str:
    return _CTRL.sub("", str(v))


def csv_safe(v) -> str:
    """Neutralise spreadsheet formula injection: prefix risky leading characters with an apostrophe."""
    s = clean_text(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s


def _csv_cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return f"{v:.2f}"
    if isinstance(v, int):
        return str(v)
    return csv_safe(v)


def _csv_bytes(headers: list[str], rows: list[list], bom: bool) -> bytes:
    buf = io.StringIO(newline="")
    w = csv.writer(buf, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    w.writerow([csv_safe(h) for h in headers])
    for r in rows:
        w.writerow([_csv_cell(v) for v in r])
    data = buf.getvalue().encode("utf-8")
    return (b"\xef\xbb\xbf" + data) if bom else data


def _set(ws, row: int, col: int, value, kind: str = "text"):
    """Write one cell with a real type. Strings are forced to text so '=...' is never a formula."""
    c = ws.cell(row=row, column=col)
    if value is None or value == "":
        return c
    if kind == "date":
        d = value if isinstance(value, date) else parse_date(str(value))
        if d:
            c.value = d
            c.number_format = DATE_FMT
            return c
    elif kind == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
        c.value = float(value)
        c.number_format = NUM_FMT
        return c
    elif kind == "int" and isinstance(value, (int, float)) and not isinstance(value, bool):
        c.value = int(value)
        c.number_format = "0"
        return c
    c.value = clean_text(value)
    c.data_type = "s"
    return c


def _style_header(ws, ncols: int):
    for i in range(1, ncols + 1):
        c = ws.cell(row=1, column=i)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEADER_FILL
        c.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"


def _widths(ws, ncols: int, minimum=10, maximum=60):
    for i in range(1, ncols + 1):
        longest = max((len(str(c.value)) for c in ws[get_column_letter(i)] if c.value is not None), default=0)
        ws.column_dimensions[get_column_letter(i)].width = max(minimum, min(maximum, longest + 2))


def _table_sheet(ws, columns, rows, add_totals=()):
    """columns: [(header, key_or_index, kind)]; rows: list of dict/list. Totals via SUM formulas."""
    for ci, (h, _, _) in enumerate(columns, 1):
        _set(ws, 1, ci, h)
    for ri, row in enumerate(rows, 2):
        for ci, (_, key, kind) in enumerate(columns, 1):
            v = row[key] if not isinstance(key, str) or isinstance(row, dict) else None
            _set(ws, ri, ci, v, kind)
    n = len(rows)
    _style_header(ws, len(columns))
    if n:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{n + 1}"
    if add_totals and n:
        tr = n + 3
        ws.cell(row=tr, column=1, value="Total").font = Font(bold=True)
        for ci, (h, _, kind) in enumerate(columns, 1):
            if h in add_totals:
                L = get_column_letter(ci)
                c = ws.cell(row=tr, column=ci, value=f"=SUM({L}2:{L}{n + 1})")
                c.number_format = NUM_FMT
                c.font = Font(bold=True)
    _widths(ws, len(columns))


def _wb_bytes(wb: Workbook) -> bytes:
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def _zip(files: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return out.getvalue()


# ------------------------------------------------------------------ bank statement
BANK_COLS = [("Transaction Date", "date", "date"), ("Value Date", "value_date", "date"),
             ("Description", "description", "text"), ("Reference No.", "reference", "text"),
             ("Cheque No.", "cheque_no", "text"), ("Debit", "debit", "number"), ("Credit", "credit", "number"),
             ("Balance", "balance", "number"), ("Currency", "currency", "text"), ("Page", "page", "int"),
             ("Review Flags", "flags_text", "text")]


def _bank_rows(result):
    msgs = result.get("flag_messages", {})
    rows = []
    for r in result["transactions"]:
        r = dict(r)
        r["flags_text"] = "; ".join(msgs.get(f, f) for f in r.get("flags", []))
        rows.append(r)
    return rows


def _export_bank(result, fmt, part, bom):
    rows = _bank_rows(result)
    if fmt == "csv":
        cols = [c for c in BANK_COLS if c[1] != "flags_text"]
        return _csv_bytes([c[0] for c in cols], [[r.get(c[1]) for c in cols] for r in rows], bom), "hisaab-bank-statement.csv", CSV_MIME
    wb = Workbook()
    ws = wb.active
    ws.title = "Transactions"
    _table_sheet(ws, BANK_COLS, rows, add_totals=("Debit", "Credit"))
    meta, summ = result.get("metadata", {}), result.get("summary", {})
    sh = wb.create_sheet("Summary")
    n = len(rows)
    lines = [("Bank", meta.get("bank_name"), "text"), ("Account holder", meta.get("account_holder"), "text"),
             ("Account number (masked)", meta.get("account_number_masked"), "text"),
             ("Statement period from", meta.get("period_from"), "date"), ("Statement period to", meta.get("period_to"), "date"),
             ("Opening balance", meta.get("opening_balance"), "number"), ("Closing balance (per statement)", meta.get("closing_balance"), "number"),
             ("Currency", meta.get("currency"), "text")]
    sh.cell(row=1, column=1, value="Field")
    sh.cell(row=1, column=2, value="Value")
    r = 2
    for label, val, kind in lines:
        _set(sh, r, 1, label)
        _set(sh, r, 2, val, kind)
        r += 1
    if n:
        for label, formula in (("Transactions", f"=COUNTA(Transactions!C2:C{n + 1})"),
                               ("Total debit", f"=SUM(Transactions!F2:F{n + 1})"),
                               ("Total credit", f"=SUM(Transactions!G2:G{n + 1})")):
            _set(sh, r, 1, label)
            c = sh.cell(row=r, column=2, value=formula)
            c.number_format = NUM_FMT if "Total" in label else "0"
            r += 1
    _set(sh, r + 1, 1, "Note")
    _set(sh, r + 1, 2, "Reconciliation conventions differ between banks. Totals reflect the reviewed table.")
    _style_header(sh, 2)
    _widths(sh, 2)
    return _wb_bytes(wb), "hisaab-bank-statement.xlsx", XLSX_MIME


# ------------------------------------------------------------------ invoice
FIELD_LABELS = [
    ("Supplier name", "supplier_name", "text"), ("Supplier address", "supplier_address", "text"),
    ("Supplier GSTIN / tax ID", "supplier_tax_id", "text"), ("Customer name", "customer_name", "text"),
    ("Customer address", "customer_address", "text"), ("Customer GSTIN / tax ID", "customer_tax_id", "text"),
    ("Invoice number", "invoice_number", "text"), ("Invoice date", "invoice_date", "date"),
    ("Due date", "due_date", "date"), ("PO number", "po_number", "text"), ("Currency", "currency", "text"),
    ("Subtotal", "subtotal", "number"), ("Discount", "discount", "number"), ("Taxable amount", "taxable_amount", "number"),
    ("CGST", "cgst", "number"), ("SGST", "sgst", "number"), ("IGST", "igst", "number"),
    ("Other taxes", "other_taxes", "number"), ("Shipping / additional charges", "shipping", "number"),
    ("Round-off", "round_off", "number"), ("Grand total", "grand_total", "number"), ("Payment terms", "payment_terms", "text"),
]
ITEM_COLS = [("Description", "description", "text"), ("HSN/SAC", "hsn_sac", "text"), ("Quantity", "quantity", "number"),
             ("Unit", "unit", "text"), ("Unit price", "unit_price", "number"), ("Discount", "discount", "number"),
             ("Tax rate (%)", "tax_rate", "number"), ("Tax amount", "tax_amount", "number"), ("Line total", "line_total", "number")]


def _export_invoice(result, fmt, part, bom):
    f, items = result["fields"], result["line_items"]
    detail_rows = [[label, f.get(key)] for label, key, _ in FIELD_LABELS]
    if fmt in ("csv", "zip"):
        d = _csv_bytes(["Field", "Value"], detail_rows, bom)
        li = _csv_bytes([c[0] for c in ITEM_COLS], [[i.get(c[1]) for c in ITEM_COLS] for i in items], bom)
        if fmt == "zip":
            return _zip({"invoice_details.csv": d, "invoice_line_items.csv": li}), "hisaab-invoice-csv.zip", ZIP_MIME
        if part == "line_items":
            return li, "hisaab-invoice-line-items.csv", CSV_MIME
        if part == "details":
            return d, "hisaab-invoice-details.csv", CSV_MIME
        raise AppError("part_required", "Invoice CSV has two files. Choose 'details' or 'line_items', or download the ZIP.", 400)
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoice Details"
    _set(ws, 1, 1, "Field")
    _set(ws, 1, 2, "Value")
    for ri, (label, key, kind) in enumerate(FIELD_LABELS, 2):
        _set(ws, ri, 1, label)
        _set(ws, ri, 2, f.get(key), kind)
    _style_header(ws, 2)
    _widths(ws, 2)
    wl = wb.create_sheet("Line Items")
    _table_sheet(wl, ITEM_COLS, items, add_totals=("Line total",))
    sh = wb.create_sheet("Summary")
    n = len(items)
    rows = [("Sum of line totals", f"=SUM('Line Items'!I2:I{n + 1})" if n else None),
            ("Subtotal (per invoice)", f.get("subtotal")),
            ("Grand total (per invoice)", f.get("grand_total"))]
    _set(sh, 1, 1, "Check")
    _set(sh, 1, 2, "Amount")
    for ri, (label, v) in enumerate(rows, 2):
        _set(sh, ri, 1, label)
        if isinstance(v, str):
            c = sh.cell(row=ri, column=2, value=v)
            c.number_format = NUM_FMT
        else:
            _set(sh, ri, 2, v, "number")
    for wi, wmsg in enumerate(result.get("warnings", []), len(rows) + 3):
        _set(sh, wi, 1, "Warning")
        _set(sh, wi, 2, wmsg)
    _style_header(sh, 2)
    _widths(sh, 2)
    return _wb_bytes(wb), "hisaab-invoice.xlsx", XLSX_MIME


# ------------------------------------------------------------------ receipts
RECEIPT_COLS = [("Merchant", "merchant", "text"), ("Receipt number", "receipt_number", "text"), ("Date", "date", "date"),
                ("Time", "time", "text"), ("Description", "description", "text"), ("Subtotal", "subtotal", "number"),
                ("Tax", "tax", "number"), ("Discount", "discount", "number"), ("Total", "total", "number"),
                ("Currency", "currency", "text"), ("Payment method", "payment_method", "text"),
                ("Tax ID", "tax_id", "text"), ("Source file", "source_file", "text")]
RITEM_COLS = [("Receipt", "receipt_label", "text"), ("Description", "description", "text"),
              ("Quantity", "quantity", "number"), ("Unit price", "unit_price", "number"), ("Amount", "amount", "number")]


def _export_receipts(result, fmt, part, bom):
    receipts, items = result["receipts"], result.get("line_items", [])
    label = {r["id"]: f'{r.get("merchant") or r.get("source_file") or ""} {r.get("date") or ""}'.strip() for r in receipts}
    items = [{**i, "receipt_label": label.get(i.get("receipt_id"), "")} for i in items]
    if fmt in ("csv", "zip"):
        a = _csv_bytes([c[0] for c in RECEIPT_COLS], [[r.get(c[1]) for c in RECEIPT_COLS] for r in receipts], bom)
        b = _csv_bytes([c[0] for c in RITEM_COLS], [[i.get(c[1]) for c in RITEM_COLS] for i in items], bom)
        if fmt == "zip":
            return _zip({"receipts.csv": a, "receipt_line_items.csv": b}), "hisaab-receipts-csv.zip", ZIP_MIME
        if part == "line_items":
            return b, "hisaab-receipt-line-items.csv", CSV_MIME
        return a, "hisaab-receipts.csv", CSV_MIME
    wb = Workbook()
    ws = wb.active
    ws.title = "Receipts"
    _table_sheet(ws, RECEIPT_COLS, receipts, add_totals=("Subtotal", "Tax", "Discount", "Total"))
    wl = wb.create_sheet("Line Items")
    _table_sheet(wl, RITEM_COLS, items)
    return _wb_bytes(wb), "hisaab-receipts.xlsx", XLSX_MIME


# ------------------------------------------------------------------ tables
_PLAIN_NUM = re.compile(r"^-?\d{1,3}(,\d{2,3})+(\.\d+)?$|^-?\d+\.\d+$|^-?[1-9]\d{0,8}$|^0$")


def _table_value(s):
    """Convert numeric-looking text to numbers; keep IDs with leading zeros, long digit strings and everything else as text."""
    s = (s or "").strip()
    if _PLAIN_NUM.match(s):
        return float(s.replace(",", ""))
    return s


def _sheet_name(name: str, used: set[str]) -> str:
    base = re.sub(r"[\[\]\*\?/\\:]", "-", clean_text(name)).strip() or "Table"
    base = base[:28]
    cand, i = base, 2
    while cand.lower() in used:
        cand = f"{base[:25]}-{i}"
        i += 1
    used.add(cand.lower())
    return cand


def _export_tables(result, fmt, part, bom):
    selected = [t for t in result["tables"] if t.get("selected")]
    if not selected:
        raise AppError("no_table_selected", "Select at least one table to export.", 400)
    if fmt == "xlsx":
        wb = Workbook()
        wb.remove(wb.active)
        used: set[str] = set()
        for t in selected:
            ws = wb.create_sheet(_sheet_name(t["name"], used))
            for ci, h in enumerate(t["columns"], 1):
                _set(ws, 1, ci, h)
            for ri, row in enumerate(t["rows"], 2):
                for ci, v in enumerate(row, 1):
                    val = _table_value(v)
                    _set(ws, ri, ci, val, "number" if isinstance(val, float) else "text")
            _style_header(ws, len(t["columns"]))
            if t["rows"]:
                ws.auto_filter.ref = f"A1:{get_column_letter(len(t['columns']))}{len(t['rows']) + 1}"
            _widths(ws, len(t["columns"]))
        return _wb_bytes(wb), "hisaab-tables.xlsx", XLSX_MIME
    files = {}
    used: set[str] = set()
    for t in selected:
        name = _sheet_name(t["name"], used).replace(" ", "_") + ".csv"
        files[name] = _csv_bytes(t["columns"], t["rows"], bom)
    if fmt == "zip" or len(files) > 1:
        if fmt == "csv":
            raise AppError("zip_required", "Several tables are selected. Download the ZIP or Excel file instead.", 400)
        return _zip(files), "hisaab-tables-csv.zip", ZIP_MIME
    return next(iter(files.values())), "hisaab-table.csv", CSV_MIME


def export_result(result: dict, fmt: str, part: str | None = None, bom: bool = True) -> tuple[bytes, str, str]:
    if fmt not in ("xlsx", "csv", "zip"):
        raise AppError("bad_format", "Format must be xlsx, csv or zip.", 400)
    tool = result.get("tool")
    fn = {"bank_statement": _export_bank, "invoice": _export_invoice,
          "receipt": _export_receipts, "tables": _export_tables}.get(tool)
    if fn is None:
        raise AppError("bad_result", "Nothing to export.", 400)
    if tool == "bank_statement" and fmt == "zip":
        raise AppError("bad_format", "Bank statements export as xlsx or csv.", 400)
    return fn(result, fmt, part, bom)

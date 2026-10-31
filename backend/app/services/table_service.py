"""General table extraction from PDFs (selectable tables via pdfplumber; OCR pages are best-effort)."""
from __future__ import annotations

import uuid

from app.core.errors import ExtractionError
from app.services.document_service import PageContent


def _dedupe_headers(cells: list[str]) -> list[str]:
    out, seen = [], {}
    for i, c in enumerate(cells, 1):
        name = (c or "").strip() or f"Column {i}"
        n = seen.get(name, 0)
        seen[name] = n + 1
        out.append(name if n == 0 else f"{name} ({n + 1})")
    return out


def extract_tables(pages: list[PageContent]) -> dict:
    tables = []
    warnings = [pc.warning for pc in pages if pc.warning]
    for pc in pages:
        for ti, t in enumerate(pc.tables, 1):
            width = max(len(r) for r in t)
            rows = [(r + [""] * (width - len(r))) for r in t]
            tw = []
            if pc.method == "ocr":
                tw.append("Detected from OCR text by column spacing; columns and merged cells may be wrong.")
            tables.append({
                "id": uuid.uuid4().hex[:10], "page": pc.page, "method": pc.method,
                "name": f"Page {pc.page} - Table {ti}", "columns": _dedupe_headers(rows[0]),
                "rows": rows[1:], "selected": True, "warnings": tw,
            })
    if not tables:
        raise ExtractionError(
            "no_tables_found",
            "No tables were detected. Tables without clear lines or columns, or low-quality scans, may not be recognised. "
            + " ".join(warnings))
    return {"tool": "tables", "tables": tables, "warnings": warnings,
            "extraction": {"pages": [{"page": pc.page, "method": pc.method} for pc in pages]}}

"""Reads a PDF or image into pages of words/lines (and tables), choosing text vs OCR per page."""
from __future__ import annotations

from dataclasses import dataclass, field

import pdfplumber
from PIL import Image, UnidentifiedImageError

from app.core.config import Settings
from app.core.control import JobControl
from app.core.errors import ExtractionError
from app.services import ocr_service
from app.services.layout import Line, Word, group_lines

MIN_WORDS_FOR_TEXT_PAGE = 8


@dataclass
class PageContent:
    page: int
    method: str  # "text" | "ocr"
    words: list[Word] = field(default_factory=list)
    lines: list[Line] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)
    warning: str | None = None
    source: int = 0  # index of the source file (for batches)


def _open_pdf(path):
    try:
        return pdfplumber.open(path)
    except Exception as e:  # pdfminer raises several exception types
        if "password" in type(e).__name__.lower() or "password" in str(e).lower():
            raise ExtractionError(
                "pdf_password_protected",
                "This PDF is password protected. Remove the password in your PDF viewer and upload it again.")
        raise ExtractionError("pdf_corrupt", "This PDF could not be read. It may be damaged or not a real PDF.")


def _text_tables(page) -> list[list[list[str]]]:
    def clean(t):
        return [[(c or "").replace("\n", " ").strip() for c in row] for row in t if row]

    found = [clean(t) for t in page.extract_tables()]
    found = [t for t in found if len(t) >= 2 and max(len(r) for r in t) >= 2]
    if found:
        return found
    # fallback for tables without ruling lines: be strict to avoid turning paragraphs into tables
    alt = page.extract_tables({"vertical_strategy": "text", "horizontal_strategy": "text"})
    out = []
    for t in alt:
        t = clean(t)
        if len(t) >= 3 and max(len(r) for r in t) >= 2:
            cells = [c for r in t for c in r]
            if cells and sum(1 for c in cells if c) / len(cells) >= 0.6:
                out.append(t)
    return out


def tables_from_lines(lines: list[Line]) -> list[list[list[str]]]:
    """Approximate tables for OCR pages: split each line at large horizontal gaps."""
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for ln in lines:
        h = sorted(w.height for w in ln.words)[len(ln.words) // 2]
        cells, buf = [], [ln.words[0]]
        for prev, w in zip(ln.words, ln.words[1:]):
            if w.x0 - prev.x1 > 1.5 * h:
                cells.append(" ".join(x.text for x in buf))
                buf = [w]
            else:
                buf.append(w)
        cells.append(" ".join(x.text for x in buf))
        if len(cells) >= 2:
            current.append(cells)
        else:
            if len(current) >= 2:
                tables.append(current)
            current = []
    if len(current) >= 2:
        tables.append(current)
    return tables


def read_document(path, kind: str, settings: Settings, ctl: JobControl | None = None,
                  want_tables: bool = False, source: int = 0) -> list[PageContent]:
    ctl = ctl or JobControl()
    if kind == "pdf":
        return _read_pdf(path, settings, ctl, want_tables, source)
    return _read_image(path, settings, ctl, want_tables, source)


def _read_pdf(path, settings, ctl, want_tables, source) -> list[PageContent]:
    pdf = _open_pdf(path)
    pages: list[PageContent] = []
    with pdf:
        n = len(pdf.pages)
        if n == 0:
            raise ExtractionError("empty_pdf", "This PDF has no pages.")
        if n > settings.max_pdf_pages:
            raise ExtractionError("too_many_pages",
                                  f"This PDF has {n} pages; the limit is {settings.max_pdf_pages}.", 413)
        ctl.add_total(n)
        ocr_ok: bool | None = None
        for i, page in enumerate(pdf.pages, 1):
            ctl.check()
            raw = page.extract_words(x_tolerance=2, y_tolerance=2, keep_blank_chars=False)
            words = [Word(w["text"], w["x0"], w["x1"], w["top"], w["bottom"], None, i) for w in raw]
            if len(words) >= MIN_WORDS_FOR_TEXT_PAGE:
                tables = _text_tables(page) if want_tables else []
                pages.append(PageContent(i, "text", words, group_lines(words, i), tables, None, source))
            else:
                if ocr_ok is None:
                    ocr_ok = ocr_service.ocr_available(settings)
                if not ocr_ok:
                    pages.append(PageContent(
                        i, "ocr", [], [], [],
                        f"Page {i} looks scanned but Tesseract OCR is not available, so it was skipped.", source))
                else:
                    ctl.set_stage("ocr")
                    try:
                        img = page.to_image(resolution=settings.ocr_dpi).original.convert("RGB")
                        owords = ocr_service.ocr_words(img, i, settings)
                    except ExtractionError as e:
                        pages.append(PageContent(i, "ocr", [], [], [], f"Page {i}: {e.message}", source))
                        ctl.advance()
                        continue
                    lines = group_lines(owords, i)
                    warn = None if owords else f"No readable text found on page {i}."
                    tables = tables_from_lines(lines) if want_tables else []
                    pages.append(PageContent(i, "ocr", owords, lines, tables, warn, source))
            page.flush_cache()
            ctl.advance()
    return pages


def _read_image(path, settings, ctl, want_tables, source) -> list[PageContent]:
    try:
        img = Image.open(path)
        img.load()
    except (UnidentifiedImageError, OSError):
        raise ExtractionError("image_corrupt", "This image could not be opened. It may be damaged.")
    if not ocr_service.ocr_available(settings):
        raise ExtractionError("ocr_unavailable", "Tesseract OCR is not installed or not on PATH.", 503)
    ctl.add_total(1)
    ctl.set_stage("ocr")
    ctl.check()
    words = ocr_service.ocr_words(img.convert("RGB"), 1, settings)
    ctl.advance()
    if not words:
        raise ExtractionError(
            "unreadable_image",
            "No readable text was found. The image may be blurry, too small, very dark or rotated; "
            "try a sharper, well-lit photo or scan.")
    lines = group_lines(words, 1)
    tables = tables_from_lines(lines) if want_tables else []
    return [PageContent(1, "ocr", words, lines, tables, None, source)]

"""Validate uploads by real file signature and structure, never by filename or declared MIME alone."""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.core.config import Settings
from app.core.errors import AppError

ALLOWED_BY_TOOL = {
    "bank_statement": {"pdf"},
    "invoice": {"pdf", "jpeg", "png", "webp"},
    "receipt": {"pdf", "jpeg", "png", "webp"},
    "tables": {"pdf"},
}
EXT = {"pdf": "pdf", "jpeg": "jpg", "png": "png", "webp": "webp"}
MIME = {"pdf": "application/pdf", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
MIN_IMAGE_SIDE = 200


@dataclass
class ValidatedFile:
    kind: str
    ext: str
    safe_name: str


def sniff(head: bytes) -> str | None:
    if head.startswith(b"%PDF-"):
        return "pdf"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def safe_filename(name: str | None) -> str:
    base = Path((name or "document").replace("\\", "/")).name
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._") or "document"
    return base[:80]


def validate_upload(filename: str | None, data: bytes, tool: str, settings: Settings) -> ValidatedFile:
    if tool not in ALLOWED_BY_TOOL:
        raise AppError("unknown_tool", "Unknown tool.", 400)
    if not data:
        raise AppError("empty_file", "The uploaded file is empty.", 400)
    if len(data) > settings.max_upload_bytes:
        raise AppError("file_too_large", f"File is larger than the {settings.max_upload_mb} MB limit.", 413)
    kind = sniff(data[:16])
    if kind is None:
        raise AppError("unsupported_type", "Unsupported file. Upload a PDF, JPG, PNG or WebP file.", 415)
    if kind not in ALLOWED_BY_TOOL[tool]:
        allowed = ", ".join(sorted(k.upper() for k in ALLOWED_BY_TOOL[tool]))
        raise AppError("unsupported_type", f"This tool accepts {allowed} files only.", 415)
    if kind != "pdf":
        try:
            with Image.open(io.BytesIO(data)) as im:
                im.verify()
            with Image.open(io.BytesIO(data)) as im:
                w, h = im.size
        except (UnidentifiedImageError, OSError, SyntaxError):
            raise AppError("image_corrupt", "This image file is damaged or not a real image.", 400)
        if min(w, h) < MIN_IMAGE_SIDE:
            raise AppError("image_too_small", "This image is too small to read reliably. Use a larger photo or scan.", 400)
    return ValidatedFile(kind, EXT[kind], safe_filename(filename))

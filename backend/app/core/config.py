"""Runtime configuration, read from environment variables (see .env.example)."""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    max_upload_mb: int
    max_pdf_pages: int
    max_batch_files: int
    job_timeout_seconds: int
    retention_minutes: int
    max_concurrency: int
    rate_limit_per_minute: int
    cors_origins: tuple[str, ...]
    jobs_dir: Path
    tesseract_cmd: str | None
    ocr_lang: str
    ocr_dpi: int

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def get_settings() -> Settings:
    origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
    jobs_dir = os.environ.get("JOBS_DIR") or str(Path(tempfile.gettempdir()) / "hisaab-jobs")
    return Settings(
        max_upload_mb=_int("MAX_UPLOAD_MB", 20),
        max_pdf_pages=_int("MAX_PDF_PAGES", 40),
        max_batch_files=_int("MAX_BATCH_FILES", 10),
        job_timeout_seconds=_int("JOB_TIMEOUT_SECONDS", 300),
        retention_minutes=_int("RETENTION_MINUTES", 60),
        max_concurrency=max(1, _int("MAX_CONCURRENCY", 2)),
        rate_limit_per_minute=_int("RATE_LIMIT_PER_MINUTE", 20),
        cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
        jobs_dir=Path(jobs_dir),
        tesseract_cmd=os.environ.get("TESSERACT_CMD") or None,
        ocr_lang=os.environ.get("OCR_LANG", "eng"),
        ocr_dpi=_int("OCR_DPI", 300),
    )

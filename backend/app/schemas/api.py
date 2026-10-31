"""Request/response models for the public API (shown in /api/docs)."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    index: int
    name: str
    kind: Literal["pdf", "jpeg", "png", "webp"]


class Progress(BaseModel):
    stage: str = Field(description="queued, reading, ocr, parsing or done")
    pages_done: int
    pages_total: Optional[int] = Field(None, description="Known once the document has been opened")


class JobError(BaseModel):
    code: str
    message: str


class JobCreated(BaseModel):
    job_id: str
    token: str = Field(description="Secret. Send as the X-Job-Token header on every later request for this job.")
    status: str
    expires_at: float = Field(description="Unix time after which the job and its files are deleted")


class JobStatus(BaseModel):
    job_id: str
    tool: str
    status: Literal["queued", "processing", "done", "failed", "cancelled"]
    progress: Progress
    error: Optional[JobError] = None
    expires_at: float
    files: list[FileInfo]


class PatchRequest(BaseModel):
    result: dict[str, Any] = Field(description="The edited parts of the result (transactions / fields+line_items / receipts / tables)")


class ExportRequest(BaseModel):
    format: Literal["xlsx", "csv", "zip"]
    part: Optional[Literal["details", "line_items"]] = Field(
        None, description="For CSV exports of multi-part results (invoice, receipts)")
    bom: bool = Field(True, description="Prefix CSV with a UTF-8 BOM so Excel on Windows reads it correctly")


class Health(BaseModel):
    status: Literal["ok"]
    version: str
    ocr_available: bool
    limits: dict[str, int]

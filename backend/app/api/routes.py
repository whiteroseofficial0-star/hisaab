"""Versioned REST API. Every job route needs the job's secret token (X-Job-Token)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Header, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response

from app import __version__
from app.core.errors import AppError
from app.core.jobs import Job
from app.schemas.api import ExportRequest, FileInfo, Health, JobCreated, JobStatus, PatchRequest, Progress
from app.services import ocr_service
from app.services.export_service import export_result
from app.services.file_validation_service import ALLOWED_BY_TOOL, MIME, validate_upload
from app.services.pipeline import run_job
from app.services.result_service import apply_patch

router = APIRouter(prefix="/api/v1")


def get_job(request: Request, job_id: str, x_job_token: str | None = Header(default=None)) -> Job:
    return request.app.state.store.get(job_id, x_job_token)


async def _read_limited(f: UploadFile, limit: int) -> bytes:
    chunks, size = [], 0
    while True:
        chunk = await f.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > limit:
            raise AppError("file_too_large", f"File is larger than the {limit // (1024 * 1024)} MB limit.", 413)
        chunks.append(chunk)
    return b"".join(chunks)


def _status(job: Job) -> JobStatus:
    c = job.control
    return JobStatus(
        job_id=job.id, tool=job.tool, status=job.status,  # type: ignore[arg-type]
        progress=Progress(stage=c.stage, pages_done=c.pages_done, pages_total=c.pages_total),
        error=job.error, expires_at=job.expires_at,
        files=[FileInfo(index=f.index, name=f.safe_name, kind=f.kind) for f in job.files],  # type: ignore[arg-type]
    )


@router.get("/health", response_model=Health)
def health(request: Request):
    s = request.app.state.settings
    return Health(status="ok", version=__version__, ocr_available=ocr_service.ocr_available(s),
                  limits={"max_upload_mb": s.max_upload_mb, "max_pdf_pages": s.max_pdf_pages,
                          "max_batch_files": s.max_batch_files, "retention_minutes": s.retention_minutes})


@router.post("/jobs", response_model=JobCreated, status_code=202)
async def create_job(request: Request, tool: str = Form(...), files: list[UploadFile] = File(...)):
    s = request.app.state.settings
    ip = request.client.host if request.client else "unknown"
    if not request.app.state.limiter.allow(ip):
        raise AppError("rate_limited", "Too many uploads. Please wait a minute and try again.", 429)
    if tool not in ALLOWED_BY_TOOL:
        raise AppError("unknown_tool", "Unknown tool.", 400)
    max_files = s.max_batch_files if tool == "receipt" else 1
    if not files or len(files) > max_files:
        raise AppError("bad_file_count", f"Upload between 1 and {max_files} file(s) for this tool.", 400)
    uploads = []
    for f in files:
        data = await _read_limited(f, s.max_upload_bytes)
        v = validate_upload(f.filename, data, tool, s)
        uploads.append((v.kind, v.ext, v.safe_name, data))
    job = request.app.state.store.create(tool, uploads)
    request.app.state.executor.submit(run_job, job, s)
    return JobCreated(job_id=job.id, token=job.token, status=job.status, expires_at=job.expires_at)


@router.get("/jobs/{job_id}", response_model=JobStatus)
def get_status(job: Job = Depends(get_job)):
    return _status(job)


@router.get("/jobs/{job_id}/result")
def get_result(job: Job = Depends(get_job)):
    if job.status != "done" or job.result is None:
        raise AppError("not_ready", f"Result is not available (status: {job.status}).", 409)
    return JSONResponse(job.result)


@router.patch("/jobs/{job_id}/result")
def patch_result(body: PatchRequest, job: Job = Depends(get_job)):
    if job.status != "done" or job.result is None:
        raise AppError("not_ready", "Nothing to edit yet.", 409)
    with job.lock:
        job.result = apply_patch(job.result, body.result)
        return JSONResponse(job.result)


@router.post("/jobs/{job_id}/export")
def export(body: ExportRequest, job: Job = Depends(get_job)):
    if job.status != "done" or job.result is None:
        raise AppError("not_ready", "Nothing to export yet.", 409)
    with job.lock:
        data, filename, mime = export_result(job.result, body.format, body.part, body.bom)
    return Response(content=data, media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/jobs/{job_id}/files/{index}")
def original_file(index: int, job: Job = Depends(get_job)):
    f = next((x for x in job.files if x.index == index), None)
    if f is None or not f.path.exists():
        raise AppError("file_not_found", "File not found.", 404)
    return FileResponse(f.path, media_type=MIME[f.kind],
                        headers={"Content-Disposition": f'inline; filename="{f.safe_name}"',
                                 "Content-Security-Policy": "sandbox"})


@router.delete("/jobs/{job_id}", status_code=204)
def delete_job(request: Request, job: Job = Depends(get_job)):
    request.app.state.store.delete(job.id)
    return Response(status_code=204)

"""In-memory job store with private per-job tokens, private temp files and expiry cleanup."""
from __future__ import annotations

import logging
import secrets
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import Settings
from app.core.control import JobControl
from app.core.errors import AppError

log = logging.getLogger("hisaab.jobs")


@dataclass
class StoredFile:
    index: int
    kind: str
    safe_name: str
    path: Path


@dataclass
class Job:
    id: str
    token: str
    tool: str
    created_at: float
    expires_at: float
    files: list[StoredFile]
    control: JobControl
    status: str = "queued"  # queued | processing | done | failed | cancelled
    result: dict | None = None
    error: dict | None = None
    failed_files: list[dict] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)


class JobStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        settings.jobs_dir.mkdir(parents=True, exist_ok=True)
        try:
            settings.jobs_dir.chmod(0o700)
        except OSError:
            pass

    def create(self, tool: str, uploads: list[tuple[str, str, str, bytes]]) -> Job:
        """uploads: (kind, ext, safe_name, data). Files are stored under random names, never the user's."""
        job_id = secrets.token_urlsafe(16)
        folder = self.settings.jobs_dir / job_id
        folder.mkdir(parents=True, exist_ok=False)
        files = []
        for i, (kind, ext, safe_name, data) in enumerate(uploads):
            p = folder / f"input_{i}.{ext}"
            p.write_bytes(data)
            files.append(StoredFile(i, kind, safe_name, p))
        now = time.time()
        job = Job(job_id, secrets.token_urlsafe(24), tool, now, now + self.settings.retention_minutes * 60,
                  files, JobControl(self.settings.job_timeout_seconds))
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str, token: str | None) -> Job:
        """Unknown, expired and wrong-token all look identical so job ids cannot be probed."""
        job = self._jobs.get(job_id)
        if job is None or not token or not secrets.compare_digest(job.token, token) or job.expires_at < time.time():
            raise AppError("job_not_found", "Job not found or expired.", 404)
        return job

    def delete(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.pop(job_id, None)
        if job:
            job.control.cancelled.set()
            shutil.rmtree(self.settings.jobs_dir / job.id, ignore_errors=True)

    def purge_expired(self) -> int:
        now = time.time()
        with self._lock:
            expired = [j for j in self._jobs.values() if j.expires_at < now]
        for j in expired:
            self.delete(j.id)
        # also remove orphaned folders (e.g. after a crash) older than the retention period
        cutoff = now - self.settings.retention_minutes * 60
        for p in self.settings.jobs_dir.iterdir():
            try:
                if p.is_dir() and p.name not in self._jobs and p.stat().st_mtime < cutoff:
                    shutil.rmtree(p, ignore_errors=True)
            except OSError:
                pass
        return len(expired)

    def start_cleanup_thread(self, interval: int = 60) -> threading.Thread:
        def loop():
            while True:
                time.sleep(interval)
                try:
                    self.purge_expired()
                except Exception:
                    log.error("cleanup failed")
        t = threading.Thread(target=loop, daemon=True, name="hisaab-cleanup")
        t.start()
        return t

"""FastAPI application factory."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes import router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.jobs import JobStore
from app.core.ratelimit import RateLimiter

log = logging.getLogger("hisaab")


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    store = JobStore(settings)
    executor = ThreadPoolExecutor(max_workers=settings.max_concurrency, thread_name_prefix="hisaab-worker")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store.purge_expired()
        store.start_cleanup_thread()
        yield
        executor.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title="Hisaab API", version=__version__, lifespan=lifespan,
                  docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None,
                  description="Convert financial documents to editable data and Excel/CSV. Jobs expire automatically.")
    app.state.settings, app.state.store, app.state.executor = settings, store, executor
    app.state.limiter = RateLimiter(settings.rate_limit_per_minute)

    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins),
                       allow_methods=["GET", "POST", "PATCH", "DELETE"],
                       allow_headers=["Content-Type", "X-Job-Token"], expose_headers=["Content-Disposition"])

    @app.middleware("http")
    async def guard(request: Request, call_next):
        if request.method == "POST" and request.url.path == "/api/v1/jobs":
            cl = request.headers.get("content-length")
            limit = settings.max_upload_bytes * settings.max_batch_files + 1024 * 1024
            if cl and cl.isdigit() and int(cl) > limit:
                return _err(413, "request_too_large", "The upload is too large.")
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers.setdefault("Cache-Control", "no-store")
        return resp

    @app.exception_handler(AppError)
    async def app_error(_: Request, e: AppError):
        return _err(e.status, e.code, e.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, e: RequestValidationError):
        return _err(422, "invalid_request", "The request was not valid. Check the fields and try again.")

    @app.exception_handler(Exception)
    async def unhandled(_: Request, e: Exception):
        log.error("unhandled %s", type(e).__name__)
        return _err(500, "internal_error", "Something went wrong. Please try again.")

    app.include_router(router)
    return app


app = create_app()

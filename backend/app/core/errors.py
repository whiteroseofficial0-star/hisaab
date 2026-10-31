"""Application errors. Messages are safe to show to end users (no paths, no document content)."""
from __future__ import annotations


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class ExtractionError(AppError):
    def __init__(self, code: str, message: str, status: int = 422):
        super().__init__(code, message, status)

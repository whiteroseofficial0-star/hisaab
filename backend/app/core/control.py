"""Cooperative cancellation, timeout and genuine progress reporting for a job."""
from __future__ import annotations

import threading
import time


class JobCancelled(Exception):
    pass


class JobTimeout(Exception):
    pass


class JobControl:
    def __init__(self, timeout_seconds: float | None = None):
        self.timeout_seconds = timeout_seconds
        self.deadline: float | None = None
        self.cancelled = threading.Event()
        self.stage = "queued"
        self.pages_done = 0
        self.pages_total: int | None = None

    def start(self) -> None:
        if self.timeout_seconds:
            self.deadline = time.monotonic() + self.timeout_seconds

    def check(self) -> None:
        if self.cancelled.is_set():
            raise JobCancelled()
        if self.deadline is not None and time.monotonic() > self.deadline:
            raise JobTimeout()

    def set_stage(self, stage: str) -> None:
        self.stage = stage

    def add_total(self, n: int) -> None:
        self.pages_total = (self.pages_total or 0) + n

    def advance(self, n: int = 1) -> None:
        self.pages_done += n

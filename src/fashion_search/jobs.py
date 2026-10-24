"""A tiny in-process job queue for slow GPU work (virtual try-on, ~50 s per image).

One worker thread runs jobs in order, because the GPU can only fit one try-on at a
time. Jobs live in memory; the job function gets its own `Job`, so it can persist its
result under the job id (the API saves finished try-ons as looks, see store.py).
"""

import queue
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

Status = Literal["queued", "running", "done", "error"]


@dataclass
class Job:
    """One unit of background work and its outcome."""

    id: str
    status: Status = "queued"
    created: float = field(default_factory=time.time)
    started: float | None = None
    finished: float | None = None
    result: Any = None
    error: str | None = None


class JobQueue:
    """FIFO queue processed by a single worker thread (one GPU, one job at a time)."""

    def __init__(self, max_kept: int = 50):
        self._jobs: dict[str, Job] = {}
        self._order: list[str] = []
        self._queue: queue.Queue[tuple[Job, Callable[[Job], Any]]] = queue.Queue()
        self._lock = threading.Lock()
        self._max_kept = max_kept
        threading.Thread(target=self._worker, daemon=True, name="job-worker").start()

    def submit(self, fn: Callable[[Job], Any]) -> Job:
        """Queue `fn(job)` to run on the worker and return the job immediately."""
        job = Job(id=uuid.uuid4().hex[:12])
        with self._lock:
            self._jobs[job.id] = job
            self._order.append(job.id)
            # Drop the oldest finished jobs so results don't pile up in memory.
            while len(self._order) > self._max_kept:
                old = self._jobs[self._order[0]]
                if old.status in ("queued", "running"):
                    break
                del self._jobs[self._order.pop(0)]
        self._queue.put((job, fn))
        return job

    def get(self, job_id: str) -> Job | None:
        """The job with this id, or None if unknown or already discarded."""
        return self._jobs.get(job_id)

    def position(self, job: Job) -> int:
        """How many jobs are ahead of this one (0 = next or running)."""
        with self._lock:
            waiting = [j for j in self._order if self._jobs[j].status == "queued"]
        return waiting.index(job.id) if job.id in waiting else 0

    def _worker(self) -> None:
        while True:
            job, fn = self._queue.get()
            job.status, job.started = "running", time.time()
            try:
                job.result = fn(job)
                job.status = "done"
            except Exception as e:  # report any failure to the client instead of dying
                job.error, job.status = str(e) or type(e).__name__, "error"
            job.finished = time.time()

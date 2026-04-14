from __future__ import annotations

from dataclasses import dataclass
from queue import Queue
from threading import Lock, Thread
from urllib.parse import quote
from uuid import uuid4

from app.models import DownloadRequest, DownloadResult, JobCreateResponse, JobState, JobStatusResponse, utc_now
from app.services.downloader import DownloadError, DownloadService


@dataclass
class JobRecord:
    job_id: str
    request: DownloadRequest
    state: JobState
    progress: int
    message: str
    created_at: object
    updated_at: object
    error: str | None = None
    result: DownloadResult | None = None

    def to_status(self) -> JobStatusResponse:
        return JobStatusResponse(
            job_id=self.job_id,
            state=self.state,
            progress=self.progress,
            message=self.message,
            created_at=self.created_at,
            updated_at=self.updated_at,
            error=self.error,
            result=self.result,
        )


class JobManager:
    def __init__(self, downloader: DownloadService):
        self._downloader = downloader
        self._jobs: dict[str, JobRecord] = {}
        self._queue: Queue[str] = Queue()
        self._lock = Lock()
        self._worker_thread: Thread | None = None

    def start(self) -> None:
        if self._worker_thread and self._worker_thread.is_alive():
            return

        self._worker_thread = Thread(target=self._worker_loop, daemon=True, name="music-downloader-worker")
        self._worker_thread.start()

    def create_job(self, request: DownloadRequest) -> JobCreateResponse:
        job_id = uuid4().hex
        now = utc_now()
        record = JobRecord(
            job_id=job_id,
            request=request,
            state=JobState.queued,
            progress=0,
            message="[QUEUED]",
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            self._jobs[job_id] = record

        self._queue.put(job_id)
        return JobCreateResponse(job_id=job_id, state=record.state)

    def get_job(self, job_id: str) -> JobStatusResponse | None:
        with self._lock:
            record = self._jobs.get(job_id)
            if not record:
                return None
            return record.to_status()

    def list_jobs(self) -> list[JobStatusResponse]:
        with self._lock:
            records = list(self._jobs.values())

        records.sort(key=lambda item: item.created_at, reverse=True)
        return [record.to_status() for record in records]

    def _worker_loop(self) -> None:
        while True:
            job_id = self._queue.get()
            try:
                self._run_job(job_id)
            finally:
                self._queue.task_done()

    def _run_job(self, job_id: str) -> None:
        record = self._unsafe_get_record(job_id)
        if not record:
            return

        self._update(job_id, state=JobState.running, progress=2, message="[STARTING]")

        try:
            artifacts = self._downloader.download_and_tag(
                request=record.request,
                job_id=job_id,
                progress=lambda pct, msg: self._update(
                    job_id,
                    progress=max(0, min(100, pct)),
                    message=msg,
                    state=JobState.running,
                ),
            )
            relative_file_path = artifacts.output_file.relative_to(self._downloader.output_root).as_posix()
            download_url = "/media/" + quote(relative_file_path, safe="/")

            result = DownloadResult(
                source=artifacts.metadata.source,
                file_path=relative_file_path,
                download_url=download_url,
                metadata=artifacts.metadata,
                tagged=True,
                navidrome_scan_triggered=artifacts.navidrome_scan_triggered,
            )

            self._update(
                job_id,
                state=JobState.completed,
                progress=100,
                message="[COMPLETED]",
                result=result,
                error=None,
            )
        except DownloadError as exc:
            self._update(
                job_id,
                state=JobState.failed,
                progress=100,
                message="[FAILED]",
                error=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            self._update(
                job_id,
                state=JobState.failed,
                progress=100,
                message="[FAILED]",
                error=f"Unexpected worker error: {exc}",
            )

    def _unsafe_get_record(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _update(
        self,
        job_id: str,
        *,
        state: JobState | None = None,
        progress: int | None = None,
        message: str | None = None,
        error: str | None = None,
        result: DownloadResult | None = None,
    ) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if not record:
                return

            if state is not None:
                record.state = state
            if progress is not None:
                record.progress = progress
            if message is not None:
                record.message = message
            if error is not None:
                record.error = error
            if result is not None:
                record.result = result

            record.updated_at = utc_now()

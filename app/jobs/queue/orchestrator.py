import asyncio
import logging
import uuid
from datetime import datetime, timezone
from app.domain.models.source_job import SourceJob

logger = logging.getLogger(__name__)

class JobOrchestrator:
    def __init__(self, repo, parse_service, sse_publisher):
        self.repo = repo
        self.parse_service = parse_service
        self.sse = sse_publisher
        self.queue = asyncio.Queue()
        self.worker_task = None

    async def start(self):
        if not self.worker_task:
            self.worker_task = asyncio.create_task(self._worker())

    async def enqueue(self, url: str, edit_payload: dict):
        job = SourceJob(id=str(uuid.uuid4()), source_url=url, source_platform='unknown')
        self.repo.upsert_job(job.model_dump(mode='json'))
        await self.queue.put({'job': job, 'url': url, 'edit_payload': edit_payload})
        await self.sse.publish(job.id, self._event(job))
        logger.info('job_enqueued job_id=%s url=%s', job.id, url)
        return job.model_dump(mode='json')

    async def _worker(self):
        while True:
            item = await self.queue.get()
            job = item['job']
            try:
                adapter = self.parse_service.registry.resolve(item['url'])
                job.source_platform = adapter.provider
                for status, progress, msg in [('fetching',10,'Fetching source metadata'), ('processing',50,'Processing audio'), ('tagging',80,'Applying metadata')]:
                    job.transition(status, progress, msg)
                    self.repo.upsert_job(job.model_dump(mode='json'))
                    await self.sse.publish(job.id, self._event(job))
                _, artifact = self.parse_service.execute(job.id, item['url'], item['edit_payload'])
                self.repo.save_artifact(artifact.model_dump(mode='json'))
                job.transition('completed',100,'Completed')
                self.repo.upsert_job(job.model_dump(mode='json'))
                await self.sse.publish(job.id, self._event(job))
                logger.info('job_completed job_id=%s artifact=%s', job.id, artifact.filename)
            except Exception as exc:
                logger.exception('job_failed job_id=%s error=%s', job.id, exc)
                now = datetime.now(timezone.utc)
                job.status='failed'; job.progress_percent=max(job.progress_percent,1); job.status_message='Failed'; job.error_code='JOB_FAILED'; job.error_detail=str(exc); job.updated_at=now; job.completed_at=now
                self.repo.upsert_job(job.model_dump(mode='json'))
                await self.sse.publish(job.id, self._event(job))
            finally:
                self.queue.task_done()

    def _event(self, job):
        return {'jobId': job.id, 'status': job.status, 'progressPercent': job.progress_percent, 'statusMessage': job.status_message, 'updatedAt': job.updated_at.isoformat()}

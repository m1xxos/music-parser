from app.domain.models.batch_request import BatchRequest

class BatchService:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    async def submit(self, payload: dict):
        req = BatchRequest(**payload)
        out = []
        for url in req.urls:
            job = await self.orchestrator.enqueue(str(url), {'trim_start_seconds': 0})
            out.append({'url': str(url), 'jobId': job['id'], 'status': job['status']})
        return out

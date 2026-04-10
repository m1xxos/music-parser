from app.domain.models.batch_request import BatchRequest

class BatchService:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    async def submit(self, payload: dict):
        req = BatchRequest(**payload)
        start = req.trim.startSeconds if req.trim else 0
        edit_payload = {
            'trim_start_seconds': 0 if start is None else start,
            'trim_end_seconds': req.trim.endSeconds if req.trim else None,
            'artist_override': req.metadata.artist if req.metadata else None,
            'album_override': req.metadata.album if req.metadata else None,
        }
        out = []
        for url in req.urls:
            job = await self.orchestrator.enqueue(str(url), edit_payload)
            out.append({'url': str(url), 'jobId': job['id'], 'status': job['status']})
        return out

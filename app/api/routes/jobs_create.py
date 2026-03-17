from pydantic import BaseModel, HttpUrl
from fastapi import APIRouter, Depends

router = APIRouter()

class Trim(BaseModel):
    startSeconds: float | None = None
    endSeconds: float | None = None

class MetadataInput(BaseModel):
    title: str | None = None
    artist: str | None = None
    album: str | None = None

class CreateJobRequest(BaseModel):
    url: HttpUrl
    trim: Trim | None = None
    metadata: MetadataInput | None = None

@router.post('/jobs', status_code=202)
async def create_job(payload: CreateJobRequest, orchestrator=Depends(lambda: router.orchestrator)):
    start = payload.trim.startSeconds if payload.trim else 0
    edit_payload = {
        'trim_start_seconds': 0 if start is None else start,
        'trim_end_seconds': payload.trim.endSeconds if payload.trim else None,
        'title_override': payload.metadata.title if payload.metadata else None,
        'artist_override': payload.metadata.artist if payload.metadata else None,
        'album_override': payload.metadata.album if payload.metadata else None,
    }
    job = await orchestrator.enqueue(str(payload.url), edit_payload)
    return {'jobId': job['id'], 'status': job['status']}

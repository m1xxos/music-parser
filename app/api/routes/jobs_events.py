from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
router = APIRouter()

@router.get('/jobs/{job_id}/events')
async def job_events(job_id: str, sse=Depends(lambda: router.sse_publisher)):
    return StreamingResponse(sse.stream(job_id), media_type='text/event-stream')

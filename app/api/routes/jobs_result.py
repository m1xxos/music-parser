from fastapi import APIRouter, Depends, HTTPException
router = APIRouter()

@router.get('/jobs/{job_id}/result')
async def job_result(job_id: str, repo=Depends(lambda: router.repository), settings=Depends(lambda: router.settings)):
    artifact = repo.get_artifact_by_job(job_id)
    job = repo.get_job(job_id)
    if not artifact or not job or job['status'] != 'completed':
        raise HTTPException(status_code=404, detail='Result not available')
    return {'jobId': job_id, 'status': 'completed', 'output': {'filename': artifact['filename'], 'format': artifact['format'], 'sizeBytes': artifact['size_bytes'], 'downloadUrl': f"http://localhost:8000{settings.api_prefix}/downloads/{job_id}?token={artifact['download_token']}"}}

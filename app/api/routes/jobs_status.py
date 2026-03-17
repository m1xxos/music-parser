from fastapi import APIRouter, Depends, HTTPException
router = APIRouter()

@router.get('/jobs/{job_id}')
async def job_status(job_id: str, repo=Depends(lambda: router.repository)):
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return {'jobId': job['id'], 'status': job['status'], 'progressPercent': job['progress_percent'], 'statusMessage': job['status_message'], 'updatedAt': job['updated_at'], 'error': {'code': job.get('error_code'), 'message': job.get('error_detail')} if job.get('error_code') else None}

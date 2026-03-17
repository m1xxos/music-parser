from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
router = APIRouter()

@router.get('/downloads/{job_id}')
async def download(job_id: str, token: str = Query(...), repo=Depends(lambda: router.repository)):
    artifact = repo.get_artifact_by_job(job_id)
    if not artifact or artifact.get('download_token') != token:
        raise HTTPException(status_code=403, detail='Invalid token')
    path = Path(artifact['storage_path'])
    if not path.exists():
        raise HTTPException(status_code=404, detail='File missing')
    return FileResponse(path, filename=artifact['filename'], media_type='audio/mpeg')

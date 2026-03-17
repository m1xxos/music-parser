from fastapi import APIRouter, Depends, Query
router = APIRouter()

@router.get('/history')
async def history(limit: int = Query(default=20, ge=1, le=100), repo=Depends(lambda: router.repository)):
    rows = repo.list_history(limit)
    return [{'jobId': r['id'], 'status': r['status'], 'summary': r['status_message'], 'updatedAt': r['updated_at']} for r in rows]

from fastapi import APIRouter, Depends
from app.domain.models.batch_request import BatchRequest
router = APIRouter()

@router.post('/batch', status_code=202)
async def batch(payload: BatchRequest, service=Depends(lambda: router.batch_service)):
    return {'items': await service.submit(payload.model_dump())}

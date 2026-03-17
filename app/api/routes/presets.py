from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
router = APIRouter()

class PresetCreate(BaseModel):
    name: str
    trim_start_seconds: float = 0
    trim_end_seconds: float | None = None
    metadata: dict[str, str] = {}

@router.post('/presets', status_code=201)
async def create_preset(payload: PresetCreate, service=Depends(lambda: router.preset_service)):
    preset = service.create(payload.name, payload.trim_start_seconds, payload.trim_end_seconds, payload.metadata)
    return preset.model_dump(mode='json')

@router.get('/presets')
async def list_presets(service=Depends(lambda: router.preset_service)):
    return service.list()

@router.post('/presets/{preset_id}/apply')
async def apply_preset(preset_id: str, service=Depends(lambda: router.preset_service)):
    try:
        return service.apply(preset_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

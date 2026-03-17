import uuid
from datetime import datetime, timezone
from app.domain.models.preset_profile import PresetProfile

class PresetService:
    def __init__(self, repository):
        self.repo = repository

    def create(self, name: str, trim_start_seconds: float, trim_end_seconds: float | None, metadata: dict[str, str]):
        preset = PresetProfile(id=str(uuid.uuid4()), name=name, trim_start_seconds=trim_start_seconds, trim_end_seconds=trim_end_seconds, metadata=metadata, created_at=datetime.now(timezone.utc))
        self.repo.save_preset(preset.model_dump(mode='json'))
        return preset

    def list(self):
        return self.repo.list_presets()

    def apply(self, preset_id: str):
        preset = self.repo.get_preset(preset_id)
        if not preset:
            raise ValueError('Preset not found')
        return preset

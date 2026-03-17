import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.domain.models.edit_profile import EditProfile
from app.domain.models.export_artifact import ExportArtifact
from app.domain.models.media_descriptor import MediaDescriptor
from app.media.metadata.service import apply_metadata, finalize_output_path
from app.media.trim.service import trim_audio

class ParseService:
    def __init__(self, adapter_registry, output_dir: str):
        self.registry = adapter_registry
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def execute(self, job_id: str, url: str, edit_payload: dict):
        adapter = self.registry.resolve(url)
        metadata = adapter.fetch_metadata(url)
        descriptor = MediaDescriptor(job_id=job_id, source_media_id=metadata.get('id', job_id), title=metadata.get('title') or 'Unknown', creator=metadata.get('uploader') or metadata.get('artist') or metadata.get('channel'), duration_seconds=int(metadata.get('duration') or 1), thumbnail_url=metadata.get('thumbnail'))
        edit = EditProfile(job_id=job_id, **edit_payload)

        with tempfile.TemporaryDirectory() as tmp:
            source_mp3, dl_meta = adapter.download_audio(url, tmp)
            trimmed = trim_audio(source_mp3, edit.trim_start_seconds, edit.trim_end_seconds, tmp)
            title = edit.title_override or descriptor.title
            artist = edit.artist_override or descriptor.creator or 'Unknown'
            album = edit.album_override or title
            out = finalize_output_path(self.output_dir, title)
            shutil.copy2(trimmed, out)
            apply_metadata(str(out), title, artist, album)

        artifact = ExportArtifact(id=str(uuid.uuid4()), job_id=job_id, filename=out.name, format='mp3', size_bytes=out.stat().st_size, duration_seconds=float(dl_meta.get('duration') or descriptor.duration_seconds), storage_path=str(out), download_token=str(uuid.uuid4()), created_at=datetime.now(timezone.utc))
        return descriptor, artifact

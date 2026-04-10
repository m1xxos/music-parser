import re
from pathlib import Path
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1
from mutagen.mp3 import MP3
from app.domain.models.export_artifact import resolve_collision

def sanitize_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r'[\x00-\x1f]', '', value).strip()
    return cleaned[:200]

def apply_metadata(path: str, title: str, artist: str, album: str, cover_bytes: bytes | None = None, cover_mime: str = 'image/jpeg') -> None:
    audio = MP3(path, ID3=ID3)
    if audio.tags is None:
        audio.add_tags()
    audio.tags['TIT2'] = TIT2(encoding=3, text=sanitize_value(title) or 'Unknown')
    audio.tags['TPE1'] = TPE1(encoding=3, text=sanitize_value(artist) or 'Unknown')
    audio.tags['TALB'] = TALB(encoding=3, text=sanitize_value(album) or 'Unknown')
    if cover_bytes:
        audio.tags['APIC'] = APIC(encoding=0, mime=cover_mime, type=3, desc='Cover', data=cover_bytes)
    audio.save()

def finalize_output_path(output_dir: str, desired_name: str) -> Path:
    name = desired_name.removesuffix('.mp3').removesuffix('.MP3')
    safe = re.sub(r'[^\w\s\-().]', '', name).strip() or 'audio'
    safe = re.sub(r'\s+', ' ', safe)
    return resolve_collision(Path(output_dir), f'{safe}.mp3')

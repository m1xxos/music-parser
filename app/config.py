from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_AUDIO_FORMATS = ("mp3", "m4a", "flac")
SUPPORTED_AUDIO_QUALITIES = ("128", "192", "256", "320")


@dataclass(frozen=True)
class Settings:
    output_root: Path
    temp_root: Path
    default_audio_format: str
    default_audio_quality: str
    navidrome_scan_url: str | None
    navidrome_scan_token: str | None
    navidrome_scan_header: str
    http_timeout_seconds: int


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _read_audio_format() -> str:
    value = os.getenv("DEFAULT_AUDIO_FORMAT", "mp3").strip().lower()
    if value not in SUPPORTED_AUDIO_FORMATS:
        return "mp3"
    return value


def _read_audio_quality() -> str:
    value = os.getenv("DEFAULT_AUDIO_QUALITY", "320").strip().lower().replace("k", "")
    if value not in SUPPORTED_AUDIO_QUALITIES:
        return "320"
    return value


def load_settings() -> Settings:
    output_root = Path(os.getenv("OUTPUT_ROOT", "/data/music")).expanduser()
    temp_root = Path(os.getenv("TMP_ROOT", "/data/tmp")).expanduser()

    return Settings(
        output_root=output_root,
        temp_root=temp_root,
        default_audio_format=_read_audio_format(),
        default_audio_quality=_read_audio_quality(),
        navidrome_scan_url=_clean_optional(os.getenv("NAVIDROME_SCAN_URL")),
        navidrome_scan_token=_clean_optional(os.getenv("NAVIDROME_SCAN_TOKEN")),
        navidrome_scan_header=os.getenv("NAVIDROME_SCAN_HEADER", "Authorization").strip() or "Authorization",
        http_timeout_seconds=int(os.getenv("HTTP_TIMEOUT_SECONDS", "20")),
    )


def ensure_directories(settings: Settings) -> None:
    settings.output_root.mkdir(parents=True, exist_ok=True)
    settings.temp_root.mkdir(parents=True, exist_ok=True)

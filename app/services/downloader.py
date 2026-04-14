from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import requests
import yt_dlp
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, COMM, TALB, TCON, TDRC, TIT2, TPE1, TRCK, ID3
from mutagen.mp4 import MP4, MP4Cover

from app.config import Settings
from app.models import DownloadRequest, MetadataOverrides, MetadataPreview, SourcePlatform


ProgressCallback = Callable[[int, str], None]


class DownloadError(RuntimeError):
    """Raised when metadata extraction, download, or tagging fails."""


@dataclass
class DownloadArtifacts:
    output_file: Path
    metadata: MetadataPreview
    navidrome_scan_triggered: bool


class DownloadService:
    def __init__(self, settings: Settings):
        self._settings = settings

    @property
    def output_root(self) -> Path:
        return self._settings.output_root

    def extract_metadata(self, url: str) -> MetadataPreview:
        info = self._extract_info(url=url, download=False)
        return self._normalize_metadata(info=info, url=url)

    def download_and_tag(
        self,
        request: DownloadRequest,
        job_id: str,
        progress: ProgressCallback | None = None,
    ) -> DownloadArtifacts:
        progress_callback = progress or (lambda _percent, _message: None)
        url = str(request.url)
        temp_dir = self._settings.temp_root / job_id

        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            progress_callback(5, "[EXTRACTING METADATA]")
            preview_before_download = self.extract_metadata(url)

            progress_callback(20, "[DOWNLOADING AUDIO]")
            info_after_download, downloaded_file = self._download_audio(url=url, target_dir=temp_dir)
            preview_after_download = self._normalize_metadata(info=info_after_download, url=url)

            resolved_metadata = self._merge_metadata(
                provider=preview_after_download,
                overrides=request.metadata,
            )
            if not resolved_metadata.comment:
                resolved_metadata.comment = preview_before_download.description

            progress_callback(55, "[TRANSCODING]")
            converted_file = self._transcode(
                source_file=downloaded_file,
                output_format=request.output_format.value,
                quality=request.quality,
                work_dir=temp_dir,
            )

            progress_callback(75, "[FETCHING COVER]")
            cover_bytes = self._fetch_cover_bytes(
                info=info_after_download,
                thumbnail_url=resolved_metadata.thumbnail_url,
            )

            progress_callback(85, "[WRITING TAGS]")
            self._apply_tags(
                file_path=converted_file,
                output_format=request.output_format.value,
                metadata=resolved_metadata,
                cover_bytes=cover_bytes,
            )

            progress_callback(92, "[MOVING TO LIBRARY]")
            final_file = self._move_to_library(
                source_file=converted_file,
                output_format=request.output_format.value,
                metadata=resolved_metadata,
            )

            scan_triggered = False
            if request.auto_scan_navidrome:
                progress_callback(97, "[TRIGGERING NAVIDROME SCAN]")
                scan_triggered = self._trigger_navidrome_scan()

            progress_callback(100, "[DONE]")
            return DownloadArtifacts(
                output_file=final_file,
                metadata=resolved_metadata,
                navidrome_scan_triggered=scan_triggered,
            )
        except DownloadError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DownloadError(str(exc)) from exc
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _extract_info(self, url: str, download: bool) -> dict[str, Any]:
        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": self._settings.http_timeout_seconds,
            "extract_flat": "discard_in_playlist" if not download else False,
        }
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=download)
        except Exception as exc:  # noqa: BLE001
            raise DownloadError(f"yt-dlp failed: {exc}") from exc

        normalized = self._pick_single_entry(info)
        if not isinstance(normalized, dict):
            raise DownloadError("Could not parse media metadata for this URL")
        return normalized

    def _download_audio(self, url: str, target_dir: Path) -> tuple[dict[str, Any], Path]:
        output_template = target_dir / "%(title).160B-%(id)s.%(ext)s"
        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": self._settings.http_timeout_seconds,
            "format": "bestaudio/best",
            "outtmpl": str(output_template),
            "writethumbnail": True,
        }

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                normalized = self._pick_single_entry(info)
                expected_file = Path(ydl.prepare_filename(normalized))
        except Exception as exc:  # noqa: BLE001
            raise DownloadError(f"Download failed: {exc}") from exc

        media_file = self._find_downloaded_media_file(expected_file=expected_file, search_dir=target_dir)
        return normalized, media_file

    def _find_downloaded_media_file(self, expected_file: Path, search_dir: Path) -> Path:
        if expected_file.exists() and expected_file.is_file():
            return expected_file

        preferred_ext = {
            ".mp3",
            ".m4a",
            ".webm",
            ".opus",
            ".ogg",
            ".aac",
            ".wav",
            ".flac",
            ".mp4",
            ".mkv",
        }
        ignored_ext = {".jpg", ".jpeg", ".png", ".webp", ".part", ".ytdl", ".vtt", ".json"}

        stem = expected_file.stem
        candidate_files = sorted(path for path in search_dir.glob(f"{stem}*") if path.is_file())
        for path in candidate_files:
            suffix = path.suffix.lower()
            if suffix in ignored_ext:
                continue
            if suffix in preferred_ext:
                return path

        for path in sorted(search_dir.iterdir()):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix in ignored_ext:
                continue
            if suffix in preferred_ext:
                return path

        raise DownloadError("Downloaded audio file was not found")

    def _transcode(self, source_file: Path, output_format: str, quality: str, work_dir: Path) -> Path:
        output_file = work_dir / f"converted.{output_format}"

        codec_args: list[str]
        if output_format == "mp3":
            codec_args = ["-c:a", "libmp3lame", "-b:a", f"{quality}k"]
        elif output_format == "m4a":
            codec_args = ["-c:a", "aac", "-b:a", f"{quality}k", "-movflags", "+faststart"]
        elif output_format == "flac":
            codec_args = ["-c:a", "flac"]
        else:
            raise DownloadError(f"Unsupported output format: {output_format}")

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source_file),
            "-vn",
            "-map_metadata",
            "-1",
            *codec_args,
            str(output_file),
        ]

        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            stderr_tail = (completed.stderr or "")[-500:]
            raise DownloadError(f"ffmpeg failed: {stderr_tail.strip()}")
        if not output_file.exists():
            raise DownloadError("Transcoded file is missing")

        return output_file

    def _fetch_cover_bytes(self, info: dict[str, Any], thumbnail_url: str | None) -> bytes | None:
        thumbnail = self._clean_text(info.get("thumbnail")) or thumbnail_url
        if not thumbnail:
            return None

        try:
            response = requests.get(
                thumbnail,
                timeout=self._settings.http_timeout_seconds,
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.RequestException:
            return None

        content = response.content
        if not content:
            return None
        if len(content) > 8 * 1024 * 1024:
            return None
        return content

    def _apply_tags(
        self,
        file_path: Path,
        output_format: str,
        metadata: MetadataPreview,
        cover_bytes: bytes | None,
    ) -> None:
        if output_format == "mp3":
            self._tag_mp3(file_path=file_path, metadata=metadata, cover_bytes=cover_bytes)
            return
        if output_format == "flac":
            self._tag_flac(file_path=file_path, metadata=metadata, cover_bytes=cover_bytes)
            return
        if output_format == "m4a":
            self._tag_m4a(file_path=file_path, metadata=metadata, cover_bytes=cover_bytes)
            return
        raise DownloadError(f"Unsupported output format for tagging: {output_format}")

    def _tag_mp3(self, file_path: Path, metadata: MetadataPreview, cover_bytes: bytes | None) -> None:
        tags = ID3()
        tags.add(TIT2(encoding=3, text=metadata.title or "Untitled"))
        tags.add(TPE1(encoding=3, text=metadata.artist or "Unknown Artist"))
        tags.add(TALB(encoding=3, text=metadata.album or "Singles"))

        if metadata.track:
            tags.add(TRCK(encoding=3, text=str(metadata.track)))
        if metadata.year:
            tags.add(TDRC(encoding=3, text=str(metadata.year)))
        if metadata.genre:
            tags.add(TCON(encoding=3, text=metadata.genre))
        if metadata.comment:
            tags.add(COMM(encoding=3, lang="eng", desc="comment", text=metadata.comment))

        if cover_bytes:
            tags.add(
                APIC(
                    encoding=3,
                    mime=self._detect_image_mime(cover_bytes),
                    type=3,
                    desc="cover",
                    data=cover_bytes,
                )
            )

        tags.save(str(file_path))

    def _tag_flac(self, file_path: Path, metadata: MetadataPreview, cover_bytes: bytes | None) -> None:
        tags = FLAC(str(file_path))
        tags["title"] = metadata.title or "Untitled"
        tags["artist"] = metadata.artist or "Unknown Artist"
        tags["album"] = metadata.album or "Singles"

        if metadata.track:
            tags["tracknumber"] = str(metadata.track)
        if metadata.year:
            tags["date"] = str(metadata.year)
        if metadata.genre:
            tags["genre"] = metadata.genre
        if metadata.comment:
            tags["comment"] = metadata.comment

        if cover_bytes:
            picture = Picture()
            picture.type = 3
            picture.mime = self._detect_image_mime(cover_bytes)
            picture.data = cover_bytes
            tags.clear_pictures()
            tags.add_picture(picture)

        tags.save()

    def _tag_m4a(self, file_path: Path, metadata: MetadataPreview, cover_bytes: bytes | None) -> None:
        tags = MP4(str(file_path))
        tags["\xa9nam"] = [metadata.title or "Untitled"]
        tags["\xa9ART"] = [metadata.artist or "Unknown Artist"]
        tags["\xa9alb"] = [metadata.album or "Singles"]

        if metadata.track:
            tags["trkn"] = [(metadata.track, 0)]
        if metadata.year:
            tags["\xa9day"] = [str(metadata.year)]
        if metadata.genre:
            tags["\xa9gen"] = [metadata.genre]
        if metadata.comment:
            tags["\xa9cmt"] = [metadata.comment]

        if cover_bytes:
            if self._detect_image_mime(cover_bytes) == "image/png":
                cover = MP4Cover(cover_bytes, imageformat=MP4Cover.FORMAT_PNG)
            else:
                cover = MP4Cover(cover_bytes, imageformat=MP4Cover.FORMAT_JPEG)
            tags["covr"] = [cover]

        tags.save()

    def _move_to_library(self, source_file: Path, output_format: str, metadata: MetadataPreview) -> Path:
        artist_dir_name = sanitize_filename(metadata.artist or "Unknown Artist")
        album_dir_name = sanitize_filename(metadata.album or "Singles")

        title_name = sanitize_filename(metadata.title or "Untitled")
        track_prefix = ""
        if metadata.track:
            track_prefix = f"{metadata.track:02d} - "

        destination_dir = self._settings.output_root / artist_dir_name / album_dir_name
        destination_dir.mkdir(parents=True, exist_ok=True)

        base_name = f"{track_prefix}{title_name}.{output_format}"
        destination = unique_path(destination_dir / base_name)

        shutil.move(str(source_file), str(destination))
        return destination

    def _trigger_navidrome_scan(self) -> bool:
        if not self._settings.navidrome_scan_url:
            return False

        headers: dict[str, str] = {}
        if self._settings.navidrome_scan_token:
            token = self._settings.navidrome_scan_token
            if self._settings.navidrome_scan_header.lower() == "authorization" and not token.lower().startswith("bearer "):
                token = f"Bearer {token}"
            headers[self._settings.navidrome_scan_header] = token

        try:
            response = requests.post(
                self._settings.navidrome_scan_url,
                headers=headers,
                timeout=self._settings.http_timeout_seconds,
            )
            return 200 <= response.status_code < 300
        except requests.RequestException:
            return False

    def _normalize_metadata(self, info: dict[str, Any], url: str) -> MetadataPreview:
        source = detect_source(url=url, extractor_name=self._clean_text(info.get("extractor")))
        description = self._clean_text(info.get("description"))
        upload_date = self._clean_text(info.get("upload_date"))

        year: int | None = None
        if upload_date and len(upload_date) >= 4 and upload_date[:4].isdigit():
            year = int(upload_date[:4])

        raw_track = info.get("track_number")
        track: int | None = None
        if isinstance(raw_track, int):
            track = raw_track
        elif isinstance(raw_track, str) and raw_track.isdigit():
            track = int(raw_track)

        return MetadataPreview(
            source=source,
            url=url,
            source_id=self._clean_text(info.get("id")),
            title=self._clean_text(info.get("track")) or self._clean_text(info.get("title")),
            artist=(
                self._clean_text(info.get("artist"))
                or self._clean_text(info.get("uploader"))
                or self._clean_text(info.get("channel"))
                or self._clean_text(info.get("creator"))
            ),
            album=self._clean_text(info.get("album")),
            year=year,
            track=track,
            genre=self._pick_genre(info),
            comment=description,
            duration_seconds=self._coerce_duration(info.get("duration")),
            upload_date=upload_date,
            thumbnail_url=self._clean_text(info.get("thumbnail")),
            description=description,
        )

    def _merge_metadata(self, provider: MetadataPreview, overrides: MetadataOverrides) -> MetadataPreview:
        merged = provider.model_copy(deep=True)

        merged.title = self._pick_override(overrides.title, merged.title) or "Untitled"
        merged.artist = self._pick_override(overrides.artist, merged.artist) or "Unknown Artist"
        merged.album = self._pick_override(overrides.album, merged.album) or "Singles"

        if overrides.year is not None:
            merged.year = overrides.year
        if overrides.track is not None:
            merged.track = overrides.track
        if overrides.genre is not None:
            merged.genre = overrides.genre.strip() or None
        if overrides.comment is not None:
            merged.comment = overrides.comment.strip() or None

        return merged

    def _pick_single_entry(self, info: Any) -> dict[str, Any]:
        if isinstance(info, dict) and "entries" in info and isinstance(info["entries"], list):
            for entry in info["entries"]:
                if isinstance(entry, dict):
                    return entry
            raise DownloadError("Playlist URL has no downloadable entries")
        if isinstance(info, dict):
            return info
        raise DownloadError("Unsupported metadata payload")

    def _coerce_duration(self, value: Any) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        return None

    def _pick_genre(self, info: dict[str, Any]) -> str | None:
        direct = self._clean_text(info.get("genre"))
        if direct:
            return direct

        categories = info.get("categories")
        if isinstance(categories, list):
            for category in categories:
                if isinstance(category, str) and category.strip():
                    return category.strip()
        return None

    def _pick_override(self, override: str | None, base: str | None) -> str | None:
        if override is None:
            return base
        cleaned = override.strip()
        if cleaned:
            return cleaned
        return None

    def _clean_text(self, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        cleaned = value.strip()
        return cleaned or None

    def _detect_image_mime(self, blob: bytes) -> str:
        if blob.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        return "image/jpeg"


def detect_source(url: str, extractor_name: str | None = None) -> SourcePlatform:
    hostname = urlparse(url).netloc.lower()
    extractor = (extractor_name or "").lower()

    if any(token in hostname for token in ("youtube.com", "youtu.be")) or "youtube" in extractor:
        return SourcePlatform.youtube
    if "rutube.ru" in hostname or "rutube" in extractor:
        return SourcePlatform.rutube
    if "soundcloud.com" in hostname or "soundcloud" in extractor:
        return SourcePlatform.soundcloud
    if any(token in hostname for token in ("vk.com", "vkvideo.ru", "vk.ru")) or extractor.startswith("vk"):
        return SourcePlatform.vk
    return SourcePlatform.unknown


def sanitize_filename(value: str) -> str:
    sanitized = re.sub(r"[\\/:*?\"<>|]", "_", value)
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" .")
    if not sanitized:
        return "untitled"
    return sanitized[:160]


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    index = 2
    while True:
        candidate = path.with_name(f"{stem} ({index}){suffix}")
        if not candidate.exists():
            return candidate
        index += 1

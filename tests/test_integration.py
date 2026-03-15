"""Integration tests with real YouTube/SoundCloud links.

These tests make real network requests and download actual audio files.
They are marked with @pytest.mark.integration and can be skipped with:
    pytest -m "not integration"
"""
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import downloader as dl
from downloader import DownloadRequest
from main import app, _jobs


# ── Markers configuration ─────────────────────────────────────────────────────

pytestmark = pytest.mark.integration


# ── Helper ────────────────────────────────────────────────────────────────────

def _clear_jobs():
    _jobs.clear()


# ── Downloader Integration Tests ─────────────────────────────────────────────

class TestDownloaderIntegration:
    """Test actual downloads from real platforms."""

    @pytest.mark.parametrize(
        "url,title,artist",
        [
            # Short music videos / live sets
            (
                "https://www.youtube.com/watch?v=5qap5dO4i9A",
                "lofi hip hop radio",
                "Lofi Girl",
            ),
            # DJ sets and Boiler Room videos
            (
                "https://www.youtube.com/watch?v=U33WyaqNzQI",
                None,  # Let yt-dlp extract title
                None,  # Let yt-dlp extract artist
            ),
        ],
        ids=["lofi-radio", "dj-set"]
    )
    def test_download_real_youtube_video(
        self, temp_music_dir, url, title, artist
    ):
        """Test downloading and processing real YouTube videos."""
        with patch.dict(os.environ, {"OUTPUT_DIR": str(temp_music_dir)}):
            with patch("downloader.OUTPUT_DIR", str(temp_music_dir)):
                req = DownloadRequest(
                    url=url,
                    title=title,
                    artist=artist,
                )
                result_filename = dl.download_and_process(req)

        # Verify file was created
        output_file = temp_music_dir / result_filename
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        assert output_file.suffix == ".mp3"

    def test_download_with_trim(self, temp_music_dir):
        """Test downloading with time trimming on a real video."""
        with patch.dict(os.environ, {"OUTPUT_DIR": str(temp_music_dir)}):
            with patch("downloader.OUTPUT_DIR", str(temp_music_dir)):
                req = DownloadRequest(
                    url="https://www.youtube.com/watch?v=5qap5dO4i9A",
                    start_time="0:30",
                    end_time="1:00",
                    title="Lofi Trim Test",
                )
                result_filename = dl.download_and_process(req)

        output_file = temp_music_dir / result_filename
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_download_with_custom_metadata(self, temp_music_dir):
        """Test that custom metadata is properly embedded."""
        custom_title = "Custom Title Test"
        custom_artist = "Custom Artist"
        custom_album = "Custom Album"

        with patch.dict(os.environ, {"OUTPUT_DIR": str(temp_music_dir)}):
            with patch("downloader.OUTPUT_DIR", str(temp_music_dir)):
                req = DownloadRequest(
                    url="https://www.youtube.com/watch?v=5qap5dO4i9A",
                    title=custom_title,
                    artist=custom_artist,
                    album=custom_album,
                )
                result_filename = dl.download_and_process(req)

        output_file = temp_music_dir / result_filename
        assert output_file.exists()

        # Verify ID3 tags were written
        from mutagen.mp3 import MP3
        audio = MP3(str(output_file))
        assert audio.tags is not None
        assert custom_title in str(audio.tags.get("TIT2", ""))


# ── API Integration Tests ────────────────────────────────────────────────────

class TestAPIIntegration:
    """Test the full API flow with real downloads."""

    def setup_method(self):
        _clear_jobs()

    def test_full_download_workflow(self, temp_music_dir, monkeypatch):
        """Test the complete download workflow via API."""
        # Set output directory
        monkeypatch.setenv("OUTPUT_DIR", str(temp_music_dir))
        monkeypatch.setattr(dl, "OUTPUT_DIR", str(temp_music_dir))

        client = TestClient(app, raise_server_exceptions=False)

        # Start a download job
        response = client.post("/api/download", json={
            "url": "https://www.youtube.com/watch?v=5qap5dO4i9A",
            "title": "API Test Download",
        })

        assert response.status_code == 202
        job_id = response.json()["job_id"]
        assert job_id is not None

        # Poll for job completion (with timeout)
        import time
        max_attempts = 30
        for _ in range(max_attempts):
            status_response = client.get(f"/api/jobs/{job_id}")
            status = status_response.json()["status"]

            if status in ("done", "error"):
                break

            time.sleep(1)

        # Verify job completed successfully
        final_status = client.get(f"/api/jobs/{job_id}").json()
        assert final_status["status"] == "done"
        assert "API Test Download" in final_status["message"]

        # Verify file exists
        output_file = temp_music_dir / final_status["file"]
        assert output_file.exists()

    def test_waveform_generation(self, temp_music_dir, monkeypatch):
        """Test waveform generation for a real video."""
        monkeypatch.setenv("OUTPUT_DIR", str(temp_music_dir))

        client = TestClient(app, raise_server_exceptions=False)

        # Generate waveform for a real video
        response = client.get(
            "/api/waveform/test-video-id",
            params={"url": "https://www.youtube.com/watch?v=5qap5dO4i9A"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "peaks" in data
        assert "duration" in data
        assert "video_id" in data
        assert len(data["peaks"]) > 0
        assert data["duration"] > 0


# ── Platform-Specific Tests ──────────────────────────────────────────────────

class TestPlatformSupport:
    """Test downloads from different platforms."""

    @pytest.mark.parametrize(
        "url,platform_name",
        [
            # YouTube - various content types
            (
                "https://www.youtube.com/watch?v=5qap5dO4i9A",
                "YouTube-Lofi",
            ),
            # YouTube - DJ sets / live performances
            (
                "https://www.youtube.com/watch?v=DS0l-I4V0Hk",
                "YouTube-DJ-Set",
            ),
            # YouTube - short music content
            (
                "https://www.youtube.com/watch?v=jfKfPfyJRdk",
                "YouTube-Lofi-2",
            ),
        ],
        ids=lambda x: x[1]
    )
    def test_download_from_platform(
        self, temp_music_dir, url, platform_name
    ):
        """Test downloading from various platforms/content types."""
        with patch.dict(os.environ, {"OUTPUT_DIR": str(temp_music_dir)}):
            with patch("downloader.OUTPUT_DIR", str(temp_music_dir)):
                req = DownloadRequest(
                    url=url,
                    title=f"Test - {platform_name}",
                )
                result_filename = dl.download_and_process(req)

        output_file = temp_music_dir / result_filename
        assert output_file.exists()
        assert output_file.stat().st_size > 1000  # At least 1KB

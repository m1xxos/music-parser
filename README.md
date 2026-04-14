# Navidrome Music Downloader

Self-hosted web application for downloading audio and writing metadata tags for Navidrome.

Supported sources:

- YouTube
- RuTube
- SoundCloud
- VK Video

Supported output formats:

- MP3
- M4A
- FLAC

## Features

- URL metadata preview before download
- Metadata overrides (title, artist, album, year, track, genre, comment)
- Audio transcoding through ffmpeg
- Tag writing via mutagen, including cover art embedding
- Library layout compatible with Navidrome: `Artist/Album/Track`
- Optional Navidrome scan trigger after successful download
- Nothing-inspired UI with dark/light modes

## Quick start

```bash
docker compose up --build
```

Application URLs:

- Downloader UI: [http://localhost:8080](http://localhost:8080)
- Navidrome: [http://localhost:4533](http://localhost:4533)

The form is prefilled with this sample URL:

- [https://www.youtube.com/watch?v=hb0XLX0b4Y4](https://www.youtube.com/watch?v=hb0XLX0b4Y4)

## Configuration

Environment variables for the downloader service:

- `OUTPUT_ROOT` (default `/data/music`)
- `TMP_ROOT` (default `/data/tmp`)
- `DEFAULT_AUDIO_FORMAT` (`mp3|m4a|flac`)
- `DEFAULT_AUDIO_QUALITY` (`128|192|256|320`)
- `HTTP_TIMEOUT_SECONDS` (default `20`)
- `NAVIDROME_SCAN_URL` (optional; if empty, no API scan trigger)
- `NAVIDROME_SCAN_TOKEN` (optional)
- `NAVIDROME_SCAN_HEADER` (default `Authorization`)

If `NAVIDROME_SCAN_URL` is configured, the downloader sends `POST` after each successful job.

## Docker image publishing (GHCR)

On every push, GitHub Actions builds `Dockerfile` and publishes the image to GitHub Container Registry for this repository:

- `ghcr.io/m1xxos/music-parser:latest` for the default branch
- `ghcr.io/m1xxos/music-parser:<branch-name>` for branch pushes
- `ghcr.io/m1xxos/music-parser:sha-<commit-sha>` for each commit

Example pull command:

```bash
docker pull ghcr.io/m1xxos/music-parser:latest
```

## API

- `GET /api/health`
- `POST /api/metadata`
- `POST /api/jobs`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /media/...` for generated files

## Local run (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

## Important

Use this project only for media that you own or have permission to download.

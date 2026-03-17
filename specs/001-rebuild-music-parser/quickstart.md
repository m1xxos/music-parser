# Quickstart: Music Parser Full Rebuild

## Goal

Run the rebuilt application locally using a single Dockerfile workflow.

## Prerequisites

- Docker installed and running
- A writable local directory for exported music files

## Build Image

```bash
docker build -t music-parser:rebuild /Users/m1xxos/projects/music-parser
```

## Run Container

```bash
mkdir -p /Users/m1xxos/projects/music-parser/music
docker run --rm \
  -p 8000:8000 \
  -v /Users/m1xxos/projects/music-parser/music:/music \
  -e OUTPUT_DIR=/music \
  --name music-parser-rebuild \
  music-parser:rebuild
```

## Access Application

- Open `http://localhost:8000`
- Paste a YouTube, SoundCloud, or RuTube URL
- Apply optional trim/metadata edits
- Start parse job and observe progress bar
- Download output from results panel

## Health Check

```bash
curl -fsS http://localhost:8000/ >/dev/null && echo "healthy"
```

## Expected Artifacts

- Exported files in `/Users/m1xxos/projects/music-parser/music`
- Job status and history visible in UI results view

## Troubleshooting

- If no output appears, verify the host volume path exists and is writable.
- If a source URL fails, confirm it is publicly accessible and supported.
- If progress appears stalled, refresh the job detail panel and check terminal
  logs for provider or media-processing errors.

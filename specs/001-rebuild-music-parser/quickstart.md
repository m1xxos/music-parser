# Quickstart: Music Parser Full Rebuild

## Build and run (single Dockerfile)

```bash
docker build -t music-parser:rebuild /Users/m1xxos/projects/music-parser
mkdir -p /Users/m1xxos/projects/music-parser/music
docker run --rm \
  -p 8000:8000 \
  -v /Users/m1xxos/projects/music-parser/music:/music \
  -e OUTPUT_DIR=/music \
  --name music-parser-rebuild \
  music-parser:rebuild
```

## Validate API and UI

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/api/v1/history
open http://localhost:8000
```

## End-to-end walkthrough

1. Open the web app and submit a YouTube/SoundCloud/RuTube URL.
2. Optionally set trim start/end and metadata overrides.
3. Watch progress updates in the timeline (SSE-based updates every stage).
4. Confirm completed artifact appears with download action.
5. (Expert mode) Create a preset and submit batch URLs.
6. Verify downloaded artifact exists in `music/` host directory.

## Troubleshooting

- If parsing fails immediately, verify source URL is public and supported.
- If no file appears in host folder, check mount path and container logs.
- If UI is stale, hard-refresh browser cache after rebuilding image.

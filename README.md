# Music Parser

Minimal automatic music downloader for:
- YouTube
- SoundCloud
- RuTube

Paste a list of links, run batch download, get MP3 files with ID3 metadata (title/artist/album) suitable for Navidrome.

The app also copies finished files to an Omnivore import folder.

## Quick start

1. Copy env file:

```bash
cp stack.env.example stack.env
```

2. Run:

```bash
docker compose -f compose.yaml up --build
```

3. Open UI:

`http://localhost:8000`

## Folders

- `MUSIC_DIR` -> mounted to `/music` (Navidrome library source)
- `OMNIVORE_IMPORT_HOST_DIR` -> mounted to `/omnivore/inbox` (Omnivore import folder)

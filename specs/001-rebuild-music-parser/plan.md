# Implementation Plan: Music Parser Full Rebuild

**Branch**: `001-rebuild-music-parser` | **Date**: 2026-03-17 | **Spec**: `/Users/m1xxos/projects/music-parser/specs/001-rebuild-music-parser/spec.md`
**Input**: Feature specification from `/specs/001-rebuild-music-parser/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Rebuild the music parser into a polished web product that supports YouTube,
SoundCloud, and RuTube ingestion, trim/edit workflows, metadata enrichment,
clear progress reporting, and strong result visibility. The implementation uses
a modular adapter-based backend, asynchronous job execution with streaming
progress updates, persistent job/result history, and a minimal-but-powerful UI.
Delivery target is a single Dockerfile-based runtime workflow.

## Technical Context

**Language/Version**: Python 3.12 + TypeScript (ES2022)  
**Primary Dependencies**: FastAPI, yt-dlp, ffmpeg, mutagen, Preact, Vite  
**Storage**: SQLite for job/result history + filesystem for exported audio files  
**Testing**: pytest, pytest-asyncio, API contract tests, UI integration smoke tests  
**Target Platform**: Linux container runtime (Docker)  
**Project Type**: Web application (API backend + SPA frontend)  
**Performance Goals**: 95% of jobs show progress updates every <=5s; first parse completion under 4 minutes for 95% of first-time users  
**Constraints**: Single Dockerfile delivery; progress bar for long tasks; multi-source support (YouTube/SoundCloud/RuTube); minimal but feature-rich UI  
**Scale/Scope**: Single-operator to small-team usage, up to 20 concurrent active jobs per instance

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Multi-source ingestion impact is defined (YouTube, SoundCloud, RuTube) and
  includes adapter/change boundaries.
- Audio editing + metadata enrichment impact is defined (trim/edit + title,
  artist, album minimum support).
- Long-running operations (>3s) define async execution and progress reporting
  (API states + UI progress bar/equivalent).
- Docker-first runtime impact is documented and includes containerized
  validation approach.
- UX plan includes both discoverability path (new users) and efficiency path
  (power users) while preserving a minimal visual design.

### Gate Assessment (Pre-Design)

- ✅ Multi-source ingestion: adapters planned for YouTube/SoundCloud/RuTube.
- ✅ Edit/metadata pipeline: trim + metadata editor required in main flow.
- ✅ Long-task transparency: async jobs + SSE status stream + UI progress bar.
- ✅ Docker-first runtime: single Dockerfile build/run as baseline workflow.
- ✅ UX balance: guided default flow + optional advanced workspace tools.

### Gate Assessment (Post-Design)

- ✅ Data model includes provider boundaries, edit profile, and result history.
- ✅ API contracts define progress and terminal states.
- ✅ Quickstart defines Dockerized run path as first-class usage.
- ✅ Design keeps advanced controls optional and non-blocking for core flow.

## Project Structure

### Documentation (this feature)

```text
specs/001-rebuild-music-parser/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
app/
├── api/
│   ├── routes/
│   └── schemas/
├── domain/
│   ├── models/
│   └── services/
├── adapters/
│   ├── youtube/
│   ├── soundcloud/
│   └── rutube/
├── jobs/
│   ├── queue/
│   ├── progress/
│   └── persistence/
├── media/
│   ├── trim/
│   └── metadata/
└── static/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── stores/
│   └── services/
└── public/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Web application split into backend (`app/`) and
frontend (`frontend/`) for a clear UX/API boundary while keeping single-image
deployment through a multi-stage Dockerfile that bundles frontend assets into
backend static output.

## Complexity Tracking

No constitution violations identified.

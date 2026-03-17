# Research: Music Parser Full Rebuild

## Decision 1: Progress transport for long-running jobs

- Decision: Use Server-Sent Events (SSE) for live progress streaming, with a
  fallback polling endpoint for degraded clients.
- Rationale: Progress is server-to-client only, so SSE is simpler than
  bidirectional channels while giving near-real-time updates needed for progress
  bars and status timelines.
- Alternatives considered:
  - Polling-only: simpler but noisier and less responsive.
  - WebSockets: flexible but unnecessary complexity for one-way updates.

## Decision 2: Job and result persistence

- Decision: Persist job metadata and recent result history in SQLite, while
  keeping short-lived hot state in memory for immediate UI reads.
- Rationale: Provides recovery after restart and stable result pages without
  requiring an additional service, and fits single-container deployment.
- Alternatives considered:
  - In-memory only: loses history on restart.
  - External cache/database: better scale but violates simplicity target.

## Decision 3: Backend architecture

- Decision: Keep a modular monolith with explicit provider adapters for
  YouTube, SoundCloud, and RuTube.
- Rationale: Enforces constitution requirement for provider isolation while
  avoiding distributed-system overhead during rebuild.
- Alternatives considered:
  - Direct provider logic in route handlers: faster initially but brittle.
  - Separate microservices per provider: operationally heavy for current scope.

## Decision 4: UI approach for "minimal + powerful"

- Decision: Use a lightweight SPA with a guided primary flow and collapsible
  advanced controls (batch actions, presets, quick-repeat options).
- Rationale: Supports intuitive first-run usage while preserving power-user
  efficiency and richer feature depth.
- Alternatives considered:
  - Server-rendered pages only: simpler, but weaker interaction model for live
    progress and result dashboards.
  - Heavy dashboard-first UX: high power, poor approachability for new users.

## Decision 5: Single Dockerfile delivery

- Decision: Use one multi-stage Dockerfile that builds frontend assets and runs
  backend API/static delivery in a single runtime image.
- Rationale: Satisfies the requirement to end with one Dockerfile while still
  allowing modern frontend tooling and optimized runtime size.
- Alternatives considered:
  - Separate frontend/backend containers: cleaner separation but not aligned
    with single-Dockerfile delivery requirement.
  - Runtime frontend build: slower startup and less reproducible.

## Decision 6: Container runtime filesystem and safety

- Decision: Use `/tmp` for transient processing files and mounted `/music` for
  durable exports, run as non-root, and expose a health endpoint.
- Rationale: Supports media workflows safely, isolates temporary files, and
  preserves user outputs across container restarts.
- Alternatives considered:
  - All output in container layer: not durable.
  - Root execution with broad permissions: avoidable security risk.

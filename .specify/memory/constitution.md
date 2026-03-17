<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles:
  - Principle slot 1 -> I. Multi-Source Ingestion Is Mandatory
  - Principle slot 2 -> II. Audio Editing and Metadata Enrichment Are Core Features
  - Principle slot 3 -> III. Long-Running Work MUST Expose Progress
  - Principle slot 4 -> IV. Docker-First Delivery
  - Principle slot 5 -> V. Power-With-Clarity UX
- Added sections:
  - Product & Platform Constraints
  - Delivery Workflow & Quality Gates
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ updated: .specify/templates/plan-template.md
  - ✅ updated: .specify/templates/spec-template.md
  - ✅ updated: .specify/templates/tasks-template.md
  - ⚠ pending (directory absent): .specify/templates/commands/*.md
- Follow-up TODOs:
  - TODO(RATIFICATION_DATE): Original adoption date is unknown from repository history.
-->
# Music Parser Constitution

## Core Principles

### I. Multi-Source Ingestion Is Mandatory
The product MUST support parsing from YouTube, SoundCloud, and RuTube as
first-class sources. Source handling MUST be implemented through explicit
adapters so provider-specific failures cannot break unrelated providers.
Rationale: the project goal is a "swiss army knife" parser, which requires
broad and resilient source coverage by design.

### II. Audio Editing and Metadata Enrichment Are Core Features
Every parsing workflow MUST support trimming/editing and metadata updates
(at minimum title, artist, and album) before final export. Any new ingest flow
MUST remain compatible with this editing/enrichment pipeline. Rationale:
download-only behavior does not satisfy the product's core value proposition.

### III. Long-Running Work MUST Expose Progress
Any operation expected to exceed 3 seconds MUST run asynchronously and expose
machine-readable progress states plus user-facing progress indicators (progress
bar or equivalent). Progress events MUST include terminal states: success,
error, and cancellation when supported. Rationale: long media operations are
common and must remain transparent and controllable.

### IV. Docker-First Delivery
The application MUST run via Docker and Docker Compose with reproducible setup
for local and deployment environments. Changes to runtime dependencies MUST be
validated in containerized execution, not only host execution. Rationale:
container-first delivery minimizes environment drift for media tooling.

### V. Power-With-Clarity UX
The UI MUST stay visually minimal and intuitive while exposing advanced
capabilities without hiding them from expert users. Feature additions MUST
define both discoverability behavior (for first-time users) and efficiency
behavior (for repeated users). Rationale: the target experience is "simple
to start, deep to master."

## Product & Platform Constraints

- API contracts for job status and progress MUST be stable and documented.
- Output artifacts MUST preserve edited metadata and deterministic filenames.
- Failure modes (provider unavailable, ffmpeg failure, invalid timestamps) MUST
  return explicit errors suitable for UI display.
- The default local stack MUST be launchable with a single Compose command.

## Delivery Workflow & Quality Gates

1. Every feature spec MUST include:
   - source coverage impact (YouTube/SoundCloud/RuTube),
   - editing/metadata impact,
   - UX impact (novice + power-user paths),
   - Docker/runtime impact.
2. Every implementation plan MUST pass the Constitution Check before design and
   again before task generation.
3. Tasks for long-running operations MUST include explicit progress state work
   in backend and UI.
4. Merge readiness requires tests appropriate to change scope and at least one
   Dockerized validation path for runtime-affecting changes.

## Governance

This constitution supersedes conflicting project habits and templates.
Amendments require: (1) a written proposal, (2) explicit semantic version bump
decision (MAJOR/MINOR/PATCH), (3) update of impacted templates, and (4) a Sync
Impact Report in the constitution commit.

Versioning policy:
- MAJOR: Principle removal, principle redefinition, or governance changes that
  break prior compliance expectations.
- MINOR: New principle/section or materially expanded mandatory guidance.
- PATCH: Clarifications, wording improvements, and non-semantic refinements.

Compliance review expectations:
- Every plan and task artifact MUST cite how constitution gates are satisfied
  or document justified exceptions in a complexity/compliance section.
- Reviewers MUST block merges that violate MUST clauses without approved
  amendment.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): Original adoption date unknown | **Last Amended**: 2026-03-17

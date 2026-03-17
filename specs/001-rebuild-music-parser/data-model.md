# Data Model: Music Parser Full Rebuild

## Entity: SourceJob

- Purpose: Tracks one parse request from submission to completion.
- Fields:
  - `id` (string, UUID, required)
  - `source_url` (string, required)
  - `source_platform` (enum: `youtube|soundcloud|rutube`, required)
  - `status` (enum: `queued|fetching|processing|tagging|completed|failed|canceled`, required)
  - `progress_percent` (integer 0..100, required)
  - `status_message` (string, required)
  - `error_code` (string, optional)
  - `error_detail` (string, optional)
  - `created_at` (datetime, required)
  - `updated_at` (datetime, required)
  - `completed_at` (datetime, optional)
- Validation Rules:
  - `source_url` must be non-empty and valid URL format.
  - `progress_percent` must be monotonic unless job transitions to `failed` or `canceled`.
  - Terminal states (`completed|failed|canceled`) require `completed_at`.

## Entity: MediaDescriptor

- Purpose: Canonical source metadata shown before export.
- Fields:
  - `job_id` (FK -> SourceJob.id, required)
  - `source_media_id` (string, required)
  - `title` (string, required)
  - `creator` (string, optional)
  - `duration_seconds` (integer, required)
  - `thumbnail_url` (string, optional)
  - `fetched_at` (datetime, required)
- Validation Rules:
  - `duration_seconds` > 0.
  - `source_media_id` must be unique per platform.

## Entity: EditProfile

- Purpose: User-defined trim and metadata edits for export.
- Fields:
  - `job_id` (FK -> SourceJob.id, required)
  - `trim_start_seconds` (number, optional, default 0)
  - `trim_end_seconds` (number, optional)
  - `title_override` (string, optional)
  - `artist_override` (string, optional)
  - `album_override` (string, optional)
  - `extra_tags` (map<string,string>, optional)
- Validation Rules:
  - `trim_start_seconds >= 0`.
  - If `trim_end_seconds` is provided, it must be greater than `trim_start_seconds`.
  - Overrides must be sanitized for output naming and metadata writing.

## Entity: ExportArtifact

- Purpose: Represents final output file generated from a job.
- Fields:
  - `id` (string, UUID, required)
  - `job_id` (FK -> SourceJob.id, required)
  - `filename` (string, required)
  - `format` (enum: `mp3`, required for current scope)
  - `size_bytes` (integer, required)
  - `duration_seconds` (number, required)
  - `storage_path` (string, required)
  - `download_token` (string, optional)
  - `created_at` (datetime, required)
- Validation Rules:
  - `filename` conflict resolution must be non-destructive.
  - `storage_path` must resolve under configured output directory.

## Entity: ResultEntry

- Purpose: UI-ready summary for current and recent jobs.
- Fields:
  - `job_id` (FK -> SourceJob.id, required)
  - `status` (enum mirror of SourceJob.status, required)
  - `summary` (string, required)
  - `artifact_id` (FK -> ExportArtifact.id, optional)
  - `last_viewed_at` (datetime, optional)
- Validation Rules:
  - `artifact_id` required when status is `completed`.
  - Failed jobs must include non-empty failure summary.

## Relationships

- SourceJob 1:1 MediaDescriptor
- SourceJob 1:1 EditProfile
- SourceJob 1:0..1 ExportArtifact
- SourceJob 1:1 ResultEntry

## State Transitions (SourceJob)

- `queued -> fetching -> processing -> tagging -> completed`
- `queued|fetching|processing|tagging -> failed`
- `queued|fetching|processing|tagging -> canceled`
- Terminal states cannot transition to non-terminal states.

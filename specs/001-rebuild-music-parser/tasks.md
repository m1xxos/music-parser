# Tasks: Music Parser Full Rebuild

**Input**: Design documents from `/specs/001-rebuild-music-parser/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests were not explicitly requested in the feature specification, so this task list focuses on implementation and executable validation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `app/` (backend), `frontend/` (UI), `tests/` (validation suites)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and baseline structure for rebuild.

- [ ] T001 Create backend and frontend directory skeleton from plan in `app/` and `frontend/src/`
- [ ] T002 Initialize frontend workspace and build scripts in `frontend/package.json`
- [ ] T003 [P] Add frontend TypeScript + Vite config in `frontend/tsconfig.json` and `frontend/vite.config.ts`
- [ ] T004 [P] Add UI base styles and design tokens in `frontend/src/styles.css`
- [ ] T005 Add backend settings module for runtime config in `app/config.py`
- [ ] T006 [P] Add shared domain constants for statuses/providers in `app/domain/constants.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T007 Implement SQLite schema/bootstrap for jobs/results in `app/jobs/persistence/sqlite_store.py`
- [ ] T008 [P] Implement in-memory hot cache for active jobs in `app/jobs/persistence/cache_store.py`
- [ ] T009 Implement repository layer combining SQLite + cache in `app/jobs/persistence/job_repository.py`
- [ ] T010 [P] Implement provider adapter interface and registry in `app/adapters/base.py` and `app/adapters/registry.py`
- [ ] T011 [P] Implement YouTube adapter scaffold in `app/adapters/youtube/adapter.py`
- [ ] T012 [P] Implement SoundCloud adapter scaffold in `app/adapters/soundcloud/adapter.py`
- [ ] T013 [P] Implement RuTube adapter scaffold in `app/adapters/rutube/adapter.py`
- [ ] T014 Implement async job orchestrator and queue flow in `app/jobs/queue/orchestrator.py`
- [ ] T015 [P] Implement SSE progress publisher for job events in `app/jobs/progress/sse.py`
- [ ] T016 Implement global API error mapping and responses in `app/api/error_handlers.py`
- [ ] T017 Implement v1 API router composition in `app/api/routes/__init__.py`
- [ ] T018 Create single-Dockerfile multi-stage build with frontend bundle copy in `./Dockerfile`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Fast Parse and Export (Priority: P1) 🎯 MVP

**Goal**: Users can parse supported URLs, trim media, edit metadata, and export audio in one guided flow.

**Independent Test**: Submit a supported URL, apply trim + metadata edits, and download a correctly named output file.

### Implementation for User Story 1

- [ ] T019 [US1] Implement media descriptor model and validators in `app/domain/models/media_descriptor.py`
- [ ] T020 [US1] Implement edit profile model and trim validation in `app/domain/models/edit_profile.py`
- [ ] T021 [US1] Implement export artifact model and naming policy in `app/domain/models/export_artifact.py`
- [ ] T022 [US1] Implement metadata enrichment service in `app/media/metadata/service.py`
- [ ] T023 [US1] Implement audio trim/edit service in `app/media/trim/service.py`
- [ ] T024 [US1] Implement parse execution service integrating adapters + media pipeline in `app/domain/services/parse_service.py`
- [ ] T025 [US1] Implement create-job API endpoint from contract in `app/api/routes/jobs_create.py`
- [ ] T026 [US1] Implement job status API endpoint from contract in `app/api/routes/jobs_status.py`
- [ ] T027 [US1] Implement file download endpoint and token guard in `app/api/routes/downloads.py`
- [ ] T028 [US1] Implement guided parse form page in `frontend/src/pages/ParsePage.tsx`
- [ ] T029 [US1] Implement metadata + trim editor component in `frontend/src/components/EditPanel.tsx`
- [ ] T030 [US1] Implement parse submission service client in `frontend/src/services/jobs.ts`
- [ ] T031 [US1] Implement initial results card with download action in `frontend/src/components/ResultCard.tsx`
- [ ] T032 [US1] Wire US1 route and page composition in `frontend/src/main.tsx`

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Clear Progress and Results View (Priority: P2)

**Goal**: Users can monitor long jobs in real time and review consolidated completion results.

**Independent Test**: Start a long parse operation and observe continuously updated progress with final result details in one view.

### Implementation for User Story 2

- [ ] T033 [US2] Implement source job model state-transition guards in `app/domain/models/source_job.py`
- [ ] T034 [US2] Implement result entry summary model in `app/domain/models/result_entry.py`
- [ ] T035 [US2] Implement SSE job events endpoint from contract in `app/api/routes/jobs_events.py`
- [ ] T036 [US2] Implement job-result endpoint from contract in `app/api/routes/jobs_result.py`
- [ ] T037 [US2] Implement recent history endpoint from contract in `app/api/routes/history.py`
- [ ] T038 [US2] Implement progress timeline UI component with SSE subscription in `frontend/src/components/ProgressTimeline.tsx`
- [ ] T039 [US2] Implement results summary page for completed/failed jobs in `frontend/src/pages/ResultsPage.tsx`
- [ ] T040 [US2] Implement history panel component for recent jobs in `frontend/src/components/HistoryPanel.tsx`
- [ ] T041 [US2] Implement SSE client and reconnection strategy in `frontend/src/services/events.ts`
- [ ] T042 [US2] Wire job state store for live updates and terminal states in `frontend/src/stores/jobStore.ts`

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Intuitive Power-User Workspace (Priority: P3)

**Goal**: Returning users can complete repeated parsing tasks faster with advanced controls that do not hinder first-time usage.

**Independent Test**: Re-run multiple parses using presets/quick actions with fewer interactions while first-time users still complete core flow.

### Implementation for User Story 3

- [ ] T043 [US3] Implement preset profile entity and serialization in `app/domain/models/preset_profile.py`
- [ ] T044 [US3] Implement preset persistence service in `app/domain/services/preset_service.py`
- [ ] T045 [US3] Implement presets API routes for create/list/apply in `app/api/routes/presets.py`
- [ ] T046 [US3] Implement batch request model and validator in `app/domain/models/batch_request.py`
- [ ] T047 [US3] Implement batch parse orchestration service in `app/domain/services/batch_service.py`
- [ ] T048 [US3] Implement batch API endpoint for multi-URL submit in `app/api/routes/batch.py`
- [ ] T049 [US3] Implement advanced controls drawer component in `frontend/src/components/AdvancedDrawer.tsx`
- [ ] T050 [US3] Implement preset manager UI component in `frontend/src/components/PresetManager.tsx`
- [ ] T051 [US3] Implement batch submit panel with per-item status in `frontend/src/components/BatchPanel.tsx`
- [ ] T052 [US3] Implement first-run simplification and expert mode toggle in `frontend/src/stores/uiModeStore.ts`

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T053 [P] Update API contract to match implemented endpoints in `specs/001-rebuild-music-parser/contracts/api-contract.yaml`
- [ ] T054 [P] Add runtime observability logs for job lifecycle and errors in `app/jobs/queue/orchestrator.py` and `app/api/error_handlers.py`
- [ ] T055 Enforce deterministic output collision handling and sanitize rules in `app/media/metadata/service.py`
- [ ] T056 Validate single-Dockerfile local workflow and document final run commands in `specs/001-rebuild-music-parser/quickstart.md`
- [ ] T057 Validate constitution-aligned UX copy for guided and advanced flows in `frontend/src/pages/ParsePage.tsx` and `frontend/src/components/AdvancedDrawer.tsx`
- [ ] T058 Perform end-to-end quickstart walkthrough and capture fixes in `specs/001-rebuild-music-parser/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on Foundational completion and reuses US1 artifacts.
- **User Story 3 (Phase 5)**: Depends on Foundational completion and builds on US1/US2 patterns.
- **Polish (Phase 6)**: Depends on all target user stories being complete.

### User Story Dependencies

- **US1 (P1)**: First MVP slice; no dependency on other stories.
- **US2 (P2)**: Uses core job execution from US1 but remains independently testable.
- **US3 (P3)**: Extends workflows with power-user features while preserving US1 path.

### Parallel Opportunities

- Setup tasks marked `[P]` can run concurrently (`T003`, `T004`, `T006`).
- Foundational adapter scaffolds can run concurrently (`T011`, `T012`, `T013`).
- US1 backend domain tasks can run in parallel after models are set (`T022`, `T023`).
- US2 UI tasks can run in parallel after event client is available (`T039`, `T040`, `T042`).
- US3 UI tasks can run in parallel after preset/batch APIs exist (`T049`, `T050`, `T051`).
- Polish tasks `T053` and `T054` can run in parallel.

---

## Parallel Example: User Story 1

```bash
Task: "T022 [US1] Implement metadata enrichment service in app/media/metadata/service.py"
Task: "T023 [US1] Implement audio trim/edit service in app/media/trim/service.py"
Task: "T029 [US1] Implement metadata + trim editor component in frontend/src/components/EditPanel.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "T039 [US2] Implement results summary page in frontend/src/pages/ResultsPage.tsx"
Task: "T040 [US2] Implement history panel component in frontend/src/components/HistoryPanel.tsx"
Task: "T042 [US2] Wire job state store in frontend/src/stores/jobStore.ts"
```

## Parallel Example: User Story 3

```bash
Task: "T049 [US3] Implement advanced controls drawer in frontend/src/components/AdvancedDrawer.tsx"
Task: "T050 [US3] Implement preset manager in frontend/src/components/PresetManager.tsx"
Task: "T051 [US3] Implement batch submit panel in frontend/src/components/BatchPanel.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate independent test for US1 end-to-end parse/export flow.
5. Demo MVP before expanding.

### Incremental Delivery

1. Ship US1 as core parser workflow.
2. Add US2 for real-time transparency and results clarity.
3. Add US3 for power-user productivity features.
4. Finish with Phase 6 polish and Docker workflow validation.

### Parallel Team Strategy

1. Team finalizes Setup + Foundational together.
2. Then split:
   - Developer A: US1 flow hardening.
   - Developer B: US2 progress/results UX.
   - Developer C: US3 presets/batch workspace.
3. Rejoin for Phase 6 integration and quickstart verification.

---

## Notes

- All tasks use strict checklist format with checkbox, task ID, optional `[P]`, story label when required, and exact file path.
- User-story phases are independently testable increments aligned with spec priorities (P1 → P2 → P3).
- Suggested MVP scope is **Phase 1 + Phase 2 + Phase 3 (US1)**.

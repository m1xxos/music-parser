from fastapi import APIRouter

def build_v1_router(orchestrator, repository, sse_publisher, preset_service, batch_service, settings):
    from app.api.routes import jobs_create, jobs_status, downloads, jobs_events, jobs_result, history, presets, batch
    jobs_create.router.orchestrator = orchestrator
    jobs_status.router.repository = repository
    downloads.router.repository = repository
    jobs_events.router.sse_publisher = sse_publisher
    jobs_result.router.repository = repository
    jobs_result.router.settings = settings
    history.router.repository = repository
    presets.router.preset_service = preset_service
    batch.router.batch_service = batch_service
    router = APIRouter(prefix=settings.api_prefix)
    for r in [jobs_create.router, jobs_status.router, jobs_events.router, jobs_result.router, history.router, downloads.router, presets.router, batch.router]:
        router.include_router(r)
    return router

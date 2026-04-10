import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.adapters.registry import AdapterRegistry
from app.adapters.youtube.adapter import YouTubeAdapter
from app.adapters.soundcloud.adapter import SoundCloudAdapter
from app.adapters.rutube.adapter import RuTubeAdapter
from app.api.error_handlers import register_error_handlers
from app.api.routes import build_v1_router
from app.config import settings
from app.domain.services.batch_service import BatchService
from app.domain.services.parse_service import ParseService
from app.domain.services.preset_service import PresetService
from app.jobs.persistence.cache_store import CacheStore
from app.jobs.persistence.job_repository import JobRepository
from app.jobs.persistence.sqlite_store import SQLiteStore
from app.jobs.progress.sse import SsePublisher
from app.jobs.queue.orchestrator import JobOrchestrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
app = FastAPI(title='Music Parser API', version='1.0.0')
sqlite = SQLiteStore(settings.sqlite_path)
cache = CacheStore()
repository = JobRepository(sqlite, cache)
registry = AdapterRegistry(); registry.register(YouTubeAdapter()); registry.register(SoundCloudAdapter()); registry.register(RuTubeAdapter())
parse_service = ParseService(registry, settings.output_dir, settings.omnivore_import_dir)
sse = SsePublisher()
orchestrator = JobOrchestrator(repository, parse_service, sse)
preset_service = PresetService(repository)
batch_service = BatchService(orchestrator)
app.include_router(build_v1_router(orchestrator, repository, sse, preset_service, batch_service, settings))
register_error_handlers(app)

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.on_event('startup')
async def startup():
    await orchestrator.start()

static_dir = Path(__file__).parent / 'static'
if static_dir.exists():
    app.mount('/', StaticFiles(directory=str(static_dir), html=True), name='static')

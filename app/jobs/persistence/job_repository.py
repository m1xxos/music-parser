import json
from app.jobs.persistence.cache_store import CacheStore
from app.jobs.persistence.sqlite_store import SQLiteStore

class JobRepository:
    def __init__(self, sqlite_store: SQLiteStore, cache_store: CacheStore):
        self.sqlite = sqlite_store
        self.cache = cache_store

    def upsert_job(self, job: dict) -> None:
        self.cache.set(job['id'], job)
        self.sqlite.execute(
            '''
            INSERT INTO jobs(id,source_url,source_platform,status,progress_percent,status_message,error_code,error_detail,created_at,updated_at,completed_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              status=excluded.status,
              progress_percent=excluded.progress_percent,
              status_message=excluded.status_message,
              error_code=excluded.error_code,
              error_detail=excluded.error_detail,
              updated_at=excluded.updated_at,
              completed_at=excluded.completed_at
            ''',
            (job['id'], job['source_url'], job['source_platform'], job['status'], job['progress_percent'], job['status_message'], job.get('error_code'), job.get('error_detail'), job['created_at'], job['updated_at'], job.get('completed_at'))
        )

    def get_job(self, job_id: str) -> dict | None:
        if cached := self.cache.get(job_id):
            return cached
        row = self.sqlite.fetchone('SELECT * FROM jobs WHERE id=?', (job_id,))
        return dict(row) if row else None

    def list_history(self, limit: int = 20) -> list[dict]:
        return [dict(r) for r in self.sqlite.fetchall('SELECT * FROM jobs ORDER BY updated_at DESC LIMIT ?', (limit,))]

    def save_artifact(self, artifact: dict) -> None:
        self.sqlite.execute('INSERT INTO artifacts(id,job_id,filename,format,size_bytes,duration_seconds,storage_path,download_token,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
            (artifact['id'], artifact['job_id'], artifact['filename'], artifact['format'], artifact['size_bytes'], artifact['duration_seconds'], artifact['storage_path'], artifact.get('download_token'), artifact['created_at']))

    def get_artifact_by_job(self, job_id: str) -> dict | None:
        row=self.sqlite.fetchone('SELECT * FROM artifacts WHERE job_id=? ORDER BY created_at DESC LIMIT 1', (job_id,))
        return dict(row) if row else None

    def save_preset(self, preset: dict) -> None:
        self.sqlite.execute('INSERT INTO presets(id,name,trim_start_seconds,trim_end_seconds,metadata_json,created_at) VALUES(?,?,?,?,?,?)',
            (preset['id'], preset['name'], preset['trim_start_seconds'], preset.get('trim_end_seconds'), json.dumps(preset.get('metadata',{})), preset['created_at']))

    def list_presets(self):
        rows=self.sqlite.fetchall('SELECT * FROM presets ORDER BY created_at DESC')
        out=[]
        for row in rows:
            item=dict(row)
            item['metadata']=json.loads(item.pop('metadata_json'))
            out.append(item)
        return out

    def get_preset(self,preset_id:str):
        row=self.sqlite.fetchone('SELECT * FROM presets WHERE id=?',(preset_id,))
        if not row:
            return None
        item=dict(row)
        item['metadata']=json.loads(item.pop('metadata_json'))
        return item

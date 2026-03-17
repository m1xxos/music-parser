class CacheStore:
    def __init__(self):
        self._jobs: dict[str, dict] = {}

    def set(self, job_id: str, payload: dict) -> None:
        self._jobs[job_id] = payload

    def get(self, job_id: str) -> dict | None:
        return self._jobs.get(job_id)

    def delete(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

import asyncio
import json

class SsePublisher:
    def __init__(self):
        self._queues: dict[str, list[asyncio.Queue]] = {}

    async def publish(self, job_id: str, event: dict) -> None:
        for queue in self._queues.get(job_id, []):
            await queue.put(event)

    async def stream(self, job_id: str):
        queue = asyncio.Queue()
        self._queues.setdefault(job_id, []).append(queue)
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event.get('status') in {'completed', 'failed', 'canceled'}:
                    break
        finally:
            self._queues[job_id].remove(queue)

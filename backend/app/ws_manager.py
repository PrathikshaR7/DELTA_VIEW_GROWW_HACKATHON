import asyncio
import json

from fastapi import WebSocket

from app.redis_client import get_redis, UPDATES_CHANNEL


class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()
        self._listener_task: asyncio.Task | None = None

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)
        if self._listener_task is None:
            self._listener_task = asyncio.create_task(self._listen_redis())

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def _listen_redis(self):
        r = get_redis()
        pubsub = r.pubsub()
        pubsub.subscribe(UPDATES_CHANNEL)
        loop = asyncio.get_event_loop()
        while True:
            message = await loop.run_in_executor(
                None, pubsub.get_message, True, 1.0
            )
            if message and message.get("type") == "message":
                await self._broadcast(message["data"])
            await asyncio.sleep(0.05)

    async def _broadcast(self, data: str):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()

import asyncio


class LiveHub:
    def __init__(self):
        self._connections = set()
        self._loop = None

    def set_loop(self, loop):
        self._loop = loop

    async def connect(self, websocket):
        await websocket.accept()
        self._connections.add(websocket)
        await websocket.send_json({"type": "connected"})

    def disconnect(self, websocket):
        self._connections.discard(websocket)

    async def broadcast(self, payload):
        stale = []

        for websocket in list(self._connections):
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.append(websocket)

        for websocket in stale:
            self.disconnect(websocket)

    def publish(self, payload):
        if not self._loop or not self._loop.is_running():
            return

        asyncio.run_coroutine_threadsafe(
            self.broadcast(payload),
            self._loop,
        )


live_hub = LiveHub()

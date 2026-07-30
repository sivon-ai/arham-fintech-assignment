from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.live import live_hub

router = APIRouter(tags=["Live"])


@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket):
    await live_hub.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        live_hub.disconnect(websocket)

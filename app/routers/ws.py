from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket import manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws/tasks")
async def websocket_tasks(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
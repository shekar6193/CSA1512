from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.notification_service import notification_hub

router = APIRouter(tags=["Real-time WebSockets"])

@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time incident event stream and live updates.
    """
    await notification_hub.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for ping/client messages
            data = await websocket.receive_text()
            # Echo back pong or acknowledge
            if data == "ping":
                await websocket.send_text('{"event": "pong"}')
    except WebSocketDisconnect:
        notification_hub.disconnect(websocket)
    except Exception:
        notification_hub.disconnect(websocket)

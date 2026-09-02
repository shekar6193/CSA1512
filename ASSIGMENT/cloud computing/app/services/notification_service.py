import json
from typing import List, Dict, Any
from fastapi import WebSocket

class NotificationHub:
    """
    WebSocket Connection Manager and Real-time Campus Event Dispatcher.
    Broadcasts live incident updates, emergency dispatches, and status changes.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, payload: Dict[str, Any]):
        message = {
            "event": event_type,
            "data": payload
        }
        # Iterate over copy to prevent mutation issues during disconnection
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception:
                self.disconnect(connection)

    def get_active_count(self) -> int:
        return len(self.active_connections)

notification_hub = NotificationHub()

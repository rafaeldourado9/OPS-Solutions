import json
from typing import Any
from uuid import UUID

import structlog
from fastapi import WebSocket

from core.ports.outbound.notification_port import NotificationPort

logger = structlog.get_logger()


class ConnectionManager(NotificationPort):
    """Manages tenant-scoped WebSocket connections for real-time updates."""

    def __init__(self) -> None:
        # tenant_id -> list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, tenant_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        key = str(tenant_id)
        if key not in self._connections:
            self._connections[key] = []
        self._connections[key].append(websocket)
        logger.debug("ws_connected", tenant_id=key, total=len(self._connections[key]))

    def disconnect(self, tenant_id: UUID, websocket: WebSocket) -> None:
        key = str(tenant_id)
        if key in self._connections:
            self._connections[key] = [ws for ws in self._connections[key] if ws is not websocket]
            if not self._connections[key]:
                del self._connections[key]
        logger.debug("ws_disconnected", tenant_id=key)

    async def push_to_tenant(self, tenant_id: UUID, event_type: str, data: dict[str, Any]) -> None:
        key = str(tenant_id)
        connections = self._connections.get(key, [])
        if not connections:
            return

        message = json.dumps({"type": event_type, "data": data})
        dead: list[WebSocket] = []

        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            self.disconnect(tenant_id, ws)

    def active_connections_count(self, tenant_id: UUID) -> int:
        return len(self._connections.get(str(tenant_id), []))

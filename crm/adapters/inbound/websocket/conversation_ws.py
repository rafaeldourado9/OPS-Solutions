from uuid import UUID

import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from infrastructure.security import decode_access_token

logger = structlog.get_logger()

router = APIRouter()


@router.websocket("/ws/conversations")
async def conversations_websocket(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket for real-time conversation updates.
    Authenticate via JWT in query parameter.

    Server pushes events:
    - new_message: {chat_id, message: {id, role, content, sender_name, created_at}}
    - new_conversation: {conversation}
    - takeover_started: {chat_id, operator}
    - takeover_ended: {chat_id}
    - conversation_updated: {chat_id, data}
    """
    # Validate JWT
    try:
        payload = decode_access_token(token)
        tenant_id = UUID(payload["tenant_id"])
        user_id = UUID(payload["sub"])
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Get connection manager from app state
    manager = websocket.app.state.ws_manager

    await manager.connect(tenant_id, websocket)
    logger.info("ws_conversation_connected", tenant_id=str(tenant_id), user_id=str(user_id))

    try:
        while True:
            # Listen for client messages (mark_read, etc.)
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "mark_read":
                # Could update unread_count here
                pass
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(tenant_id, websocket)
        logger.info("ws_conversation_disconnected", tenant_id=str(tenant_id))
    except Exception as e:
        manager.disconnect(tenant_id, websocket)
        logger.error("ws_error", error=str(e))

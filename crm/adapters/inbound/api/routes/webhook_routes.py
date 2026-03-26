from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request

from adapters.inbound.api.dependencies import get_handle_gateway_proxy_uc, get_receive_agent_event_uc
from core.domain.events import InboundAgentEvent
from core.use_cases.conversations.handle_gateway_proxy import HandleGatewayProxyUseCase
from core.use_cases.conversations.receive_agent_event import ReceiveAgentEventUseCase

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/agent-events")
async def receive_agent_events(
    request: Request,
    uc: ReceiveAgentEventUseCase = Depends(get_receive_agent_event_uc),
):
    """Receives CRM events from agents CRMEventAdapter (fire-and-forget POST)."""
    body: dict[str, Any] = await request.json()

    event = InboundAgentEvent(
        event_type=body.get("event_type", ""),
        chat_id=body.get("chat_id", ""),
        agent_id=body.get("agent_id", ""),
        data=body.get("data", {}),
    )
    await uc.execute(event)
    return {"status": "ok"}


@router.post("/gateway-proxy")
async def gateway_proxy(
    request: Request,
    uc: HandleGatewayProxyUseCase = Depends(get_handle_gateway_proxy_uc),
):
    """
    Gateway webhook proxy. All gateway messages come here first.
    Checks takeover state and either intercepts or forwards to agents.
    """
    payload: dict[str, Any] = await request.json()
    result = await uc.execute(payload)
    return result

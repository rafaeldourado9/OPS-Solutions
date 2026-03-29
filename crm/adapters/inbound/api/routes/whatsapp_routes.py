"""
WhatsApp Numbers API — manage multiple WhatsApp numbers per tenant.

Each number maps to a gateway session and optionally to a specific agent.
"""

import asyncio
import os
import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from adapters.outbound.agents.whatsapp_status_adapter import get_whatsapp_adapter
from adapters.outbound.persistence.database import get_session
from adapters.outbound.persistence.repositories.pg_whatsapp_number_repository import PgWhatsAppNumberRepository
from core.domain.whatsapp_number import WhatsAppNumber

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])


async def _sync_agent_session(agent_id: str, session_name: str) -> None:
    """Write waha_session into business.yml and reload the agent process."""
    try:
        import httpx
        from adapters.outbound.agents.filesystem_agent_config import FilesystemAgentConfig
        from infrastructure.config import settings

        agents_dir = os.environ.get("AGENTS_DIR", "/app/shared-agents")
        config_port = FilesystemAgentConfig(agents_dir)
        if config_port.exists(agent_id):
            cfg = config_port.read(agent_id)
            cfg.setdefault("agent", {})["waha_session"] = session_name
            config_port.write(agent_id, cfg)

        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{settings.agents_api_url}/reload/{agent_id}")
    except Exception:
        logger.exception("Failed to sync waha_session for agent=%s session=%s", agent_id, session_name)


# --- Schemas ---

class AddNumberBody(BaseModel):
    label: Optional[str] = None
    agent_id: Optional[str] = None


class UpdateNumberBody(BaseModel):
    label: Optional[str] = None
    agent_id: Optional[str] = None


class NumberOut(BaseModel):
    id: str
    session_name: str
    phone_number: Optional[str] = None
    label: Optional[str] = None
    agent_id: Optional[str] = None
    is_active: bool = True
    status: str = "unknown"
    connected_at: Optional[str] = None
    created_at: Optional[str] = None


# --- Routes ---

@router.get("/numbers")
async def list_numbers(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    repo = PgWhatsAppNumberRepository(session)
    numbers = await repo.list_by_tenant(current_user.tenant_id)
    adapter = get_whatsapp_adapter()

    result = []
    for n in numbers:
        # Get live status from gateway
        try:
            status_data = await adapter.get_status(session=n.session_name)
            live_status = status_data.get("status", "unknown")
            phone = status_data.get("phone") or n.phone_number
        except Exception:
            live_status = "unknown"
            phone = n.phone_number

        result.append({
            "id": str(n.id),
            "session_name": n.session_name,
            "phone_number": phone,
            "label": n.label,
            "agent_id": n.agent_id,
            "is_active": n.is_active,
            "status": live_status,
            "connected_at": n.connected_at.isoformat() if n.connected_at else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        })
    return result


@router.post("/numbers", status_code=201)
async def add_number(
    body: AddNumberBody,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    repo = PgWhatsAppNumberRepository(session)

    # Generate unique session name scoped to tenant
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
    tenant_repo = PgTenantRepository(session)
    tenant = await tenant_repo.get_by_id(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    count = await repo.count_by_tenant(current_user.tenant_id)
    session_name = f"{tenant.slug}-wa-{count + 1}"

    # Create session on the gateway
    adapter = get_whatsapp_adapter()
    gw_result = await adapter.create_session(session_name)
    if gw_result.get("status") == "error":
        raise HTTPException(status_code=502, detail=f"Gateway error: {gw_result.get('error')}")

    # Persist in DB
    number = WhatsAppNumber.create(
        tenant_id=current_user.tenant_id,
        session_name=session_name,
        label=body.label,
        agent_id=body.agent_id,
    )
    await repo.save(number)

    # Write waha_session into the agent's business.yml so the agent registry
    # routes incoming webhooks for this session to the correct agent.
    effective_agent_id = body.agent_id or tenant.get_active_agent_id()
    if effective_agent_id:
        asyncio.create_task(_sync_agent_session(effective_agent_id, session_name))

    return {
        "id": str(number.id),
        "session_name": number.session_name,
        "phone_number": None,
        "label": number.label,
        "agent_id": number.agent_id,
        "is_active": True,
        "status": "connecting",
        "connected_at": None,
        "created_at": number.created_at.isoformat(),
    }


@router.delete("/numbers/{number_id}", status_code=204)
async def remove_number(
    number_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    repo = PgWhatsAppNumberRepository(session)
    number = await repo.get_by_id(UUID(number_id))
    if not number or number.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Número não encontrado")

    # Remove session from gateway
    adapter = get_whatsapp_adapter()
    await adapter.remove_session(number.session_name)

    # Remove from DB
    await repo.delete(number.id)


@router.get("/numbers/{number_id}/qr")
async def get_number_qr(
    number_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    repo = PgWhatsAppNumberRepository(session)
    number = await repo.get_by_id(UUID(number_id))
    if not number or number.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Número não encontrado")

    adapter = get_whatsapp_adapter()
    return await adapter.get_qr(session=number.session_name)


@router.get("/numbers/{number_id}/status")
async def get_number_status(
    number_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    repo = PgWhatsAppNumberRepository(session)
    number = await repo.get_by_id(UUID(number_id))
    if not number or number.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Número não encontrado")

    adapter = get_whatsapp_adapter()
    return await adapter.get_status(session=number.session_name)


@router.post("/numbers/{number_id}/restart")
async def restart_number(
    number_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    repo = PgWhatsAppNumberRepository(session)
    number = await repo.get_by_id(UUID(number_id))
    if not number or number.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Número não encontrado")

    adapter = get_whatsapp_adapter()
    return await adapter.restart(session=number.session_name)


@router.post("/numbers/{number_id}/logout")
async def logout_number(
    number_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    repo = PgWhatsAppNumberRepository(session)
    number = await repo.get_by_id(UUID(number_id))
    if not number or number.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Número não encontrado")

    adapter = get_whatsapp_adapter()
    return await adapter.logout(session=number.session_name)


@router.put("/numbers/{number_id}")
async def update_number(
    number_id: str,
    body: UpdateNumberBody,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    repo = PgWhatsAppNumberRepository(session)
    number = await repo.get_by_id(UUID(number_id))
    if not number or number.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Número não encontrado")

    if body.label is not None:
        number.label = body.label
    if body.agent_id is not None:
        number.agent_id = body.agent_id

    await repo.update(number)

    if body.agent_id is not None:
        asyncio.create_task(_sync_agent_session(body.agent_id, number.session_name))

    return {
        "id": str(number.id),
        "session_name": number.session_name,
        "phone_number": number.phone_number,
        "label": number.label,
        "agent_id": number.agent_id,
        "is_active": number.is_active,
    }

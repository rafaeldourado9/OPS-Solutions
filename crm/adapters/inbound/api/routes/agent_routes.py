import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

from adapters.inbound.api.dependencies import (
    get_delete_rag_document_uc,
    get_get_agent_config_uc,
    get_list_rag_documents_uc,
    get_update_agent_config_uc,
    get_upload_rag_document_uc,
    _get_agent_config_port,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from adapters.outbound.agents.whatsapp_status_adapter import get_whatsapp_adapter
from adapters.outbound.persistence.database import get_session
from core.ports.outbound.agent_config_port import AgentConfigPort
from core.use_cases.agents.delete_rag_document import DeleteRagDocumentRequest, DeleteRagDocumentUseCase
from core.use_cases.agents.get_agent_config import GetAgentConfigUseCase
from core.use_cases.agents.list_rag_documents import ListRagDocumentsUseCase
from core.use_cases.agents.update_agent_config import UpdateAgentConfigRequest, UpdateAgentConfigUseCase
from core.use_cases.agents.upload_rag_document import UploadRagDocumentRequest, UploadRagDocumentUseCase

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

GEMINI_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-3-flash-preview",
]


# --- Schemas ---

class AgentConfigUpdateBody(BaseModel):
    updates: dict


class CreateInstanceBody(BaseModel):
    agent_id: str
    name: Optional[str] = None
    company: Optional[str] = None
    persona: Optional[str] = None


class RagDocumentOut(BaseModel):
    name: str
    collection: str
    chunk_count: int
    ingested_at: str | None = None


# --- Config Routes ---

@router.get("/config")
async def get_agent_config(
    current_user: CurrentUser = Depends(get_current_user),
    uc: GetAgentConfigUseCase = Depends(get_get_agent_config_uc),
):
    try:
        config = await uc.execute(current_user.tenant_id)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Never expose the API key — replace it with a boolean sentinel
    import copy
    config = copy.deepcopy(config)
    llm = config.get("llm", {})
    raw_key = llm.pop("api_key", None)
    llm["api_key_set"] = bool(raw_key)
    config["llm"] = llm
    return config


@router.put("/config")
async def update_agent_config(
    body: AgentConfigUpdateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: UpdateAgentConfigUseCase = Depends(get_update_agent_config_uc),
):
    try:
        result = await uc.execute(UpdateAgentConfigRequest(
            tenant_id=current_user.tenant_id,
            updates=body.updates,
        ))
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Signal the running agent to reload its config from disk (fire-and-forget)
    import asyncio
    import httpx
    from infrastructure.config import settings

    async def _fire_reload():
        import structlog as _structlog
        _logger = _structlog.get_logger()
        try:
            from adapters.outbound.persistence.database import async_session_factory
            from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
            async with async_session_factory() as s:
                repo = PgTenantRepository(s)
                tenant = await repo.get_by_id(current_user.tenant_id)
                if tenant:
                    active_id = tenant.get_active_agent_id()
                    if active_id:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            resp = await client.post(f"{settings.agents_api_url}/reload/{active_id}")
                            if resp.status_code >= 400:
                                _logger.warning("agent_reload_failed", agent_id=active_id, status=resp.status_code, body=resp.text[:200])
                            else:
                                _logger.info("agent_reload_ok", agent_id=active_id)
        except Exception as exc:
            _logger.warning("agent_reload_error", error=str(exc))  # Fire-and-forget: log, never block save

    asyncio.create_task(_fire_reload())
    return result


# --- RAG Routes ---

@router.get("/rag/documents", response_model=list[RagDocumentOut])
async def list_rag_documents(
    agent_id: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListRagDocumentsUseCase = Depends(get_list_rag_documents_uc),
):
    try:
        docs = await uc.execute(current_user.tenant_id, agent_id=agent_id)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [
        RagDocumentOut(
            name=d.name,
            collection=d.collection,
            chunk_count=d.chunk_count,
            ingested_at=d.ingested_at.isoformat() if d.ingested_at else None,
        )
        for d in docs
    ]


@router.post("/rag/documents", response_model=RagDocumentOut, status_code=201)
async def upload_rag_document(
    doc_name: str = Form(""),
    agent_id: str = Form(""),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    uc: UploadRagDocumentUseCase = Depends(get_upload_rag_document_uc),
):
    content = await file.read()
    try:
        doc = await uc.execute(UploadRagDocumentRequest(
            tenant_id=current_user.tenant_id,
            filename=file.filename or "document",
            content=content,
            doc_name=doc_name,
            agent_id=agent_id or None,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("rag_upload_error", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

    return RagDocumentOut(
        name=doc.name,
        collection=doc.collection,
        chunk_count=doc.chunk_count,
        ingested_at=doc.ingested_at.isoformat() if doc.ingested_at else None,
    )


@router.delete("/rag/documents/{doc_name}", status_code=204)
async def delete_rag_document(
    doc_name: str,
    agent_id: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    uc: DeleteRagDocumentUseCase = Depends(get_delete_rag_document_uc),
):
    try:
        await uc.execute(DeleteRagDocumentRequest(
            tenant_id=current_user.tenant_id,
            doc_name=doc_name,
            agent_id=agent_id,
        ))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Instance Management Routes ---

@router.get("/instances")
async def list_instances(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
    config_port = _get_agent_config_port()
    tenant_repo = PgTenantRepository(session)
    tenant = await tenant_repo.get_by_id(current_user.tenant_id)
    if not tenant:
        return []

    # Only show agents owned by this tenant
    owned = tenant.get_owned_agents()
    active_id = tenant.get_active_agent_id()

    result = []
    for agent_id in owned:
        try:
            cfg = config_port.read(agent_id)
        except Exception:
            cfg = {}
        result.append({
            "agent_id": agent_id,
            "name": cfg.get("agent", {}).get("name", agent_id),
            "company": cfg.get("agent", {}).get("company", ""),
            "active": agent_id == active_id,
        })
    return result


@router.post("/instances", status_code=201)
async def create_instance(
    body: CreateInstanceBody,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    import re
    from sqlalchemy import select as sa_select
    from adapters.outbound.persistence.models.tenant_model import TenantModel
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository

    if not re.match(r'^[a-z0-9_-]+$', body.agent_id):
        raise HTTPException(status_code=400, detail="agent_id must be lowercase letters, numbers, hyphens, underscores only")

    # Fetch tenant to auto-populate company name
    result_tenant = await session.execute(sa_select(TenantModel).where(TenantModel.id == current_user.tenant_id))
    tenant_model_pre = result_tenant.scalar_one_or_none()
    auto_company = body.company or (tenant_model_pre.name if tenant_model_pre else "")
    auto_name = body.name or auto_company

    # Namespace agent_id with tenant slug to prevent cross-tenant collisions.
    # e.g. user types "mateus" → stored as "acme-mateus" (isolated per tenant)
    tenant_slug = tenant_model_pre.slug if tenant_model_pre else current_user.tenant_id[:8]
    namespaced_id = f"{tenant_slug}-{body.agent_id}"

    config_port = _get_agent_config_port()
    try:
        config_port.create_agent(
            namespaced_id,
            company_name=auto_company,
            agent_name=auto_name,
            persona=body.persona or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Register this agent as owned by this tenant
    result = await session.execute(sa_select(TenantModel).where(TenantModel.id == current_user.tenant_id))
    tenant_model = result.scalar_one_or_none()
    if tenant_model:
        current_settings = dict(tenant_model.settings or {})
        owned = list(current_settings.get("owned_agents") or [])
        is_first_agent = len(owned) == 0

        if namespaced_id not in owned:
            owned.append(namespaced_id)
        current_settings["owned_agents"] = owned
        tenant_model.settings = current_settings

        # If this is the first agent created, set it as the primary agent for the tenant
        if is_first_agent or not config_port.exists(tenant_model.agent_id or ""):
            tenant_model.agent_id = namespaced_id

        await session.commit()

    # Sync manifest + tell agent process to load this agent
    import asyncio
    import httpx
    from infrastructure.config import settings
    from adapters.inbound.api.main import sync_agent_manifest

    async def _fire_load():
        try:
            await sync_agent_manifest()

            # If tenant already has a WhatsApp number, bind its session to this agent
            from adapters.outbound.persistence.repositories.pg_whatsapp_number_repository import PgWhatsAppNumberRepository
            from adapters.outbound.persistence.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                number_repo = PgWhatsAppNumberRepository(db)
                numbers = await number_repo.list_by_tenant(current_user.tenant_id)
                if numbers:
                    wa_session = numbers[0].session_name
                    existing_cfg = config_port.read(namespaced_id)
                    existing_cfg.setdefault("agent", {})["waha_session"] = wa_session
                    config_port.write(namespaced_id, existing_cfg)

            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(f"{settings.agents_api_url}/load/{namespaced_id}")
        except Exception:
            pass

    asyncio.create_task(_fire_load())

    try:
        new_cfg = config_port.read(namespaced_id)
    except Exception:
        new_cfg = {}
    return {
        "agent_id": namespaced_id,
        "name": new_cfg.get("agent", {}).get("name", namespaced_id),
        "company": new_cfg.get("agent", {}).get("company", ""),
        "active": False,
    }


@router.delete("/instances/{agent_id}", status_code=204)
async def delete_instance(
    agent_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import select as sa_select
    from adapters.outbound.persistence.models.tenant_model import TenantModel
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository

    result = await session.execute(sa_select(TenantModel).where(TenantModel.id == current_user.tenant_id))
    tenant_model = result.scalar_one_or_none()
    if not tenant_model:
        raise HTTPException(status_code=404, detail="Tenant not found")

    current_settings = dict(tenant_model.settings or {})
    owned = list(current_settings.get("owned_agents") or [tenant_model.agent_id])

    # Security: only allow deleting agents this tenant owns
    if agent_id not in owned:
        raise HTTPException(status_code=403, detail="Agente não pertence a este tenant")

    # Cannot delete the primary registered agent
    if agent_id == tenant_model.agent_id:
        raise HTTPException(status_code=400, detail="Não é possível excluir o agente principal do tenant")

    # Cannot delete the currently active config
    active_id = current_settings.get("active_config_id") or tenant_model.agent_id
    if agent_id == active_id:
        raise HTTPException(status_code=400, detail="Não é possível excluir a instância ativa. Ative outra primeiro.")

    config_port = _get_agent_config_port()
    try:
        config_port.delete_agent(agent_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Remove from owned_agents
    owned = [a for a in owned if a != agent_id]
    current_settings["owned_agents"] = owned
    tenant_model.settings = current_settings
    await session.commit()

    # Sync manifest + tell agent process to unload
    import asyncio
    import httpx
    from infrastructure.config import settings
    from adapters.inbound.api.main import sync_agent_manifest

    async def _fire_unload():
        try:
            await sync_agent_manifest()
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.delete(f"{settings.agents_api_url}/unload/{agent_id}")
        except Exception:
            pass

    asyncio.create_task(_fire_unload())


@router.post("/instances/{agent_id}/activate")
async def activate_instance(
    agent_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from sqlalchemy import select as sa_select
    from adapters.outbound.persistence.models.tenant_model import TenantModel

    config_port = _get_agent_config_port()
    if not config_port.exists(agent_id):
        raise HTTPException(status_code=404, detail=f"Agente '{agent_id}' não encontrado")

    result = await session.execute(sa_select(TenantModel).where(TenantModel.id == current_user.tenant_id))
    tenant_model = result.scalar_one_or_none()
    if not tenant_model:
        raise HTTPException(status_code=404, detail="Tenant not found")

    current_settings = dict(tenant_model.settings or {})
    owned = list(current_settings.get("owned_agents") or [tenant_model.agent_id])

    # Security: only allow activating agents this tenant owns
    if agent_id not in owned:
        raise HTTPException(status_code=403, detail="Agente não pertence a este tenant")

    # Store active config in settings JSON — do NOT change tenant.agent_id
    # tenant.agent_id is the stable registered agent used for webhook routing
    current_settings["active_config_id"] = agent_id
    tenant_model.settings = current_settings
    await session.commit()

    # Signal the agent process to switch personas (fire-and-forget)
    import asyncio
    import httpx
    from infrastructure.config import settings

    async def _fire_set_active():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(f"{settings.agents_api_url}/set-active/{agent_id}")
        except Exception:
            pass

    asyncio.create_task(_fire_set_active())

    return {"agent_id": agent_id, "active": True}


# --- WhatsApp Routes ---

@router.get("/whatsapp/status")
async def get_whatsapp_status(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    adapter = get_whatsapp_adapter()
    return await adapter.get_status()


@router.get("/whatsapp/qr")
async def get_whatsapp_qr(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    adapter = get_whatsapp_adapter()
    return await adapter.get_qr()


@router.post("/whatsapp/restart")
async def restart_whatsapp(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    adapter = get_whatsapp_adapter()
    return await adapter.restart()


@router.post("/whatsapp/logout")
async def logout_whatsapp(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    adapter = get_whatsapp_adapter()
    return await adapter.logout()


# --- LLM Routes ---

@router.get("/llm/models")
async def list_llm_models(
    provider: str = "ollama",
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    if provider == "gemini":
        return {"provider": "gemini", "models": GEMINI_MODELS}
    adapter = get_whatsapp_adapter()
    models = await adapter.list_ollama_models()
    return {"provider": "ollama", "models": models}

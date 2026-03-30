import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.inbound.api.routes.auth_routes import router as auth_router
from adapters.inbound.api.routes.public_routes import router as public_router
from adapters.inbound.api.routes.conversation_routes import router as conversation_router
from adapters.inbound.api.routes.customer_routes import router as customer_router
from adapters.inbound.api.routes.health_routes import router as health_router
from adapters.inbound.api.routes.lead_routes import router as lead_router
from adapters.inbound.api.routes.agent_routes import router as agent_router
from adapters.inbound.api.routes.contract_routes import router as contract_router
from adapters.inbound.api.routes.contract_template_routes import router as contract_template_router
from adapters.inbound.api.routes.premise_routes import router as premise_router
from adapters.inbound.api.routes.product_routes import router as product_router
from adapters.inbound.api.routes.quote_routes import router as quote_router
from adapters.inbound.api.routes.quote_template_routes import router as quote_template_router
from adapters.inbound.api.routes.dashboard_routes import router as dashboard_router
from adapters.inbound.api.routes.webhook_routes import router as webhook_router
from adapters.inbound.api.routes.payment_routes import router as payment_router, _webhook_router as mp_webhook_router
from adapters.inbound.api.routes.user_routes import router as user_router
from adapters.inbound.websocket.connection_manager import ConnectionManager
from adapters.inbound.websocket.conversation_ws import router as ws_router
from adapters.inbound.api.routes.whatsapp_routes import router as whatsapp_router
import adapters.outbound.persistence.models  # noqa: F401 — registers all models with Base
from adapters.outbound.persistence.database import create_tables, engine
from infrastructure.logging import setup_logging

logger = structlog.get_logger()


_TRIAL_EXEMPT_PREFIXES = (
    "/api/v1/auth/",
    "/api/v1/health",
    "/api/v1/subscriptions/",
    "/webhooks/",
    "/ws/",
    "/health",
    "/docs",
    "/openapi",
)


async def _trial_check_middleware(request, call_next):
    """Return 402 when the authenticated tenant's trial has expired.

    Auth routes, webhooks and WebSocket endpoints are always exempt so the
    user can still reach settings / upgrade even after expiry.
    """
    from datetime import datetime
    from uuid import UUID

    from fastapi.responses import JSONResponse
    from sqlalchemy import select

    from adapters.outbound.persistence.database import async_session_factory
    from adapters.outbound.persistence.models.tenant_model import TenantModel
    from infrastructure.security import decode_access_token

    path = request.url.path
    if any(path.startswith(p) for p in _TRIAL_EXEMPT_PREFIXES):
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return await call_next(request)

    try:
        payload = decode_access_token(auth_header.split(" ", 1)[1])
        tenant_id = UUID(payload["tenant_id"])
    except Exception:
        return await call_next(request)

    async with async_session_factory() as session:
        result = await session.execute(
            select(TenantModel).where(TenantModel.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()

    if (
        tenant is not None
        and tenant.trial_ends_at is not None
        and tenant.trial_ends_at < datetime.utcnow()
    ):
        return JSONResponse(status_code=402, content={"detail": "trial_expired"})

    return await call_next(request)


async def sync_agent_manifest():
    """
    Write active-agents.json to the shared agents volume.

    The agent process reads this manifest to know which agents to load.
    Only agents owned by active tenants are included — this is the core
    of tenant-level agent isolation.
    """
    import json
    from pathlib import Path
    from sqlalchemy import select

    from adapters.outbound.persistence.database import async_session_factory
    from adapters.outbound.persistence.models.tenant_model import TenantModel
    from infrastructure.config import settings

    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(TenantModel).where(TenantModel.is_active == True)
            )
            tenants = result.scalars().all()

        agents_dir = Path(settings.agents_dir)

        # Write per-tenant manifest files — each tenant only loads its own agents
        all_agents: list[str] = []
        for t in tenants:
            owned = (t.settings or {}).get("owned_agents") or ([t.agent_id] if t.agent_id else [])
            owned = [a for a in owned if a]  # filter empty
            # Per-tenant manifest keyed by tenant ID
            per_tenant = agents_dir / f"active-agents-{t.id}.json"
            per_tenant.write_text(json.dumps(owned), encoding="utf-8")
            all_agents.extend(owned)

        # Global manifest (backward compat / unfiltered deployments)
        unique = list(dict.fromkeys(all_agents))
        manifest_path = agents_dir / "active-agents.json"
        manifest_path.write_text(json.dumps(unique), encoding="utf-8")
        logger.info("agent_manifest_synced", agents=unique, count=len(unique))
    except Exception as e:
        logger.error("agent_manifest_sync_failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("crm_starting")

    # Initialize WebSocket connection manager
    app.state.ws_manager = ConnectionManager()

    # Create tables on startup (dev convenience; production uses Alembic)
    try:
        await create_tables()
        logger.info("database_tables_created")
        # Migrate existing databases: add trial_ends_at if not present
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text(
                "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP"
            ))
            await conn.execute(text(
                "ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS last_inactivity_email_at TIMESTAMP"
            ))
            await conn.execute(text(
                "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS mp_subscription_id TEXT"
            ))
            await conn.execute(text(
                "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS mp_payer_email TEXT"
            ))
            await conn.execute(text(
                "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50)"
            ))
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT"
            ))
        logger.info("migration_trial_ends_at_done")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))

    # Sync agent manifest so the agent process knows which agents to load
    await sync_agent_manifest()

    # Start background tasks
    from tasks.trial_reminder_task import run_trial_reminder_loop
    from tasks.lead_reminder_task import run_lead_reminder_loop
    reminder_task = asyncio.create_task(run_trial_reminder_loop())
    lead_task = asyncio.create_task(run_lead_reminder_loop())

    yield

    # Shutdown
    reminder_task.cancel()
    lead_task.cancel()
    await engine.dispose()
    logger.info("crm_shutdown")


app = FastAPI(
    title="CRM White-Label API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(_trial_check_middleware)

app.include_router(health_router)
app.include_router(public_router)
app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(lead_router)
app.include_router(agent_router)
app.include_router(contract_router)
app.include_router(contract_template_router)
app.include_router(premise_router)
app.include_router(product_router)
app.include_router(quote_router)
app.include_router(quote_template_router)
app.include_router(conversation_router)
app.include_router(dashboard_router)
app.include_router(webhook_router)
app.include_router(payment_router)
app.include_router(mp_webhook_router)
app.include_router(user_router)
app.include_router(ws_router)
app.include_router(whatsapp_router)

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
from adapters.inbound.api.routes.premise_routes import router as premise_router
from adapters.inbound.api.routes.product_routes import router as product_router
from adapters.inbound.api.routes.quote_routes import router as quote_router
from adapters.inbound.api.routes.quote_template_routes import router as quote_template_router
from adapters.inbound.api.routes.dashboard_routes import router as dashboard_router
from adapters.inbound.api.routes.webhook_routes import router as webhook_router
from adapters.inbound.websocket.connection_manager import ConnectionManager
from adapters.inbound.websocket.conversation_ws import router as ws_router
import adapters.outbound.persistence.models  # noqa: F401 — registers all models with Base
from adapters.outbound.persistence.database import create_tables, engine
from infrastructure.logging import setup_logging

logger = structlog.get_logger()


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
    except Exception as e:
        logger.error("database_init_failed", error=str(e))

    yield

    # Shutdown
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

app.include_router(health_router)
app.include_router(public_router)
app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(lead_router)
app.include_router(agent_router)
app.include_router(contract_router)
app.include_router(premise_router)
app.include_router(product_router)
app.include_router(quote_router)
app.include_router(quote_template_router)
app.include_router(conversation_router)
app.include_router(dashboard_router)
app.include_router(webhook_router)
app.include_router(ws_router)

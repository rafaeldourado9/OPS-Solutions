"""
FastAPI application entry point for the WhatsApp agent framework.

Supports both single-agent and multi-agent modes:

  Single agent (default):
      AGENT_ID=empresa_x uvicorn api.main:app

  Multiple agents in one process:
      AGENT_IDS=empresa_x,empresa_y uvicorn api.main:app

Each agent has its own namespaced Redis debouncer, LLM, memory, and CRM.
WAHA webhooks are routed to the correct agent by session name.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from uuid import uuid4

import structlog

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.inbound.waha_webhook import router as webhook_router
from api.agent_registry import AgentInstance, AgentRegistry
from api.dependencies import build_agent_instance
from infrastructure.config_loader import get_config, load_config
from infrastructure.postgres import close_engine, create_tables
from infrastructure.rate_limiter import RateLimiter
from infrastructure.redis_client import (
    MessageDebouncer,
    close_redis,
    get_redis,
    listen_for_expired_keys,
)

_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
_LOG_JSON = os.environ.get("LOG_JSON", "false").lower() == "true"

logging.basicConfig(
    level=_LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# Configure structlog to wrap stdlib logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        (
            structlog.processors.JSONRenderer()
            if _LOG_JSON
            else structlog.dev.ConsoleRenderer()
        ),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Agent ID resolution
# ---------------------------------------------------------------------------


def _resolve_agent_ids() -> list[str]:
    """
    Return the list of agent IDs to load.

    Checks AGENT_IDS (comma-separated) first, then AGENT_ID, then 'empresa_x'.
    Special value "auto" scans the agents directory and loads all valid agents.
    """
    multi = os.environ.get("AGENT_IDS", "").strip()
    if multi and multi.lower() != "auto":
        return [a.strip() for a in multi.split(",") if a.strip()]

    if multi.lower() == "auto":
        return _auto_discover_agents()

    single = os.environ.get("AGENT_ID", "empresa_x").strip()
    return [single]


def _auto_discover_agents() -> list[str]:
    """
    Read the CRM-managed manifest to determine which agents to load.

    The CRM writes 'active-agents.json' to the shared agents directory whenever
    tenants create or delete agents.  This ensures only tenant-owned agents are
    loaded — no stale or test directories interfere.

    Manifest format:  ["tenant-slug-agent1", "tenant-slug-agent2", ...]

    Falls back to scanning the directory for agents with crm.enabled if the
    manifest does not exist (first boot before CRM has started).
    """
    import json as _json
    from infrastructure.config_loader import _agents_dir, load_config

    agents_path = _agents_dir()
    manifest = agents_path / "active-agents.json"

    if manifest.exists():
        try:
            agent_ids = _json.loads(manifest.read_text(encoding="utf-8"))
            # Validate each agent has a business.yml
            valid = [a for a in agent_ids if (agents_path / a / "business.yml").exists()]
            logger.info("Loaded %d agents from CRM manifest: %s", len(valid), valid)
            return valid
        except Exception as exc:
            logger.warning("Failed to read manifest — falling back to scan: %s", exc)

    # Fallback: scan directory for CRM-enabled agents
    if not agents_path.exists():
        logger.warning("Agents directory not found: %s", agents_path)
        return []

    skip = {"template", "__pycache__"}
    discovered = []
    for entry in sorted(agents_path.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith(".") or entry.name in skip:
            continue
        if not (entry / "business.yml").exists():
            continue
        try:
            cfg = load_config(entry.name)
            if cfg.crm.enabled:
                discovered.append(entry.name)
        except Exception as exc:
            logger.warning("Skipping agent '%s' — config error: %s", entry.name, exc)

    logger.info("Fallback scan found %d CRM-enabled agents: %s", len(discovered), discovered)
    return discovered


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise all agents, start keyspace listener, tear down on shutdown."""
    agent_ids = _resolve_agent_ids()
    logger.info("Starting agents: %s", agent_ids)

    # Initialise database tables once (shared by all agents)
    for attempt in range(3):
        try:
            await create_tables()
            logger.info("Database tables ready.")
            break
        except Exception:
            if attempt < 2:
                logger.warning(
                    "Database not ready (attempt %d/3) — retrying in 3s…", attempt + 1
                )
                await asyncio.sleep(3)
            else:
                logger.error(
                    "Could not create database tables after 3 attempts — "
                    "message history will not be persisted."
                )

    # Build all agent instances
    registry = AgentRegistry()
    agent_sessions_env = os.environ.get("AGENT_SESSION", "").strip()
    # Gateway session name — all agents share the same gateway session so that
    # incoming messages (which carry session="default") can be routed to them.
    gateway_session = agent_sessions_env or os.environ.get("SESSION_NAME", "default")
    redis_startup = await get_redis()
    for agent_id in agent_ids:
        try:
            config = get_config(agent_id)
            # Use the gateway session for all agents so webhook routing works.
            # Individual agents can override via waha_session in their config.
            session_override = config.agent.waha_session or gateway_session
            instance = await build_agent_instance(agent_id, config, session=session_override)
            registry.register(instance)

            # Check Redis for a persisted agent switch — restore it so restarts don't revert
            saved = await redis_startup.get(f"active_agent:{instance.session}")
            if saved:
                saved_id = saved.decode() if isinstance(saved, bytes) else saved
                if saved_id != agent_id:
                    try:
                        get_config.cache_clear()
                        saved_config = load_config(saved_id)
                        saved_instance = await build_agent_instance(saved_id, saved_config, session=instance.session)
                        registry.replace_agent(agent_id, saved_instance)
                        instance = saved_instance
                        config = saved_config
                        logger.info("Restored persisted agent switch: %s → %s", agent_id, saved_id)
                    except Exception:
                        logger.exception("Failed to restore saved agent '%s' — keeping '%s'", saved_id, agent_id)

            logger.info(
                "Agent ready: id=%s session=%s name=%s llm=%s/%s",
                instance.agent_id,
                instance.session,
                config.agent.name,
                config.llm.provider,
                config.llm.model,
            )
        except Exception:
            logger.exception("Failed to start agent '%s' — skipping", agent_id)

    if not registry.all_instances():
        raise RuntimeError("No agents could be started. Check configuration.")

    # Build rate limiter (shared across all agents — per chat_id)
    redis = await get_redis()
    rate_limiter = RateLimiter(
        redis=redis,
        max_messages=int(os.environ.get("RATE_LIMIT_MAX", "20")),
        window_seconds=int(os.environ.get("RATE_LIMIT_WINDOW", "60")),
    )

    # Start WebToolsAdapter (Playwright) for agents that have tools enabled
    for inst in registry.all_instances():
        wt = inst.web_tools
        if wt is not None:
            try:
                await wt.start()
                logger.info("WebToolsAdapter started for agent=%s", inst.agent_id)
            except Exception:
                logger.exception("Failed to start WebToolsAdapter for agent=%s", inst.agent_id)

    # Start proactive schedulers for agents that have it enabled
    from infrastructure.proactive_scheduler import ProactiveScheduler
    schedulers = []
    for inst in registry.all_instances():
        if getattr(inst.config, 'proactive', None) and inst.config.proactive.enabled:
            target_chats = inst.config.proactive.target_chat_ids or []
            use_llm = getattr(inst.config.proactive, 'daily_message_type', 'static') == 'llm'
            scheduler = ProactiveScheduler(
                agent_id=inst.agent_id,
                gateway=inst.gateway,
                activity_tracker=inst.activity_tracker,
                calendar=inst.calendar,
                config=inst.config.proactive,
                target_chat_ids=target_chats,
                llm=inst.primary_llm if use_llm else None,
                llm_system_prompt=inst.config.agent.persona if use_llm else "",
            )
            scheduler.start()
            schedulers.append(scheduler)
            logger.info("ProactiveScheduler started for agent=%s", inst.agent_id)

    # Store shared state
    app.state.registry = registry
    app.state.rate_limiter = rate_limiter
    app.state.waha_api_key = os.environ.get("WAHA_API_KEY", "")
    app.state.waha_url = os.environ.get("WAHA_URL", "http://localhost:3000")

    # Convenience attributes for single-agent backward compatibility
    first = registry.all_instances()[0]
    app.state.agent_id = first.agent_id
    app.state.config = first.config
    app.state.debouncer = first.debouncer
    app.state.process_message = first.process_message
    app.state.media = first.media

    # Store app reference for the keyspace callback
    _app_ref[0] = app

    # Start Redis keyspace expiry listener (one shared listener for all agents)
    listener_task = asyncio.create_task(
        listen_for_expired_keys(callback=_on_debounce_expired)
    )

    logger.info("All agents running. Registry size: %d", len(registry))
    yield

    # Shutdown
    logger.info("Shutting down %d agent(s).", len(registry))
    for scheduler in schedulers:
        scheduler.stop()
    for inst in registry.all_instances():
        if inst.web_tools is not None:
            try:
                await inst.web_tools.stop()
            except Exception:
                pass
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass
    await close_redis()
    await close_engine()
    logger.info("Shutdown complete.")


_app_ref: list = [None]


# ---------------------------------------------------------------------------
# Keyspace expiry callback
# ---------------------------------------------------------------------------


async def _on_debounce_expired(key: str) -> None:
    """
    Called when any Redis debounce key expires.

    Key format (namespaced):    debounce:{agent_id}:{chat_id}
    Key format (single-agent):  debounce:{chat_id}

    Routes the expired buffer to the correct agent's ProcessMessageUseCase.
    """
    if not key.startswith("debounce:"):
        return

    app = _app_ref[0]
    if app is None:
        return

    registry: AgentRegistry = app.state.registry
    rest = key[len("debounce:"):]  # "{agent_id}:{chat_id}" or "{chat_id}"

    # Try to find a matching agent by namespace prefix
    instance: AgentInstance | None = None
    chat_id: str = rest

    for inst in registry.all_instances():
        ns = inst.debouncer.namespace
        if ns and rest.startswith(f"{ns}:"):
            instance = inst
            chat_id = rest[len(ns) + 1:]
            break

    # Fallback for single-agent (no namespace in key)
    if instance is None:
        instance = registry.get_by_session(registry.all_instances()[0].session)

    if instance is None:
        return

    raw_messages = await instance.debouncer.get_and_clear_buffer(chat_id)
    if not raw_messages:
        return

    user_texts: list[str] = []
    push_name: str = ""
    for raw in raw_messages:
        try:
            parsed = json.loads(raw)
            text = parsed.get("text", "")
            if not push_name:
                push_name = parsed.get("push_name", "")
        except (json.JSONDecodeError, AttributeError):
            text = raw
        if text:
            user_texts.append(text)

    if not user_texts:
        return

    task_id = str(uuid4())
    logger.info(
        "Debounce expired: agent=%s chat_id=%s msgs=%d task=%s",
        instance.agent_id,
        chat_id,
        len(user_texts),
        task_id,
    )

    asyncio.create_task(
        instance.process_message.execute(
            agent_id=instance.agent_id,
            chat_id=chat_id,
            user_texts=user_texts,
            task_id=task_id,
            push_name=push_name,
        )
    )


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------


app = FastAPI(
    title="WhatsApp Agent Framework",
    description="Multi-tenant WhatsApp agent with hexagonal architecture.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router, tags=["webhook"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.post("/set-active/{agent_id}", tags=["admin"])
async def set_active_agent(agent_id: str) -> dict:
    """
    Make agent_id the active agent, replacing whoever is currently running.
    Does not need to know the current agent_id — reads it from the registry.
    Persists the choice in Redis so container restarts restore it.
    """
    from fastapi import HTTPException
    registry: AgentRegistry = getattr(app.state, "registry", None)
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not ready")

    instances = registry.all_instances()
    if not instances:
        raise HTTPException(status_code=503, detail="No agents running")

    current = instances[0]  # single-agent mode: always the first one

    get_config.cache_clear()
    new_config = load_config(agent_id)
    new_instance = await build_agent_instance(agent_id, new_config, session=current.session)

    if current.agent_id == agent_id:
        registry.replace(new_instance)
    else:
        registry.replace_agent(current.agent_id, new_instance)

    redis = await get_redis()
    await redis.set(f"active_agent:{current.session}", agent_id)

    app.state.agent_id = agent_id
    app.state.config = new_config
    app.state.debouncer = new_instance.debouncer
    app.state.process_message = new_instance.process_message
    app.state.media = new_instance.media

    logger.info("Active agent set: %s → %s (session=%s)", current.agent_id, agent_id, current.session)
    return {"status": "ok", "agent_id": agent_id, "name": new_config.agent.name}


@app.post("/load/{agent_id}", tags=["admin"])
async def load_agent(agent_id: str) -> dict:
    """
    Dynamically load a new agent into the registry without restarting.
    Called by the CRM when a tenant creates a new agent via onboarding.
    If the agent is already loaded, reloads its config instead.
    """
    from fastapi import HTTPException
    registry: AgentRegistry = getattr(app.state, "registry", None)
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not ready")

    # If already loaded, just reload
    existing = registry.get_by_agent_id(agent_id)
    if existing is not None:
        get_config.cache_clear()
        new_config = load_config(agent_id)
        new_instance = await build_agent_instance(agent_id, new_config, session=existing.session)
        registry.replace(new_instance)
        logger.info("Agent '%s' reloaded via /load", agent_id)
        return {"status": "reloaded", "agent_id": agent_id, "name": new_config.agent.name}

    # Load new agent — use the gateway session so it receives webhook messages
    gateway_session = os.environ.get("AGENT_SESSION", "") or os.environ.get("SESSION_NAME", "default")
    get_config.cache_clear()
    new_config = load_config(agent_id)
    session_name = new_config.agent.waha_session or gateway_session
    new_instance = await build_agent_instance(agent_id, new_config, session=session_name)
    registry.register(new_instance)

    logger.info("Agent '%s' loaded dynamically (session=%s)", agent_id, session_name)
    return {"status": "loaded", "agent_id": agent_id, "name": new_config.agent.name}


@app.delete("/unload/{agent_id}", tags=["admin"])
async def unload_agent(agent_id: str) -> dict:
    """
    Remove an agent from the registry. Called by CRM when an agent is deleted.
    """
    from fastapi import HTTPException
    registry: AgentRegistry = getattr(app.state, "registry", None)
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not ready")

    instance = registry.get_by_agent_id(agent_id)
    if instance is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    # Don't allow unloading the last agent
    if len(registry) <= 1:
        raise HTTPException(status_code=400, detail="Cannot unload the last running agent")

    registry.remove(agent_id)
    logger.info("Agent '%s' unloaded from registry", agent_id)
    return {"status": "unloaded", "agent_id": agent_id}


@app.post("/reload/{agent_id}", tags=["admin"])
async def reload_agent(agent_id: str) -> dict:
    """Reload agent config from business.yml without restarting the process."""
    registry: AgentRegistry = getattr(app.state, "registry", None)
    if registry is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Registry not ready")

    old_instance = registry.get_by_agent_id(agent_id)
    if old_instance is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found in registry")

    # Clear lru_cache so load_config re-reads from disk
    get_config.cache_clear()

    # Load fresh config directly (bypassing cache)
    new_config = load_config(agent_id)

    # Rebuild the full agent instance with fresh config, preserving session name
    new_instance = await build_agent_instance(agent_id, new_config, session=old_instance.session)

    # Swap the old instance in the registry
    registry.replace(new_instance)

    # Update backward-compat single-agent state if this was the primary agent
    if getattr(app.state, "agent_id", None) == agent_id:
        app.state.config = new_config
        app.state.debouncer = new_instance.debouncer
        app.state.process_message = new_instance.process_message
        app.state.media = new_instance.media

    logger.info("Agent '%s' reloaded: model=%s/%s", agent_id, new_config.llm.provider, new_config.llm.model)
    return {"status": "reloaded", "agent_id": agent_id, "name": new_config.agent.name}


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Liveness check with info about all running agents."""
    registry: AgentRegistry = getattr(app.state, "registry", None)
    if registry is None:
        return {"status": "starting"}

    agents = [
        {
            "agent_id": inst.agent_id,
            "session": inst.session,
            "name": inst.config.agent.name,
            "company": inst.config.agent.company,
        }
        for inst in registry.all_instances()
    ]
    return {"status": "ok", "agents": agents}

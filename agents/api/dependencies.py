"""
Dependency injection container for the WhatsApp agent API.

Builds and wires all adapters and use cases based on the agent's BusinessConfig.
Adapters are created once at startup and shared across requests.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from infrastructure.config_loader import BusinessConfig, get_config
from infrastructure.redis_client import MessageDebouncer, get_redis

logger = logging.getLogger(__name__)


async def build_primary_llm(config: BusinessConfig):
    """Instantiate the primary LLM adapter from config."""
    from adapters.outbound.llm.gemini_adapter import GeminiAdapter
    from adapters.outbound.llm.ollama_adapter import OllamaAdapter

    provider = config.llm.provider.lower()
    if provider == "gemini":
        return GeminiAdapter(
            model_name=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )
    elif provider == "ollama":
        return OllamaAdapter(
            model_name=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider!r}")


async def build_fallback_llm(config: BusinessConfig) -> Optional[object]:
    """Instantiate the fallback LLM adapter, or None if not configured."""
    from adapters.outbound.llm.gemini_adapter import GeminiAdapter
    from adapters.outbound.llm.ollama_adapter import OllamaAdapter

    provider = config.llm.fallback_provider.lower() if config.llm.fallback_provider else ""
    if not provider:
        return None

    if provider == "gemini":
        return GeminiAdapter(
            model_name=config.llm.fallback_model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )
    elif provider == "ollama":
        return OllamaAdapter(
            model_name=config.llm.fallback_model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )
    return None


def build_media(config: BusinessConfig):
    """Instantiate the media adapter.

    Uses OpenVoiceTTSAdapter (Gemini + voice cloning) when tts_voice_sample is set,
    otherwise falls back to plain GeminiMediaAdapter.
    """
    import os
    if os.environ.get("USE_NULL_MEDIA", "").lower() == "true":
        from adapters.outbound.media.null_media_adapter import NullMediaAdapter
        return NullMediaAdapter()

    gemini_kwargs = dict(
        audio_model=config.media.audio_model,
        image_model=config.media.image_model,
        video_model=config.media.video_model,
        video_frame_interval=config.media.video_frame_interval,
    )

    if config.media.tts_voice_sample:
        from adapters.outbound.media.openvoice_tts_adapter import OpenVoiceTTSAdapter
        logger.info("TTS: OpenVoice v2 (sample=%s)", config.media.tts_voice_sample)
        return OpenVoiceTTSAdapter(
            voice_sample_path=config.media.tts_voice_sample,
            **gemini_kwargs,
        )

    from adapters.outbound.media.gemini_media_adapter import GeminiMediaAdapter
    return GeminiMediaAdapter(**gemini_kwargs)


def build_gateway(config: BusinessConfig, agent_id: str = "default"):
    """Instantiate the WhatsApp gateway adapter."""
    import os
    
    # MODO SEGURO: Use fake gateway para testes
    if os.environ.get("USE_FAKE_GATEWAY", "").lower() == "true":
        from adapters.outbound.gateway.fake_gateway_adapter import FakeGatewayAdapter
        logger.warning("🔒 FAKE GATEWAY ATIVO - Mensagens NÃO serão enviadas!")
        return FakeGatewayAdapter()
    
    from adapters.outbound.gateway.waha_adapter import WAHAAdapter

    # Per-agent waha_url overrides the global env var
    waha_url = config.agent.waha_url or os.environ.get("WAHA_URL", "http://localhost:3000")
    # Per-agent waha_session overrides WAHA_SESSION env var, which overrides agent_id
    waha_session = config.agent.waha_session or os.environ.get("WAHA_SESSION", agent_id)
    return WAHAAdapter(base_url=waha_url, session=waha_session)


async def build_memory(config: BusinessConfig):
    """
    Instantiate the HybridMemoryAdapter (Qdrant + Postgres).

    Falls back to NullMemoryAdapter if USE_NULL_MEMORY=true env var is set
    (useful for running without infrastructure in development/testing).

    Returns:
        (memory_adapter, qdrant_adapter_or_none)
    """
    import os
    if os.environ.get("USE_NULL_MEMORY", "").lower() == "true":
        from adapters.outbound.memory.null_memory_adapter import NullMemoryAdapter
        return NullMemoryAdapter(), None

    from adapters.outbound.memory.qdrant_adapter import QdrantAdapter
    from adapters.outbound.memory.postgres_adapter import PostgresMessageRepository
    from adapters.outbound.memory.hybrid_memory_adapter import HybridMemoryAdapter

    qdrant = QdrantAdapter(
        chat_collection=config.memory.qdrant_collection,
        rules_collection=config.memory.qdrant_rag_collection,
        embedding_model=config.memory.embedding_model,
    )
    await qdrant.ensure_collections()

    postgres = PostgresMessageRepository()
    return HybridMemoryAdapter(qdrant=qdrant, postgres=postgres), qdrant


def build_crm(config: BusinessConfig):
    """Instantiate the CRM adapter based on config."""
    from adapters.outbound.crm.crm_event_adapter import CRMEventAdapter
    from adapters.outbound.crm.null_crm_adapter import NullCRMAdapter

    if config.crm.enabled and config.crm.events_webhook:
        return CRMEventAdapter(webhook_url=config.crm.events_webhook)
    return NullCRMAdapter()


def build_web_tools(config: BusinessConfig, media=None):
    """Instantiate WebToolsAdapter if tools are enabled in config."""
    if not config.tools.enabled:
        return None
    from adapters.outbound.mcp.web_tools import WebToolsAdapter
    return WebToolsAdapter(media_adapter=media)


def build_calendar(config: BusinessConfig):
    """Instantiate the calendar adapter based on config."""
    from adapters.outbound.calendar.null_calendar_adapter import NullCalendarAdapter
    if not config.calendar.enabled:
        return NullCalendarAdapter()
    creds = config.calendar.credentials_file
    cal_id = config.calendar.calendar_id
    if not creds or not cal_id:
        logger.warning("Calendar enabled but credentials_file or calendar_id not set — using NullCalendarAdapter")
        return NullCalendarAdapter()
    try:
        from adapters.outbound.calendar.google_calendar_adapter import GoogleCalendarAdapter
        return GoogleCalendarAdapter(credentials_file=creds, calendar_id=cal_id)
    except Exception:
        logger.exception("Failed to build GoogleCalendarAdapter — falling back to Null")
        return NullCalendarAdapter()


async def build_agent_instance(
    agent_id: str,
    config: BusinessConfig,
    session: Optional[str] = None,
):
    """
    Build and wire all components for a single agent.

    Args:
        agent_id: Agent identifier (matches folder in agents/).
        config:   Loaded BusinessConfig for this agent.
        session:  WAHA session name; defaults to agent_id.

    Returns:
        AgentInstance with all adapters wired.
    """
    from api.agent_registry import AgentInstance
    from core.use_cases.build_context import BuildContextUseCase
    from core.use_cases.ingest_documents import IngestDocumentsUseCase
    from core.use_cases.process_message import ProcessMessageUseCase

    resolved_session = session or agent_id
    redis = await get_redis()

    # Each agent gets its own namespaced debouncer to avoid key collisions
    debouncer = MessageDebouncer(
        redis,
        debounce_seconds=config.messaging.debounce_seconds,
        namespace=agent_id,
    )

    primary_llm = await build_primary_llm(config)
    fallback_llm = await build_fallback_llm(config)
    gateway = build_gateway(config, agent_id=resolved_session)
    memory_result = await build_memory(config)
    # build_memory now returns (memory, qdrant_or_none)
    if isinstance(memory_result, tuple):
        memory, qdrant_adapter = memory_result
    else:
        memory, qdrant_adapter = memory_result, None
    media = build_media(config)
    crm = build_crm(config)
    calendar = build_calendar(config)
    web_tools = build_web_tools(config, media=media)
    from infrastructure.activity_tracker import ActivityTracker
    activity_tracker = ActivityTracker(redis=redis, agent_id=agent_id)

    build_context = BuildContextUseCase(memory=memory, config=config)
    process_message = ProcessMessageUseCase(
        primary_llm=primary_llm,
        fallback_llm=fallback_llm,
        gateway=gateway,
        memory=memory,
        crm=crm,
        debouncer=debouncer,
        config=config,
        build_context=build_context,
        media=media,
        calendar=calendar,
        web_tools=web_tools,
    )

    # Build ingest use case (only when qdrant is available)
    ingest_uc = None
    if qdrant_adapter is not None:
        ingest_uc = IngestDocumentsUseCase(qdrant=qdrant_adapter, config=config)

    return AgentInstance(
        agent_id=agent_id,
        session=resolved_session,
        config=config,
        debouncer=debouncer,
        process_message=process_message,
        media=media,
        memory=memory,
        gateway=gateway,
        primary_llm=primary_llm,
        qdrant=qdrant_adapter,
        ingest=ingest_uc,
        calendar=calendar,
        activity_tracker=activity_tracker,
        web_tools=web_tools,
    )


# Keep legacy alias for backward compatibility with tests
async def build_use_cases(agent_id: str, config: BusinessConfig):
    """Legacy single-agent builder. Returns (debouncer, process_message, media)."""
    instance = await build_agent_instance(agent_id, config)
    return instance.debouncer, instance.process_message, instance.media

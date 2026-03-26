"""
Config loader — reads business.yml for the active agent and returns
a fully-typed BusinessConfig.

Environment variable interpolation: any value of the form "${VAR_NAME}"
is replaced with the value of the corresponding environment variable.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Typed configuration models
# ---------------------------------------------------------------------------


class AgentConfig(BaseModel):
    name: str
    company: str
    language: str = "pt-BR"
    persona: str = ""
    admin_phones: list[str] = Field(
        default_factory=list,
        description="List of phone numbers (digits only, with country code) allowed to use admin commands like /rag",
    )
    waha_url: Optional[str] = Field(
        default=None,
        description="Override WAHA_URL for this specific agent. Falls back to WAHA_URL env var.",
    )
    waha_session: Optional[str] = Field(
        default=None,
        description="Override WAHA session name. Falls back to agent_id.",
    )
    target_phones: list[str] = Field(
        default_factory=list,
        description="If set, this agent ONLY handles messages from these phone numbers. Empty = catch-all.",
    )


class LLMConfig(BaseModel):
    provider: str = "gemini"
    model: str = "gemini-3-flash-preview"
    fallback_provider: str = "ollama"
    fallback_model: str = "llama3.1:8b"
    temperature: float = 0.3
    max_tokens: int = 400


class MessagingConfig(BaseModel):
    debounce_seconds: float = 2.5
    max_message_chars: int = 180
    typing_delay_per_char: float = 0.04
    min_pause_between_parts: float = 1.2
    max_pause_between_parts: float = 2.8
    enable_tts: bool = False


class MemoryConfig(BaseModel):
    qdrant_collection: str
    qdrant_rag_collection: str
    semantic_k: int = 6
    max_recent_messages: int = 15
    embedding_model: str = "nomic-embed-text"


class AntiHallucinationConfig(BaseModel):
    rag_mandatory: bool = True
    unknown_answer: str = (
        "Não tenho essa informação agora, mas posso verificar com nossa equipe!"
    )
    grounding_enabled: bool = True


class MediaConfig(BaseModel):
    audio_model: str = "gemini-3-flash-preview"
    image_model: str = "gemini-3-flash-preview"
    video_model: str = "gemini-3-flash-preview"
    video_frame_interval: int = 5
    # TTS (text-to-speech) — agent responds with voice messages sometimes
    tts_enabled: bool = False
    tts_voice: str = "Kore"         # Gemini TTS voice name (fallback when no voice_sample)
    tts_voice_sample: str = ""      # Path to reference audio for OpenVoice cloning
    tts_chance: float = 0.15        # Probability of responding with audio (0.0 - 1.0)


class CRMConfig(BaseModel):
    enabled: bool = False
    events_webhook: Optional[str] = None
    push_events: list[str] = Field(
        default_factory=lambda: [
            "new_contact",
            "message_received",
            "agent_response_sent",
            "conversation_closed",
        ]
    )


class ProactiveConfig(BaseModel):
    enabled: bool = False
    daily_motivation_time: str = "18:00"
    daily_message_type: str = "static"  # "static" | "llm"
    inactivity_warning_days: int = 2
    inactivity_alert_days: int = 5
    calendar_reminder_days_before: int = 2
    timezone: str = "America/Sao_Paulo"
    target_chat_ids: list[str] = Field(default_factory=list)


class CalendarConfig(BaseModel):
    enabled: bool = False
    credentials_file: Optional[str] = None
    calendar_id: Optional[str] = None


class ToolsConfig(BaseModel):
    enabled: bool = False


class BusinessConfig(BaseModel):
    agent: AgentConfig
    llm: LLMConfig
    messaging: MessagingConfig
    memory: MemoryConfig
    anti_hallucination: AntiHallucinationConfig = Field(
        default_factory=AntiHallucinationConfig
    )
    media: MediaConfig = Field(default_factory=MediaConfig)
    crm: CRMConfig = Field(default_factory=CRMConfig)
    proactive: ProactiveConfig = Field(default_factory=ProactiveConfig)
    calendar: CalendarConfig = Field(default_factory=CalendarConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)


# ---------------------------------------------------------------------------
# Env-var interpolation
# ---------------------------------------------------------------------------

_ENV_VAR_RE = re.compile(r"\$\{([^}]+)\}")


def _interpolate(value: object) -> object:
    """Recursively replace '${VAR}' tokens with their env values."""
    if isinstance(value, str):
        def _replace(match: re.Match) -> str:
            var_name = match.group(1)
            return os.environ.get(var_name, "")

        return _ENV_VAR_RE.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(item) for item in value]
    return value


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

AGENTS_DIR = Path(__file__).parent.parent / "agents"


def _agents_dir() -> Path:
    """Return the agents base directory, allowing override via env var."""
    return Path(os.environ.get("AGENTS_DIR", str(AGENTS_DIR)))


def load_config(agent_id: Optional[str] = None) -> BusinessConfig:
    """
    Load and validate the business.yml for the given agent_id.

    If agent_id is None, falls back to the AGENT_ID environment variable.
    Raises FileNotFoundError if the config file does not exist.
    Raises ValidationError if the YAML does not match the schema.
    """
    resolved_id = agent_id or os.environ.get("AGENT_ID", "empresa_x")
    config_path = _agents_dir() / resolved_id / "business.yml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"business.yml not found for agent '{resolved_id}' at {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    interpolated = _interpolate(raw)
    return BusinessConfig.model_validate(interpolated)


@lru_cache(maxsize=32)
def get_config(agent_id: Optional[str] = None) -> BusinessConfig:
    """
    Cached version of load_config.  The cache is keyed by agent_id so that
    multiple agents can coexist in the same process without reloading each
    time.  Call get_config.cache_clear() in tests to reset.
    """
    return load_config(agent_id)

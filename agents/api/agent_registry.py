"""
AgentRegistry — in-process registry of active agent instances.

Supports two routing modes:
  1. By WAHA session name (one agent per session — default multi-agent setup)
  2. By sender phone within a shared session (when two agents share the same number)

     An agent with `agent.target_phones` set is a "restricted" agent — it only
     handles messages from those phone numbers.  An agent without target_phones
     is a "catch-all" — it handles everyone else on that session.

Usage:
    registry = AgentRegistry()
    registry.register(instance_ops)   # catch-all, session="default"
    registry.register(instance_maya)  # target_phones=["5511999999999"], session="default"

    # In the webhook:
    instance = registry.get_by_session_and_phone(session_name, chat_id)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from core.ports.gateway_port import GatewayPort
from core.ports.media_port import MediaPort
from core.ports.memory_port import MemoryPort
from core.use_cases.ingest_documents import IngestDocumentsUseCase
from core.use_cases.process_message import ProcessMessageUseCase
from infrastructure.config_loader import BusinessConfig
from infrastructure.redis_client import MessageDebouncer


@dataclass
class AgentInstance:
    """All runtime components for a single configured agent."""

    agent_id: str
    session: str             # WAHA session name (usually == agent_id)
    config: BusinessConfig
    debouncer: MessageDebouncer
    process_message: ProcessMessageUseCase
    media: MediaPort
    memory: MemoryPort = None
    gateway: GatewayPort = None
    primary_llm: object = None   # LLMPort
    # RAG components — available when USE_NULL_MEMORY is not set
    qdrant: object = None    # QdrantAdapter | None
    ingest: object = None    # IngestDocumentsUseCase | None
    calendar: object = None      # CalendarPort | None
    activity_tracker: object = None  # ActivityTracker | None
    proactive_scheduler: object = None  # ProactiveScheduler | None
    web_tools: object = None     # WebToolsAdapter | None


def _normalize_phone(chat_id: str) -> str:
    """Extract digits-only phone number from a WhatsApp JID."""
    number = re.sub(r"@.*$", "", chat_id)
    return re.sub(r"\D", "", number)


def _phone_matches(phone: str, target_phones: list[str]) -> bool:
    """Return True if `phone` matches any entry in `target_phones`."""
    return any(re.sub(r"\D", "", str(p)) == phone for p in target_phones)


class AgentRegistry:
    """
    Maps WAHA session names to AgentInstance objects.

    Multiple agents can share the same session — they are disambiguated by
    the sender's phone number via target_phones in their config.
    """

    def __init__(self) -> None:
        # session → ordered list of instances (registration order preserved)
        self._by_session: dict[str, list[AgentInstance]] = {}

    def register(self, instance: AgentInstance) -> None:
        """Register an agent instance under its session name."""
        self._by_session.setdefault(instance.session, []).append(instance)

    def get_by_session_and_phone(self, session: str, chat_id: str) -> Optional[AgentInstance]:
        """
        Return the AgentInstance that should handle this message.

        Lookup order:
          1. Find all agents registered for `session`.
          2. Single-agent fallback (any session → the only agent).
          3. "default" session → first registered agents list.
          4. Among candidates, prefer a targeted agent whose target_phones
             matches the sender's phone number.
          5. Fall back to the catch-all agent (no target_phones) for this session.
        """
        candidates = self._by_session.get(session)

        if not candidates:
            all_instances = self.all_instances()
            # Single-agent fallback
            if len(all_instances) == 1:
                return all_instances[0]
            # WAHA "default" session → first registered session's agents
            if session == "default" and self._by_session:
                candidates = next(iter(self._by_session.values()))
            else:
                return None

        phone = _normalize_phone(chat_id)

        # Priority 1: targeted agent matching this phone
        for inst in candidates:
            target = inst.config.agent.target_phones
            if target and _phone_matches(phone, target):
                return inst

        # Priority 2: catch-all agent (no target_phones restriction)
        for inst in candidates:
            if not inst.config.agent.target_phones:
                return inst

        # Last resort: first candidate
        return candidates[0]

    def get_by_agent_id(self, agent_id: str) -> Optional[AgentInstance]:
        """Return the AgentInstance for a specific agent_id."""
        for inst in self.all_instances():
            if inst.agent_id == agent_id:
                return inst
        return None

    def get_by_command(self, command: str) -> Optional[AgentInstance]:
        """
        Find an agent matching a slash command like /maya or /ops_solutions.

        Matches against (case-insensitive):
          - /{agent_id}       e.g. /ops_solutions
          - /{agent.name}     e.g. /rafael  (from name: "Rafael")
        """
        cmd = command.lstrip("/").lower().strip()
        for inst in self.all_instances():
            if inst.agent_id.lower() == cmd:
                return inst
            if inst.config.agent.name.lower() == cmd:
                return inst
        return None

    def get_by_session(self, session: str) -> Optional[AgentInstance]:
        """
        Backward-compatible single lookup (returns first agent for session).
        Prefer get_by_session_and_phone when the chat_id is available.
        """
        instances = self._by_session.get(session)
        if instances:
            return instances[0]
        all_instances = self.all_instances()
        if len(all_instances) == 1:
            return all_instances[0]
        if session == "default" and self._by_session:
            return next(iter(self._by_session.values()))[0]
        return None

    def all_instances(self) -> list[AgentInstance]:
        """Return all registered agent instances (in registration order)."""
        return [inst for instances in self._by_session.values() for inst in instances]

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_session.values())

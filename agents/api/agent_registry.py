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

    Two indices are maintained in sync:
      _by_session  — session → ordered list of instances (for webhook routing)
      _by_agent_id — agent_id → instance (O(1) lookup by id)

    Multiple agents can share the same session — they are disambiguated by
    the sender's phone number via target_phones in their config.
    """

    def __init__(self) -> None:
        self._by_session: dict[str, list[AgentInstance]] = {}
        self._by_agent_id: dict[str, AgentInstance] = {}

    def register(self, instance: AgentInstance) -> None:
        """Register an agent instance under its session name and agent_id."""
        self._by_session.setdefault(instance.session, []).append(instance)
        self._by_agent_id[instance.agent_id] = instance

    def get_by_session_and_phone(self, session: str, chat_id: str) -> Optional[AgentInstance]:
        """
        Return the AgentInstance that should handle this message.

        Lookup order:
          1. Find all agents registered for `session`.
          2. Single-agent fallback (any session → the only agent).
          3. "default" session → first registered session's agents.
          4. Among candidates, prefer a targeted agent whose target_phones
             matches the sender's phone number.
          5. Fall back to the catch-all agent (no target_phones) for this session.
        """
        candidates = self._by_session.get(session)

        if not candidates:
            all_inst = list(self._by_agent_id.values())
            if len(all_inst) == 1:
                return all_inst[0]
            if session == "default" and self._by_session:
                candidates = next(iter(self._by_session.values()))
            else:
                return None

        phone = _normalize_phone(chat_id)

        # Priority 1: targeted agent matching this phone
        for inst in candidates:
            if inst.config.agent.target_phones and _phone_matches(phone, inst.config.agent.target_phones):
                return inst

        # Priority 2: catch-all agent (no target_phones restriction)
        for inst in candidates:
            if not inst.config.agent.target_phones:
                return inst

        return candidates[0]

    def get_by_agent_id(self, agent_id: str) -> Optional[AgentInstance]:
        """O(1) lookup by agent_id."""
        return self._by_agent_id.get(agent_id)

    def get_by_command(self, command: str) -> Optional[AgentInstance]:
        """
        Find an agent matching a slash command like /maya or /ops_solutions.

        Matches against (case-insensitive):
          - /{agent_id}       e.g. /ops_solutions
          - /{agent.name}     e.g. /rafael  (from name: "Rafael")
        """
        cmd = command.lstrip("/").lower().strip()
        # O(1) check by agent_id first
        inst = self._by_agent_id.get(cmd)
        if inst:
            return inst
        # Linear scan by name (names are not indexed)
        for inst in self._by_agent_id.values():
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
        all_inst = list(self._by_agent_id.values())
        if len(all_inst) == 1:
            return all_inst[0]
        if session == "default" and self._by_session:
            return next(iter(self._by_session.values()))[0]
        return None

    def replace(self, new_instance: AgentInstance) -> bool:
        """Replace the instance with the same agent_id. Returns True if found."""
        old = self._by_agent_id.get(new_instance.agent_id)
        if old is None:
            return False
        session_list = self._by_session.get(old.session, [])
        for i, inst in enumerate(session_list):
            if inst.agent_id == old.agent_id:
                session_list[i] = new_instance
                break
        self._by_agent_id[new_instance.agent_id] = new_instance
        return True

    def replace_agent(self, old_agent_id: str, new_instance: AgentInstance) -> bool:
        """
        Replace the instance identified by old_agent_id with new_instance.
        new_instance may have a different agent_id (used when switching personas).
        """
        old = self._by_agent_id.get(old_agent_id)
        if old is None:
            return False
        session_list = self._by_session.get(old.session, [])
        for i, inst in enumerate(session_list):
            if inst.agent_id == old_agent_id:
                session_list[i] = new_instance
                break
        del self._by_agent_id[old_agent_id]
        self._by_agent_id[new_instance.agent_id] = new_instance
        return True

    def remove(self, agent_id: str) -> bool:
        """Remove an agent from the registry. Returns True if found."""
        inst = self._by_agent_id.pop(agent_id, None)
        if inst is None:
            return False
        session_list = self._by_session.get(inst.session, [])
        self._by_session[inst.session] = [i for i in session_list if i.agent_id != agent_id]
        if not self._by_session[inst.session]:
            del self._by_session[inst.session]
        return True

    def all_instances(self) -> list[AgentInstance]:
        """Return all registered agent instances."""
        return list(self._by_agent_id.values())

    def __len__(self) -> int:
        return len(self._by_agent_id)

"""
Unit tests for AgentRegistry and multi-agent routing.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from api.agent_registry import AgentInstance, AgentRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_instance(agent_id: str, session: str | None = None) -> AgentInstance:
    return AgentInstance(
        agent_id=agent_id,
        session=session or agent_id,
        config=MagicMock(),
        debouncer=MagicMock(),
        process_message=MagicMock(),
        media=MagicMock(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAgentRegistry:
    def test_register_and_get_by_session(self):
        registry = AgentRegistry()
        instance = _make_instance("empresa_x")
        registry.register(instance)

        result = registry.get_by_session("empresa_x")
        assert result is instance

    def test_get_by_unknown_session_returns_none_with_multiple_agents(self):
        registry = AgentRegistry()
        registry.register(_make_instance("empresa_x"))
        registry.register(_make_instance("empresa_y"))

        result = registry.get_by_session("empresa_z")
        assert result is None

    def test_single_agent_fallback_on_unknown_session(self):
        registry = AgentRegistry()
        instance = _make_instance("empresa_x")
        registry.register(instance)

        # Single agent → fallback regardless of session name
        result = registry.get_by_session("qualquer_coisa")
        assert result is instance

    def test_multiple_agents_no_fallback_on_unknown(self):
        registry = AgentRegistry()
        registry.register(_make_instance("empresa_x"))
        registry.register(_make_instance("empresa_y"))

        assert registry.get_by_session("empresa_z") is None

    def test_all_instances_returns_all(self):
        registry = AgentRegistry()
        a = _make_instance("empresa_x")
        b = _make_instance("empresa_y")
        registry.register(a)
        registry.register(b)

        instances = registry.all_instances()
        assert len(instances) == 2
        assert a in instances
        assert b in instances

    def test_len(self):
        registry = AgentRegistry()
        assert len(registry) == 0
        registry.register(_make_instance("empresa_x"))
        assert len(registry) == 1
        registry.register(_make_instance("empresa_y"))
        assert len(registry) == 2

    def test_session_overrides_agent_id(self):
        """An agent can have a different session name than its agent_id."""
        registry = AgentRegistry()
        instance = _make_instance("empresa_x", session="whatsapp_session_1")
        registry.register(instance)

        # Direct session lookup works
        assert registry.get_by_session("whatsapp_session_1") is instance
        # Single-agent fallback: any unknown session returns the only agent
        assert registry.get_by_session("empresa_x") is instance
        assert registry.get_by_session("whatever") is instance


class TestDebouncerNamespace:
    @pytest.mark.asyncio
    async def test_namespaced_key_includes_agent_id(self):
        """Namespaced debouncer uses agent-prefixed Redis keys."""
        from tests.unit.test_debouncer import FakeRedis
        from infrastructure.redis_client import MessageDebouncer

        redis = FakeRedis()
        debouncer = MessageDebouncer(redis, debounce_seconds=2.5, namespace="empresa_x")
        await debouncer.push_message("5511@c.us", '{"text":"oi"}')
        assert "buffer:empresa_x:5511@c.us" in redis._data

    @pytest.mark.asyncio
    async def test_different_namespaces_dont_collide(self):
        """Two agents with same chat_id don't share buffers."""
        from tests.unit.test_debouncer import FakeRedis
        from infrastructure.redis_client import MessageDebouncer

        redis = FakeRedis()
        debouncer_x = MessageDebouncer(redis, debounce_seconds=2.5, namespace="empresa_x")
        debouncer_y = MessageDebouncer(redis, debounce_seconds=2.5, namespace="empresa_y")

        await debouncer_x.push_message("5511@c.us", "msg x")
        await debouncer_y.push_message("5511@c.us", "msg y")

        assert redis._data.get("buffer:empresa_x:5511@c.us") == ["msg x"]
        assert redis._data.get("buffer:empresa_y:5511@c.us") == ["msg y"]

    @pytest.mark.asyncio
    async def test_no_namespace_backward_compatible(self):
        """Debouncer without namespace uses legacy key format."""
        from tests.unit.test_debouncer import FakeRedis
        from infrastructure.redis_client import MessageDebouncer

        redis = FakeRedis()
        debouncer = MessageDebouncer(redis, debounce_seconds=2.5)  # no namespace
        await debouncer.push_message("5511@c.us", "msg")
        assert "buffer:5511@c.us" in redis._data


class TestCRMEventsInProcessMessage:
    @pytest.mark.asyncio
    async def test_new_contact_event_fired_on_first_message(self):
        from tests.unit.test_process_message import (
            MockLLM, MockGateway, MockMemory, MockCRM, MockDebouncer,
            _make_config
        )
        from core.use_cases.build_context import BuildContextUseCase
        from core.use_cases.process_message import ProcessMessageUseCase

        config = _make_config()
        config = config.model_copy(update={"crm": config.crm.model_copy(
            update={"enabled": True, "push_events": ["new_contact", "message_received", "agent_response_sent"]}
        )})

        llm = MockLLM("Olá!")
        gateway = MockGateway()
        memory = MockMemory()
        crm = MockCRM()
        debouncer = MockDebouncer()
        build_context = BuildContextUseCase(memory=memory, config=config)

        uc = ProcessMessageUseCase(
            primary_llm=llm, fallback_llm=None, gateway=gateway,
            memory=memory, crm=crm, debouncer=debouncer,
            config=config, build_context=build_context,
        )

        await uc.execute("empresa_x", "5511@c.us", ["Olá!"], task_id="t1")

        event_types = [e.event_type for e in crm.events]
        assert "new_contact" in event_types
        assert "message_received" in event_types
        assert "agent_response_sent" in event_types

    @pytest.mark.asyncio
    async def test_no_new_contact_event_on_returning_user(self):
        from tests.unit.test_process_message import (
            MockLLM, MockGateway, MockCRM, MockDebouncer, _make_config
        )
        from core.domain.message import Message
        from core.use_cases.build_context import BuildContextUseCase
        from core.use_cases.process_message import ProcessMessageUseCase
        from adapters.outbound.memory.null_memory_adapter import NullMemoryAdapter
        from unittest.mock import AsyncMock

        config = _make_config()
        config = config.model_copy(update={"crm": config.crm.model_copy(
            update={"enabled": True, "push_events": ["new_contact", "message_received", "agent_response_sent"]}
        )})

        # Memory returns one previous message → not a new contact
        memory_with_history = NullMemoryAdapter()
        memory_with_history.get_recent = AsyncMock(return_value=[
            Message(chat_id="5511@c.us", agent_id="x", role="user", content="mensagem anterior")
        ])
        memory_with_history.save_message = AsyncMock()
        memory_with_history.search_semantic = AsyncMock(return_value=[])
        memory_with_history.search_business_rules = AsyncMock(return_value=[])

        llm = MockLLM("Olá!")
        gateway = MockGateway()
        crm = MockCRM()
        debouncer = MockDebouncer()
        build_context = BuildContextUseCase(memory=memory_with_history, config=config)

        uc = ProcessMessageUseCase(
            primary_llm=llm, fallback_llm=None, gateway=gateway,
            memory=memory_with_history, crm=crm, debouncer=debouncer,
            config=config, build_context=build_context,
        )

        await uc.execute("empresa_x", "5511@c.us", ["Olá de novo!"], task_id="t1")

        event_types = [e.event_type for e in crm.events]
        assert "new_contact" not in event_types
        assert "message_received" in event_types

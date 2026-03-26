"""
Unit tests for ProcessMessageUseCase.

All external dependencies (LLM, gateway, memory, CRM, Redis) are mocked
so these tests run entirely in memory with no network or infrastructure.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.domain.memory import ContextWindow
from core.ports.crm_port import CRMEvent
from core.ports.gateway_port import GatewayPort
from core.ports.llm_port import LLMPort
from core.ports.memory_port import MemoryPort
from core.use_cases.build_context import BuildContextUseCase
from core.use_cases.process_message import ProcessMessageUseCase
from infrastructure.config_loader import (
    AgentConfig,
    AntiHallucinationConfig,
    BusinessConfig,
    CRMConfig,
    LLMConfig,
    MediaConfig,
    MemoryConfig,
    MessagingConfig,
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _make_config(rag_mandatory: bool = False) -> BusinessConfig:
    return BusinessConfig(
        agent=AgentConfig(name="TestBot", company="Test Co"),
        llm=LLMConfig(provider="ollama", model="llama3.1:8b"),
        messaging=MessagingConfig(
            debounce_seconds=2.5,
            max_message_chars=180,
            typing_delay_per_char=0.0,   # No delay in tests
            min_pause_between_parts=0.0,
            max_pause_between_parts=0.0,
        ),
        memory=MemoryConfig(
            qdrant_collection="test_chats",
            qdrant_rag_collection="test_rules",
        ),
        anti_hallucination=AntiHallucinationConfig(
            rag_mandatory=rag_mandatory,
            unknown_answer="Não sei!",
            grounding_enabled=False,
        ),
        media=MediaConfig(),
        crm=CRMConfig(enabled=False),
    )


async def _simple_stream(text: str) -> AsyncIterator[str]:
    """Yield a single chunk for mocked LLM."""
    yield text


class MockLLM(LLMPort):
    def __init__(self, response: str = "Olá! Como posso ajudar?"):
        self._response = response
        self.calls: list[dict] = []

    async def stream_response(
        self, messages: list[dict], system: str = ""
    ) -> AsyncIterator[str]:
        self.calls.append({"messages": messages, "system": system})
        yield self._response

    async def generate(self, messages: list[dict], system: str = "") -> str:
        return self._response


class MockGateway(GatewayPort):
    def __init__(self):
        self.sent_messages: list[tuple[str, str]] = []
        self.typing_states: list[tuple[str, bool]] = []

    async def send_message(self, chat_id: str, text: str) -> None:
        self.sent_messages.append((chat_id, text))

    async def send_typing(self, chat_id: str, active: bool) -> None:
        self.typing_states.append((chat_id, active))


class MockMemory(MemoryPort):
    def __init__(self):
        self.saved: list = []

    async def save_message(self, message) -> None:
        self.saved.append(message)

    async def search_semantic(self, chat_id, query, k=6):
        return []

    async def get_recent(self, chat_id, n=15):
        return []

    async def search_business_rules(self, query, k=4, agent_id=""):
        return []


class MockCRM:
    def __init__(self):
        self.events: list[CRMEvent] = []

    async def push_event(self, event: CRMEvent) -> None:
        self.events.append(event)


class MockDebouncer:
    def __init__(self, active: bool = True):
        self._active = active
        self.active_task: dict[str, str] = {}

    async def set_active_task(self, chat_id: str, task_id: str) -> None:
        self.active_task[chat_id] = task_id

    async def get_active_task(self, chat_id: str):
        return self.active_task.get(chat_id)

    async def is_task_active(self, chat_id: str, task_id: str) -> bool:
        return self._active and self.active_task.get(chat_id) == task_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_use_case(
    llm_response: str = "Olá! Tudo bem.",
    rag_mandatory: bool = False,
    task_active: bool = True,
):
    config = _make_config(rag_mandatory=rag_mandatory)
    llm = MockLLM(llm_response)
    gateway = MockGateway()
    memory = MockMemory()
    crm = MockCRM()
    debouncer = MockDebouncer(active=task_active)

    build_context = BuildContextUseCase(memory=memory, config=config)

    uc = ProcessMessageUseCase(
        primary_llm=llm,
        fallback_llm=None,
        gateway=gateway,
        memory=memory,
        crm=crm,
        debouncer=debouncer,
        config=config,
        build_context=build_context,
    )
    return uc, gateway, memory, crm, debouncer


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestProcessMessageUseCase:
    @pytest.mark.asyncio
    async def test_sends_response_to_gateway(self):
        uc, gateway, *_ = _make_use_case("Olá! Como posso ajudar?")
        await uc.execute("agent_x", "5511@c.us", ["Oi"], task_id="t1")
        assert len(gateway.sent_messages) == 1
        assert gateway.sent_messages[0][0] == "5511@c.us"
        assert "Olá" in gateway.sent_messages[0][1]

    @pytest.mark.asyncio
    async def test_empty_user_texts_does_nothing(self):
        uc, gateway, *_ = _make_use_case()
        await uc.execute("agent_x", "5511@c.us", [], task_id="t1")
        assert len(gateway.sent_messages) == 0

    @pytest.mark.asyncio
    async def test_multipart_response_sends_multiple_messages(self):
        # Two paragraphs → two send_message calls
        response = "Primeira parte.\n\nSegunda parte."
        uc, gateway, *_ = _make_use_case(response)
        await uc.execute("agent_x", "5511@c.us", ["oi"], task_id="t1")
        assert len(gateway.sent_messages) == 2

    @pytest.mark.asyncio
    async def test_typing_indicator_sent_before_each_part(self):
        response = "Parte um.\n\nParte dois."
        uc, gateway, *_ = _make_use_case(response)
        await uc.execute("agent_x", "5511@c.us", ["oi"], task_id="t1")
        # Should have True/False pairs for each part
        true_states = [s for _, s in gateway.typing_states if s is True]
        assert len(true_states) == 2

    @pytest.mark.asyncio
    async def test_saves_user_and_assistant_messages(self):
        uc, _, memory, *_ = _make_use_case("Resposta do agente.")
        await uc.execute("agent_x", "5511@c.us", ["Olá", "Tudo bem?"], task_id="t1")
        roles = [m.role for m in memory.saved]
        assert "user" in roles
        assert "assistant" in roles

    @pytest.mark.asyncio
    async def test_superseded_task_does_not_send(self):
        # task_active=False simulates a newer task replacing this one
        uc, gateway, *_ = _make_use_case(task_active=False)
        await uc.execute("agent_x", "5511@c.us", ["oi"], task_id="t1")
        assert len(gateway.sent_messages) == 0

    @pytest.mark.asyncio
    async def test_consolidated_query_sent_to_llm(self):
        config = _make_config()
        llm = MockLLM("ok")
        gateway = MockGateway()
        memory = MockMemory()
        crm = MockCRM()
        debouncer = MockDebouncer()
        build_context = BuildContextUseCase(memory=memory, config=config)
        uc = ProcessMessageUseCase(
            primary_llm=llm,
            fallback_llm=None,
            gateway=gateway,
            memory=memory,
            crm=crm,
            debouncer=debouncer,
            config=config,
            build_context=build_context,
        )
        await uc.execute("agent_x", "5511@c.us", ["Oi", "Tudo bem?"], task_id="t1")
        assert len(llm.calls) == 1
        # The consolidated text should be in the last user message
        last_msg = llm.calls[0]["messages"][-1]
        assert "Oi" in last_msg["content"]
        assert "Tudo bem?" in last_msg["content"]

    @pytest.mark.asyncio
    async def test_rag_mandatory_without_context_returns_unknown_answer(self):
        uc, gateway, *_ = _make_use_case(rag_mandatory=True)
        await uc.execute("agent_x", "5511@c.us", ["Pergunta sem contexto"], task_id="t1")
        assert len(gateway.sent_messages) == 1
        assert gateway.sent_messages[0][1] == "Não sei!"

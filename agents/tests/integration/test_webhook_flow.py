"""
Integration tests for the full webhook → debounce → process flow.

Uses a lightweight FastAPI app (no lifespan, all adapters stubbed) so
no Docker infrastructure is required.

Run with:
    pytest tests/integration/
"""

from __future__ import annotations

import json
from typing import AsyncIterator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from adapters.inbound.waha_webhook import router as webhook_router
from api.agent_registry import AgentInstance, AgentRegistry
from core.ports.crm_port import CRMEvent, CRMPort
from core.ports.gateway_port import GatewayPort
from core.ports.llm_port import LLMPort
from core.ports.media_port import MediaPort
from core.ports.memory_port import MemoryPort
from infrastructure.rate_limiter import RateLimiter


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


class StubLLM(LLMPort):
    def __init__(self, response: str = "Olá! Como posso ajudar?"):
        self._response = response
        self.calls: list = []

    async def stream_response(self, messages, system="") -> AsyncIterator[str]:
        self.calls.append(messages)
        yield self._response

    async def generate(self, messages, system="") -> str:
        return self._response


class StubGateway(GatewayPort):
    def __init__(self):
        self.sent: list[tuple[str, str]] = []
        self.typing: list = []

    async def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))

    async def send_typing(self, chat_id, active):
        self.typing.append((chat_id, active))


class StubMemory(MemoryPort):
    async def save_message(self, message): pass
    async def search_semantic(self, chat_id, query, k=6): return []
    async def get_recent(self, chat_id, n=15): return []
    async def search_business_rules(self, query, k=4, agent_id=""): return []


class StubCRM(CRMPort):
    def __init__(self):
        self.events: list[CRMEvent] = []

    async def push_event(self, event: CRMEvent):
        self.events.append(event)


class StubMedia(MediaPort):
    async def transcribe_audio(self, data): return "transcrição do áudio"
    async def describe_image(self, data): return "descrição da imagem"
    async def describe_video(self, data): return "descrição do vídeo"


class StubDebouncer:
    def __init__(self):
        self.pushed: list[tuple[str, str]] = []
        self._active: dict[str, str] = {}

    async def push_message(self, chat_id, msg_json):
        self.pushed.append((chat_id, msg_json))

    async def get_and_clear_buffer(self, chat_id): return []

    async def set_active_task(self, chat_id, task_id):
        self._active[chat_id] = task_id

    async def get_active_task(self, chat_id):
        return self._active.get(chat_id)

    async def is_task_active(self, chat_id, task_id):
        return self._active.get(chat_id) == task_id

    @property
    def namespace(self): return "empresa_x"


class FakeRedisForRate:
    def __init__(self):
        self._c: dict = {}

    async def incr(self, key):
        self._c[key] = self._c.get(key, 0) + 1
        return self._c[key]

    async def expire(self, key, ttl): pass


# ---------------------------------------------------------------------------
# Test app factory (no lifespan — state injected directly)
# ---------------------------------------------------------------------------


def _make_payload(
    chat_id="5511@c.us",
    body="Olá",
    msg_type="chat",
    session="empresa_x",
    from_me=False,
    has_media=False,
    media_url="",
) -> dict:
    return {
        "event": "message",
        "session": session,
        "payload": {
            "id": "test_msg_001",
            "from": chat_id,
            "fromMe": from_me,
            "type": msg_type,
            "body": body,
            "hasMedia": has_media,
            "mediaUrl": media_url,
        },
    }


@pytest.fixture()
def stubs():
    return {
        "llm": StubLLM(),
        "gateway": StubGateway(),
        "memory": StubMemory(),
        "crm": StubCRM(),
        "media": StubMedia(),
        "debouncer": StubDebouncer(),
    }


@pytest.fixture()
def client(stubs):
    """
    Lightweight FastAPI app with the webhook router and pre-injected state.
    No lifespan runs — avoids any infrastructure requirements.
    """
    from infrastructure.config_loader import get_config

    get_config.cache_clear()
    config = get_config("empresa_x")
    config = config.model_copy(update={
        "messaging": config.messaging.model_copy(update={
            "typing_delay_per_char": 0.0,
            "min_pause_between_parts": 0.0,
            "max_pause_between_parts": 0.0,
        })
    })

    from core.use_cases.build_context import BuildContextUseCase
    from core.use_cases.process_message import ProcessMessageUseCase

    build_context = BuildContextUseCase(memory=stubs["memory"], config=config)
    process_message = ProcessMessageUseCase(
        primary_llm=stubs["llm"],
        fallback_llm=None,
        gateway=stubs["gateway"],
        memory=stubs["memory"],
        crm=stubs["crm"],
        debouncer=stubs["debouncer"],
        config=config,
        build_context=build_context,
    )

    instance = AgentInstance(
        agent_id="empresa_x",
        session="empresa_x",
        config=config,
        debouncer=stubs["debouncer"],
        process_message=process_message,
        media=stubs["media"],
    )
    registry = AgentRegistry()
    registry.register(instance)

    rate_limiter = RateLimiter(FakeRedisForRate(), max_messages=100, window_seconds=60)

    # Build isolated app — no lifespan
    test_app = FastAPI()
    test_app.include_router(webhook_router)
    test_app.state.registry = registry
    test_app.state.rate_limiter = rate_limiter
    test_app.state.waha_api_key = ""

    @test_app.get("/health")
    async def health():
        agents = [
            {"agent_id": i.agent_id, "session": i.session, "name": i.config.agent.name}
            for i in registry.all_instances()
        ]
        return {"status": "ok", "agents": agents}

    return TestClient(test_app)


# ---------------------------------------------------------------------------
# Webhook tests
# ---------------------------------------------------------------------------


class TestWebhookEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert any(a["agent_id"] == "empresa_x" for a in data["agents"])

    def test_text_message_queued(self, client, stubs):
        debouncer: StubDebouncer = stubs["debouncer"]
        payload = _make_payload(body="Olá, preciso de ajuda")
        resp = client.post("/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"
        assert len(debouncer.pushed) == 1
        pushed_chat, pushed_json = debouncer.pushed[0]
        assert pushed_chat == "5511@c.us"
        data = json.loads(pushed_json)
        assert data["text"] == "Olá, preciso de ajuda"

    def test_fromMe_messages_ignored(self, client, stubs):
        debouncer: StubDebouncer = stubs["debouncer"]
        resp = client.post("/webhook", json=_make_payload(from_me=True))
        assert resp.status_code == 200
        assert resp.json()["reason"] == "fromMe"
        assert len(debouncer.pushed) == 0

    def test_non_message_events_ignored(self, client):
        resp = client.post("/webhook", json={"event": "session.status", "session": "empresa_x"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    def test_empty_body_ignored(self, client, stubs):
        debouncer: StubDebouncer = stubs["debouncer"]
        resp = client.post("/webhook", json=_make_payload(body="   "))
        assert resp.status_code == 200
        assert len(debouncer.pushed) == 0

    def test_unknown_session_single_agent_fallback(self, client, stubs):
        """With one agent registered, any session falls back to it."""
        debouncer: StubDebouncer = stubs["debouncer"]
        payload = _make_payload(body="oi", session="qualquer_sessao")
        resp = client.post("/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"

    def test_invalid_json_returns_400(self, client):
        resp = client.post(
            "/webhook",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    def test_media_message_returns_processing(self, client):
        payload = _make_payload(
            msg_type="ptt", has_media=True, media_url="http://waha/audio.ogg"
        )
        resp = client.post("/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "processing"

    def test_multiple_messages_from_same_chat(self, client, stubs):
        """Each message pushed individually to the debouncer."""
        debouncer: StubDebouncer = stubs["debouncer"]
        for body in ["oi", "tudo bem?", "preciso de ajuda"]:
            client.post("/webhook", json=_make_payload(body=body))
        assert len(debouncer.pushed) == 3

    def test_rate_limited_chat_throttled(self, client, stubs):
        """After exceeding rate limit, messages are throttled."""
        # Use a rate limiter set to max 2
        from infrastructure.rate_limiter import RateLimiter
        strict_limiter = RateLimiter(FakeRedisForRate(), max_messages=2, window_seconds=60)
        client.app.state.rate_limiter = strict_limiter

        client.post("/webhook", json=_make_payload(body="msg 1"))
        client.post("/webhook", json=_make_payload(body="msg 2"))
        resp = client.post("/webhook", json=_make_payload(body="msg 3"))
        assert resp.json()["status"] == "throttled"


# ---------------------------------------------------------------------------
# ProcessMessage end-to-end
# ---------------------------------------------------------------------------


class TestProcessMessageIntegration:
    @pytest.mark.asyncio
    async def test_full_flow_sends_response(self):
        from core.use_cases.build_context import BuildContextUseCase
        from core.use_cases.process_message import ProcessMessageUseCase
        from infrastructure.config_loader import get_config

        get_config.cache_clear()
        config = get_config("empresa_x")
        config = config.model_copy(update={
            "messaging": config.messaging.model_copy(update={
                "typing_delay_per_char": 0.0,
                "min_pause_between_parts": 0.0,
                "max_pause_between_parts": 0.0,
            })
        })

        llm = StubLLM("Tudo bem! Como posso ajudar?")
        gateway = StubGateway()
        memory = StubMemory()
        debouncer = StubDebouncer()
        build_context = BuildContextUseCase(memory=memory, config=config)

        uc = ProcessMessageUseCase(
            primary_llm=llm, fallback_llm=None,
            gateway=gateway, memory=memory, crm=StubCRM(),
            debouncer=debouncer, config=config, build_context=build_context,
        )

        await uc.execute("empresa_x", "5511@c.us", ["Olá!"], task_id="t1")

        assert len(gateway.sent) >= 1
        assert any("ajudar" in text for _, text in gateway.sent)

    @pytest.mark.asyncio
    async def test_three_messages_consolidated_into_one_llm_call(self):
        from core.use_cases.build_context import BuildContextUseCase
        from core.use_cases.process_message import ProcessMessageUseCase
        from infrastructure.config_loader import get_config

        get_config.cache_clear()
        config = get_config("empresa_x")
        config = config.model_copy(update={
            "messaging": config.messaging.model_copy(update={
                "typing_delay_per_char": 0.0,
                "min_pause_between_parts": 0.0,
                "max_pause_between_parts": 0.0,
            })
        })

        llm = StubLLM("Entendido!")
        gateway = StubGateway()
        memory = StubMemory()
        debouncer = StubDebouncer()
        build_context = BuildContextUseCase(memory=memory, config=config)

        uc = ProcessMessageUseCase(
            primary_llm=llm, fallback_llm=None,
            gateway=gateway, memory=memory, crm=StubCRM(),
            debouncer=debouncer, config=config, build_context=build_context,
        )

        # Three messages consolidated (as debouncer would do)
        await uc.execute(
            "empresa_x", "5511@c.us",
            ["oi", "tudo bem?", "preciso de ajuda"],
            task_id="t1",
        )

        # LLM called exactly once with all 3 consolidated
        assert len(llm.calls) == 1
        last_user_msg = llm.calls[0][-1]
        assert "oi" in last_user_msg["content"]
        assert "preciso de ajuda" in last_user_msg["content"]

    @pytest.mark.asyncio
    async def test_superseded_task_skips_send(self):
        """
        Simulates a newer task overwriting the active_task after set but before send.
        Uses a stub that always reports the task as inactive.
        """
        from core.use_cases.build_context import BuildContextUseCase
        from core.use_cases.process_message import ProcessMessageUseCase
        from infrastructure.config_loader import get_config

        get_config.cache_clear()
        config = get_config("empresa_x")
        config = config.model_copy(update={
            "messaging": config.messaging.model_copy(update={
                "typing_delay_per_char": 0.0,
                "min_pause_between_parts": 0.0,
                "max_pause_between_parts": 0.0,
            })
        })

        class SupersededDebouncer(StubDebouncer):
            """Always reports the current task as inactive (newer task took over)."""
            async def is_task_active(self, chat_id, task_id):
                return False  # simulate immediate supersession

        llm = StubLLM("Resposta")
        gateway = StubGateway()
        memory = StubMemory()
        debouncer = SupersededDebouncer()

        build_context = BuildContextUseCase(memory=memory, config=config)
        uc = ProcessMessageUseCase(
            primary_llm=llm, fallback_llm=None,
            gateway=gateway, memory=memory, crm=StubCRM(),
            debouncer=debouncer, config=config, build_context=build_context,
        )

        await uc.execute("empresa_x", "5511@c.us", ["oi"], task_id="old-task-id")

        assert len(gateway.sent) == 0

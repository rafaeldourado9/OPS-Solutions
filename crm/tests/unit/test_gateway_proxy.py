import pytest

from core.domain.conversation import Conversation
from core.use_cases.conversations.handle_gateway_proxy import HandleGatewayProxyUseCase


@pytest.fixture
def use_case(agent_gateway, cache):
    """Basic proxy without message storage (backward-compatible)."""
    return HandleGatewayProxyUseCase(agent_gateway, cache)


@pytest.fixture
def use_case_full(agent_gateway, cache, conversation_repo, message_repo, tenant_repo, notification):
    """Full proxy with intercepted message storage."""
    return HandleGatewayProxyUseCase(
        agent_gateway, cache, conversation_repo, message_repo, tenant_repo, notification,
    )


def _make_gateway_payload(chat_id: str, text: str = "oi", session: str = "default") -> dict:
    return {
        "event": "message",
        "session": session,
        "payload": {
            "id": "msg123",
            "from": chat_id,
            "chatId": chat_id,
            "fromMe": False,
            "body": text,
            "hasMedia": False,
            "type": "chat",
            "timestamp": 1234567890,
            "pushName": "Maria",
        },
    }


async def test_forward_to_agents_when_no_takeover(use_case, agent_gateway):
    payload = _make_gateway_payload("5511999999999@c.us")
    result = await use_case.execute(payload)

    assert result["action"] == "forwarded"
    assert result["reason"] == "no_takeover"
    assert len(agent_gateway.forwarded_payloads) == 1
    assert agent_gateway.forwarded_payloads[0] == payload


async def test_intercept_when_takeover_active(use_case, agent_gateway, cache):
    await cache.set("takeover:default:5511999999999@c.us", '{"operator_id": "abc"}')

    payload = _make_gateway_payload("5511999999999@c.us")
    result = await use_case.execute(payload)

    assert result["action"] == "intercepted"
    assert result["reason"] == "takeover_active"
    assert len(agent_gateway.forwarded_payloads) == 0


async def test_forward_when_different_chat_has_takeover(use_case, agent_gateway, cache):
    await cache.set("takeover:default:OTHER_CHAT@c.us", '{"operator_id": "abc"}')

    payload = _make_gateway_payload("5511999999999@c.us")
    result = await use_case.execute(payload)

    assert result["action"] == "forwarded"
    assert len(agent_gateway.forwarded_payloads) == 1


async def test_forward_when_no_chat_id(use_case, agent_gateway):
    payload = {"event": "status", "session": "default", "payload": {}}
    result = await use_case.execute(payload)

    assert result["action"] == "forwarded"
    assert result["reason"] == "no_chat_id"
    assert len(agent_gateway.forwarded_payloads) == 1


async def test_intercept_stores_message_and_pushes_ws(
    use_case_full, cache, conversation_repo, message_repo, tenant_repo, notification, sample_tenant,
):
    # Setup: save tenant so it can be found by gateway_session
    await tenant_repo.save(sample_tenant)

    # Create conversation for the chat
    conv = Conversation.create(
        tenant_id=sample_tenant.id, chat_id="5511999999999@c.us", agent_id=sample_tenant.agent_id,
    )
    await conversation_repo.save(conv)

    # Set takeover
    await cache.set("takeover:default:5511999999999@c.us", "op123")

    payload = _make_gateway_payload("5511999999999@c.us", text="Preciso de ajuda")
    result = await use_case_full.execute(payload)

    assert result["action"] == "intercepted"

    # Message stored
    msgs, total = await message_repo.list_by_conversation(sample_tenant.id, conv.id)
    assert total == 1
    assert msgs[0].role == "user"
    assert msgs[0].content == "Preciso de ajuda"
    assert msgs[0].sender_name == "Maria"

    # Conversation updated
    updated = await conversation_repo.get_by_chat_id(sample_tenant.id, "5511999999999@c.us")
    assert updated.unread_count == 1
    assert updated.last_message_preview == "Preciso de ajuda"

    # WebSocket notification pushed
    assert len(notification.events) == 1
    assert notification.events[0][1] == "new_message"


async def test_intercept_creates_conversation_if_missing(
    use_case_full, cache, conversation_repo, tenant_repo, message_repo, sample_tenant,
):
    await tenant_repo.save(sample_tenant)
    await cache.set("takeover:default:5511888880000@c.us", "op123")

    payload = _make_gateway_payload("5511888880000@c.us", text="Ola")
    await use_case_full.execute(payload)

    # Conversation created
    conv = await conversation_repo.get_by_chat_id(sample_tenant.id, "5511888880000@c.us")
    assert conv is not None
    assert conv.customer_phone == "5511888880000"

    # Message stored
    msgs, _ = await message_repo.list_by_conversation(sample_tenant.id, conv.id)
    assert len(msgs) == 1

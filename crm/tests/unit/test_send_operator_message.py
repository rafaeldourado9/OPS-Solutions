from uuid import uuid4

import pytest

from core.domain.conversation import Conversation
from core.use_cases.conversations.send_operator_message import SendOperatorMessageUseCase


@pytest.fixture
def uc(conversation_repo, message_repo, whatsapp_gateway, notification):
    return SendOperatorMessageUseCase(conversation_repo, message_repo, whatsapp_gateway, notification)


async def test_sends_message_via_waha_and_stores(
    uc, conversation_repo, message_repo, whatsapp_gateway, notification, sample_tenant,
):
    conv = Conversation.create(tenant_id=sample_tenant.id, chat_id="123@w", agent_id="bot")
    conv.is_takeover_active = True
    conv.takeover_operator_id = uuid4()
    await conversation_repo.save(conv)

    operator_id = uuid4()
    msg = await uc.execute(
        tenant_id=sample_tenant.id,
        chat_id="123@w",
        operator_id=operator_id,
        operator_name="Carlos",
        content="Oi, sou o Carlos!",
    )

    # Message stored
    assert msg.role == "operator"
    assert msg.content == "Oi, sou o Carlos!"
    assert msg.sender_name == "Carlos"

    # WhatsApp gateway called
    assert len(whatsapp_gateway.sent_messages) == 1
    session, chat_id, text = whatsapp_gateway.sent_messages[0]
    assert session == "default"
    assert chat_id == "123@w"
    assert text == "Oi, sou o Carlos!"

    # Conversation updated
    updated = await conversation_repo.get_by_chat_id(sample_tenant.id, "123@w")
    assert updated.last_message_preview == "Oi, sou o Carlos!"

    # WebSocket notification
    assert len(notification.events) == 1
    assert notification.events[0][1] == "new_message"
    assert notification.events[0][2]["message"]["role"] == "operator"

    # Message in repo
    msgs, total = await message_repo.list_by_conversation(sample_tenant.id, conv.id)
    assert total == 1
    assert msgs[0].role == "operator"


async def test_fails_if_conversation_not_found(uc, sample_tenant):
    with pytest.raises(ValueError, match="Conversation not found"):
        await uc.execute(sample_tenant.id, "unknown@w", uuid4(), "Op", "Hi")


async def test_fails_if_takeover_not_active(uc, conversation_repo, sample_tenant):
    conv = Conversation.create(tenant_id=sample_tenant.id, chat_id="123@w", agent_id="bot")
    await conversation_repo.save(conv)

    with pytest.raises(ValueError, match="Takeover not active"):
        await uc.execute(sample_tenant.id, "123@w", uuid4(), "Op", "Hi")

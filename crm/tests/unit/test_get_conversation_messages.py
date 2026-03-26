from uuid import uuid4

import pytest

from core.domain.conversation import CRMMessage, Conversation
from core.use_cases.conversations.get_conversation_messages import GetConversationMessagesUseCase


@pytest.fixture
def uc(conversation_repo, message_repo):
    return GetConversationMessagesUseCase(conversation_repo, message_repo)


async def test_returns_messages_for_conversation(uc, conversation_repo, message_repo, sample_tenant):
    conv = Conversation.create(tenant_id=sample_tenant.id, chat_id="a@w", agent_id="bot")
    await conversation_repo.save(conv)

    m1 = CRMMessage.create(
        tenant_id=sample_tenant.id, conversation_id=conv.id,
        chat_id="a@w", role="user", content="Oi",
    )
    m2 = CRMMessage.create(
        tenant_id=sample_tenant.id, conversation_id=conv.id,
        chat_id="a@w", role="agent", content="Ola!",
    )
    await message_repo.save(m1)
    await message_repo.save(m2)

    result = await uc.execute(sample_tenant.id, "a@w")
    assert result.total == 2
    assert result.items[0].role == "user"
    assert result.items[1].role == "agent"


async def test_raises_for_unknown_conversation(uc, sample_tenant):
    with pytest.raises(ValueError, match="Conversation not found"):
        await uc.execute(sample_tenant.id, "nonexistent@w")


async def test_pagination(uc, conversation_repo, message_repo, sample_tenant):
    conv = Conversation.create(tenant_id=sample_tenant.id, chat_id="a@w", agent_id="bot")
    await conversation_repo.save(conv)

    for i in range(5):
        m = CRMMessage.create(
            tenant_id=sample_tenant.id, conversation_id=conv.id,
            chat_id="a@w", role="user", content=f"msg {i}",
        )
        await message_repo.save(m)

    result = await uc.execute(sample_tenant.id, "a@w", offset=0, limit=2)
    assert len(result.items) == 2
    assert result.total == 5


async def test_isolates_tenants(uc, conversation_repo, message_repo, sample_tenant):
    other_tenant = uuid4()
    conv = Conversation.create(tenant_id=other_tenant, chat_id="a@w", agent_id="bot")
    await conversation_repo.save(conv)

    with pytest.raises(ValueError):
        await uc.execute(sample_tenant.id, "a@w")

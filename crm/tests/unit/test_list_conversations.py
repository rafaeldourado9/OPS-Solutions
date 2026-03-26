from uuid import uuid4

import pytest

from core.domain.conversation import Conversation
from core.use_cases.conversations.list_conversations import ListConversationsUseCase


@pytest.fixture
def uc(conversation_repo):
    return ListConversationsUseCase(conversation_repo)


async def test_returns_empty_list(uc):
    result = await uc.execute(uuid4())
    assert result.items == []
    assert result.total == 0


async def test_lists_tenant_conversations(uc, conversation_repo, sample_tenant):
    c1 = Conversation.create(tenant_id=sample_tenant.id, chat_id="a@w", agent_id="bot")
    c2 = Conversation.create(tenant_id=sample_tenant.id, chat_id="b@w", agent_id="bot")
    await conversation_repo.save(c1)
    await conversation_repo.save(c2)

    result = await uc.execute(sample_tenant.id)
    assert result.total == 2
    assert len(result.items) == 2


async def test_filters_by_status(uc, conversation_repo, sample_tenant):
    c1 = Conversation.create(tenant_id=sample_tenant.id, chat_id="a@w", agent_id="bot")
    c2 = Conversation.create(tenant_id=sample_tenant.id, chat_id="b@w", agent_id="bot")
    c2.status = "closed"
    await conversation_repo.save(c1)
    await conversation_repo.save(c2)

    result = await uc.execute(sample_tenant.id, status="active")
    assert result.total == 1
    assert result.items[0].chat_id == "a@w"


async def test_pagination(uc, conversation_repo, sample_tenant):
    for i in range(5):
        c = Conversation.create(tenant_id=sample_tenant.id, chat_id=f"{i}@w", agent_id="bot")
        await conversation_repo.save(c)

    result = await uc.execute(sample_tenant.id, offset=0, limit=2)
    assert len(result.items) == 2
    assert result.total == 5


async def test_isolates_tenants(uc, conversation_repo, sample_tenant):
    other_tenant_id = uuid4()
    c1 = Conversation.create(tenant_id=sample_tenant.id, chat_id="a@w", agent_id="bot")
    c2 = Conversation.create(tenant_id=other_tenant_id, chat_id="b@w", agent_id="bot")
    await conversation_repo.save(c1)
    await conversation_repo.save(c2)

    result = await uc.execute(sample_tenant.id)
    assert result.total == 1
    assert result.items[0].chat_id == "a@w"

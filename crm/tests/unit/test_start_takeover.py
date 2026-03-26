from uuid import uuid4

import pytest

from core.domain.conversation import Conversation
from core.use_cases.conversations.start_takeover import StartTakeoverUseCase


@pytest.fixture
def uc(conversation_repo, cache, notification):
    return StartTakeoverUseCase(conversation_repo, cache, notification)


async def test_start_takeover_sets_redis_and_updates_conversation(
    uc, conversation_repo, cache, notification, sample_tenant,
):
    conv = Conversation.create(tenant_id=sample_tenant.id, chat_id="123@w", agent_id="bot")
    await conversation_repo.save(conv)
    operator_id = uuid4()

    await uc.execute(sample_tenant.id, "123@w", operator_id)

    # Conversation updated
    updated = await conversation_repo.get_by_chat_id(sample_tenant.id, "123@w")
    assert updated.is_takeover_active is True
    assert updated.takeover_operator_id == operator_id

    # Redis key set
    assert await cache.exists("takeover:default:123@w")

    # WebSocket notification sent
    assert len(notification.events) == 1
    assert notification.events[0][1] == "takeover_started"


async def test_start_takeover_fails_if_conversation_not_found(uc, sample_tenant):
    with pytest.raises(ValueError, match="Conversation not found"):
        await uc.execute(sample_tenant.id, "unknown@w", uuid4())


async def test_start_takeover_fails_if_already_active(
    uc, conversation_repo, sample_tenant,
):
    conv = Conversation.create(tenant_id=sample_tenant.id, chat_id="123@w", agent_id="bot")
    conv.is_takeover_active = True
    conv.takeover_operator_id = uuid4()
    await conversation_repo.save(conv)

    with pytest.raises(ValueError, match="Takeover already active"):
        await uc.execute(sample_tenant.id, "123@w", uuid4())

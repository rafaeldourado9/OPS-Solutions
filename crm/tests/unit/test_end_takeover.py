from uuid import uuid4

import pytest

from core.domain.conversation import Conversation
from core.use_cases.conversations.end_takeover import EndTakeoverUseCase


@pytest.fixture
def uc(conversation_repo, cache, notification):
    return EndTakeoverUseCase(conversation_repo, cache, notification)


async def test_end_takeover_clears_redis_and_updates_conversation(
    uc, conversation_repo, cache, notification, sample_tenant,
):
    operator_id = uuid4()
    conv = Conversation.create(tenant_id=sample_tenant.id, chat_id="123@w", agent_id="bot")
    conv.is_takeover_active = True
    conv.takeover_operator_id = operator_id
    await conversation_repo.save(conv)
    await cache.set("takeover:default:123@w", str(operator_id))

    await uc.execute(sample_tenant.id, "123@w")

    # Conversation updated
    updated = await conversation_repo.get_by_chat_id(sample_tenant.id, "123@w")
    assert updated.is_takeover_active is False
    assert updated.takeover_operator_id is None

    # Redis key deleted
    assert not await cache.exists("takeover:default:123@w")

    # WebSocket notification sent
    assert len(notification.events) == 1
    assert notification.events[0][1] == "takeover_ended"


async def test_end_takeover_fails_if_conversation_not_found(uc, sample_tenant):
    with pytest.raises(ValueError, match="Conversation not found"):
        await uc.execute(sample_tenant.id, "unknown@w")


async def test_end_takeover_fails_if_not_active(uc, conversation_repo, sample_tenant):
    conv = Conversation.create(tenant_id=sample_tenant.id, chat_id="123@w", agent_id="bot")
    await conversation_repo.save(conv)

    with pytest.raises(ValueError, match="No active takeover"):
        await uc.execute(sample_tenant.id, "123@w")

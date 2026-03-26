from uuid import uuid4

import pytest

from core.domain.customer import Customer
from core.domain.events import InboundAgentEvent
from core.use_cases.conversations.store_agent_event_message import StoreAgentEventMessageUseCase


@pytest.fixture
def uc(conversation_repo, message_repo, customer_repo, tenant_repo, notification):
    return StoreAgentEventMessageUseCase(
        conversation_repo, message_repo, customer_repo, tenant_repo, notification,
    )


@pytest.fixture
async def tenant_with_agent(tenant_repo, sample_tenant):
    await tenant_repo.save(sample_tenant)
    return sample_tenant


async def test_stores_user_message_and_creates_conversation(uc, tenant_with_agent, conversation_repo, message_repo, notification):
    tenant = tenant_with_agent
    event = InboundAgentEvent(
        event_type="message_received",
        chat_id="5511999990000@s.whatsapp.net",
        agent_id=tenant.agent_id,
        data={"content": "Ola, preciso de ajuda", "pushName": "Maria"},
    )

    msg = await uc.execute(event)

    assert msg is not None
    assert msg.role == "user"
    assert msg.content == "Ola, preciso de ajuda"
    assert msg.sender_name == "Maria"

    # Conversation was created
    conv = await conversation_repo.get_by_chat_id(tenant.id, event.chat_id)
    assert conv is not None
    assert conv.customer_phone == "5511999990000"
    assert conv.last_message_preview == "Ola, preciso de ajuda"
    assert conv.unread_count == 1

    # WebSocket notification was pushed
    assert len(notification.events) == 1
    assert notification.events[0][1] == "new_message"


async def test_stores_agent_response(uc, tenant_with_agent, conversation_repo):
    tenant = tenant_with_agent
    chat_id = "5511888880000@s.whatsapp.net"

    # First, create conversation via user message
    await uc.execute(InboundAgentEvent(
        event_type="message_received",
        chat_id=chat_id,
        agent_id=tenant.agent_id,
        data={"content": "Oi"},
    ))

    # Now agent responds
    msg = await uc.execute(InboundAgentEvent(
        event_type="agent_response_sent",
        chat_id=chat_id,
        agent_id=tenant.agent_id,
        data={"content": "Ola! Como posso ajudar?", "agent_name": "Bot Acme"},
    ))

    assert msg is not None
    assert msg.role == "agent"
    assert msg.content == "Ola! Como posso ajudar?"
    assert msg.sender_name == "Bot Acme"

    # Unread should still be 1 (only user messages increment)
    conv = await conversation_repo.get_by_chat_id(tenant.id, chat_id)
    assert conv.unread_count == 1


async def test_ignores_irrelevant_event_types(uc, tenant_with_agent):
    event = InboundAgentEvent(
        event_type="conversation_closed",
        chat_id="123@s.whatsapp.net",
        agent_id=tenant_with_agent.agent_id,
        data={},
    )
    result = await uc.execute(event)
    assert result is None


async def test_returns_none_for_unknown_agent(uc):
    event = InboundAgentEvent(
        event_type="message_received",
        chat_id="123@s.whatsapp.net",
        agent_id="nonexistent_agent",
        data={"content": "test"},
    )
    result = await uc.execute(event)
    assert result is None


async def test_links_existing_customer(uc, tenant_with_agent, customer_repo, conversation_repo):
    tenant = tenant_with_agent
    customer = Customer.create(
        tenant_id=tenant.id, name="Joao", phone="5511777770000",
    )
    await customer_repo.save(customer)

    event = InboundAgentEvent(
        event_type="message_received",
        chat_id="5511777770000@s.whatsapp.net",
        agent_id=tenant.agent_id,
        data={"content": "Oi"},
    )
    await uc.execute(event)

    conv = await conversation_repo.get_by_chat_id(tenant.id, event.chat_id)
    assert conv.customer_id == customer.id
    assert conv.customer_name == "Joao"


async def test_skips_empty_content(uc, tenant_with_agent):
    event = InboundAgentEvent(
        event_type="message_received",
        chat_id="5511666660000@s.whatsapp.net",
        agent_id=tenant_with_agent.agent_id,
        data={"content": ""},
    )
    result = await uc.execute(event)
    assert result is None

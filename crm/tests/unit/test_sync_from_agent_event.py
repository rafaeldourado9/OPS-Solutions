import pytest

from core.domain.events import InboundAgentEvent
from core.domain.tenant import Tenant
from core.use_cases.customers.sync_from_agent_event import SyncCustomerFromAgentEventUseCase


@pytest.fixture
async def seeded_tenant(tenant_repo):
    tenant = Tenant.create(slug="acme", name="Acme", agent_id="acme_agent")
    await tenant_repo.save(tenant)
    return tenant


@pytest.fixture
def use_case(customer_repo, tenant_repo):
    return SyncCustomerFromAgentEventUseCase(customer_repo, tenant_repo)


async def test_new_contact_creates_customer(use_case, seeded_tenant, customer_repo):
    event = InboundAgentEvent(
        event_type="new_contact",
        chat_id="5511999999999@c.us",
        agent_id="acme_agent",
        data={"pushName": "Joao"},
    )
    customer = await use_case.execute(event)

    assert customer is not None
    assert customer.name == "Joao"
    assert customer.phone == "5511999999999"
    assert customer.source == "whatsapp_auto"
    assert customer.chat_id == "5511999999999@c.us"

    saved = await customer_repo.get_by_phone(seeded_tenant.id, "5511999999999")
    assert saved is not None


async def test_new_contact_skips_existing_customer(use_case, seeded_tenant, customer_repo):
    event = InboundAgentEvent(
        event_type="new_contact",
        chat_id="5511999999999@c.us",
        agent_id="acme_agent",
        data={"pushName": "Joao"},
    )
    first = await use_case.execute(event)
    second = await use_case.execute(event)

    assert first.id == second.id  # same customer returned


async def test_ignores_non_new_contact_events(use_case, seeded_tenant):
    event = InboundAgentEvent(
        event_type="message_received",
        chat_id="5511999999999@c.us",
        agent_id="acme_agent",
        data={},
    )
    result = await use_case.execute(event)
    assert result is None


async def test_unknown_agent_returns_none(use_case):
    event = InboundAgentEvent(
        event_type="new_contact",
        chat_id="5511999999999@c.us",
        agent_id="unknown_agent",
        data={},
    )
    result = await use_case.execute(event)
    assert result is None

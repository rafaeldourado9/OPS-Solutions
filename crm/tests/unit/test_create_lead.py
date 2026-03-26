from uuid import uuid4

import pytest

from core.domain.lead import LeadStage
from core.use_cases.leads.create_lead import CreateLeadRequest, CreateLeadUseCase


@pytest.fixture
def uc(lead_repo):
    return CreateLeadUseCase(lead_repo)


async def test_create_lead_success(uc, sample_tenant):
    req = CreateLeadRequest(
        tenant_id=sample_tenant.id,
        title="Proposta para Joao",
        value=5000.0,
        source="whatsapp",
        tags=["urgente"],
    )
    lead = await uc.execute(req)

    assert lead.title == "Proposta para Joao"
    assert lead.stage == LeadStage.NEW
    assert lead.value == 5000.0
    assert lead.source == "whatsapp"
    assert lead.tags == ["urgente"]
    assert lead.tenant_id == sample_tenant.id


async def test_create_lead_with_customer(uc, sample_tenant):
    customer_id = uuid4()
    req = CreateLeadRequest(
        tenant_id=sample_tenant.id,
        title="Lead de teste",
        customer_id=customer_id,
    )
    lead = await uc.execute(req)
    assert lead.customer_id == customer_id


async def test_create_lead_with_assignment(uc, sample_tenant):
    user_id = uuid4()
    req = CreateLeadRequest(
        tenant_id=sample_tenant.id,
        title="Lead atribuido",
        assigned_to=user_id,
    )
    lead = await uc.execute(req)
    assert lead.assigned_to == user_id

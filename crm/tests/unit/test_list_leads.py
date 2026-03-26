from uuid import uuid4

import pytest

from core.domain.lead import Lead, LeadStage
from core.use_cases.leads.list_leads import ListLeadsUseCase


@pytest.fixture
def uc(lead_repo):
    return ListLeadsUseCase(lead_repo)


async def test_list_empty(uc, sample_tenant):
    result = await uc.execute(sample_tenant.id)
    assert result.items == []
    assert result.total == 0


async def test_list_with_leads(uc, lead_repo, sample_tenant):
    for i in range(3):
        lead = Lead.create(tenant_id=sample_tenant.id, title=f"Lead {i}")
        await lead_repo.save(lead)

    result = await uc.execute(sample_tenant.id)
    assert result.total == 3


async def test_filter_by_stage(uc, lead_repo, sample_tenant):
    l1 = Lead.create(tenant_id=sample_tenant.id, title="New lead")
    l2 = Lead.create(tenant_id=sample_tenant.id, title="Contacted lead")
    l2.stage = LeadStage.CONTACTED
    await lead_repo.save(l1)
    await lead_repo.save(l2)

    result = await uc.execute(sample_tenant.id, stage="contacted")
    assert result.total == 1
    assert result.items[0].title == "Contacted lead"


async def test_filter_by_assigned_to(uc, lead_repo, sample_tenant):
    user_id = uuid4()
    l1 = Lead.create(tenant_id=sample_tenant.id, title="Assigned", assigned_to=user_id)
    l2 = Lead.create(tenant_id=sample_tenant.id, title="Unassigned")
    await lead_repo.save(l1)
    await lead_repo.save(l2)

    result = await uc.execute(sample_tenant.id, assigned_to=user_id)
    assert result.total == 1
    assert result.items[0].title == "Assigned"


async def test_search_by_title(uc, lead_repo, sample_tenant):
    l1 = Lead.create(tenant_id=sample_tenant.id, title="Projeto solar")
    l2 = Lead.create(tenant_id=sample_tenant.id, title="Reforma escritorio")
    await lead_repo.save(l1)
    await lead_repo.save(l2)

    result = await uc.execute(sample_tenant.id, search="solar")
    assert result.total == 1
    assert result.items[0].title == "Projeto solar"


async def test_pagination(uc, lead_repo, sample_tenant):
    for i in range(5):
        await lead_repo.save(Lead.create(tenant_id=sample_tenant.id, title=f"L{i}"))

    result = await uc.execute(sample_tenant.id, offset=0, limit=2)
    assert len(result.items) == 2
    assert result.total == 5


async def test_tenant_isolation(uc, lead_repo, sample_tenant):
    other = uuid4()
    await lead_repo.save(Lead.create(tenant_id=sample_tenant.id, title="Mine"))
    await lead_repo.save(Lead.create(tenant_id=other, title="Other"))

    result = await uc.execute(sample_tenant.id)
    assert result.total == 1

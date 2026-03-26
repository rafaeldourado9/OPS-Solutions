import pytest

from core.domain.lead import Lead, LeadStage
from core.use_cases.leads.move_lead_stage import MoveLeadStageRequest, MoveLeadStageUseCase


@pytest.fixture
def uc(lead_repo):
    return MoveLeadStageUseCase(lead_repo)


async def test_move_new_to_contacted(uc, lead_repo, sample_tenant):
    lead = Lead.create(tenant_id=sample_tenant.id, title="Test")
    await lead_repo.save(lead)

    result = await uc.execute(MoveLeadStageRequest(
        tenant_id=sample_tenant.id, lead_id=lead.id, target_stage="contacted",
    ))
    assert result.stage == LeadStage.CONTACTED


async def test_full_pipeline_to_won(uc, lead_repo, sample_tenant):
    lead = Lead.create(tenant_id=sample_tenant.id, title="Big deal", value=10000)
    await lead_repo.save(lead)

    stages = ["contacted", "qualified", "proposal", "negotiation", "won"]
    for stage in stages:
        lead = await uc.execute(MoveLeadStageRequest(
            tenant_id=sample_tenant.id, lead_id=lead.id, target_stage=stage,
        ))
    assert lead.stage == LeadStage.WON
    assert lead.closed_at is not None


async def test_move_to_lost_with_reason(uc, lead_repo, sample_tenant):
    lead = Lead.create(tenant_id=sample_tenant.id, title="Lost deal")
    await lead_repo.save(lead)

    result = await uc.execute(MoveLeadStageRequest(
        tenant_id=sample_tenant.id,
        lead_id=lead.id,
        target_stage="lost",
        lost_reason="Preco alto",
    ))
    assert result.stage == LeadStage.LOST
    assert result.lost_reason == "Preco alto"
    assert result.closed_at is not None


async def test_reopen_lost_lead(uc, lead_repo, sample_tenant):
    lead = Lead.create(tenant_id=sample_tenant.id, title="Reopen")
    lead.move_to(LeadStage.LOST, lost_reason="test")
    await lead_repo.save(lead)

    result = await uc.execute(MoveLeadStageRequest(
        tenant_id=sample_tenant.id, lead_id=lead.id, target_stage="new",
    ))
    assert result.stage == LeadStage.NEW
    assert result.closed_at is None
    assert result.lost_reason == ""


async def test_invalid_transition_raises(uc, lead_repo, sample_tenant):
    lead = Lead.create(tenant_id=sample_tenant.id, title="Test")
    await lead_repo.save(lead)

    with pytest.raises(ValueError, match="Cannot move from 'new' to 'won'"):
        await uc.execute(MoveLeadStageRequest(
            tenant_id=sample_tenant.id, lead_id=lead.id, target_stage="won",
        ))


async def test_invalid_stage_value_raises(uc, lead_repo, sample_tenant):
    lead = Lead.create(tenant_id=sample_tenant.id, title="Test")
    await lead_repo.save(lead)

    with pytest.raises(ValueError, match="Invalid stage"):
        await uc.execute(MoveLeadStageRequest(
            tenant_id=sample_tenant.id, lead_id=lead.id, target_stage="nonexistent",
        ))


async def test_move_not_found_raises(uc, sample_tenant):
    from uuid import uuid4
    with pytest.raises(ValueError, match="Lead not found"):
        await uc.execute(MoveLeadStageRequest(
            tenant_id=sample_tenant.id, lead_id=uuid4(), target_stage="contacted",
        ))

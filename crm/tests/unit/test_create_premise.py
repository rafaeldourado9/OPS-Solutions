from uuid import uuid4

import pytest

from core.domain.premise import Premise, PremiseType
from core.use_cases.premises.create_premise import CreatePremiseRequest, CreatePremiseUseCase
from tests.conftest import FakePremiseRepository


@pytest.fixture
def uc(premise_repo):
    return CreatePremiseUseCase(premise_repo)


async def test_create_percentage_premise(uc, sample_tenant):
    req = CreatePremiseRequest(
        tenant_id=sample_tenant.id,
        name="Imposto",
        type="percentage",
        value=12.0,
        description="ISS 12%",
    )
    premise = await uc.execute(req)

    assert premise.name == "Imposto"
    assert premise.type == PremiseType.PERCENTAGE
    assert premise.value == 12.0
    assert premise.tenant_id == sample_tenant.id
    assert premise.is_active is True


async def test_create_fixed_premise(uc, sample_tenant):
    req = CreatePremiseRequest(
        tenant_id=sample_tenant.id,
        name="Locomoção",
        type="fixed",
        value=150.0,
    )
    premise = await uc.execute(req)

    assert premise.type == PremiseType.FIXED
    assert premise.value == 150.0


async def test_premise_apply_to_percentage(sample_tenant):
    premise = Premise.create(
        tenant_id=sample_tenant.id,
        name="Comissão",
        type=PremiseType.PERCENTAGE,
        value=10.0,
    )
    assert premise.apply_to(1000.0) == 100.0


async def test_premise_apply_to_fixed(sample_tenant):
    premise = Premise.create(
        tenant_id=sample_tenant.id,
        name="Taxa fixa",
        type=PremiseType.FIXED,
        value=200.0,
    )
    assert premise.apply_to(1000.0) == 200.0

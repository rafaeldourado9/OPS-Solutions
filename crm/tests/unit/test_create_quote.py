from uuid import uuid4

import pytest

from core.domain.premise import Premise, PremiseType
from core.domain.quote import QuoteStatus
from core.use_cases.quotes.create_quote import CreateQuoteRequest, CreateQuoteUseCase, QuoteItemInput
from core.use_cases.quotes.update_quote_status import UpdateQuoteStatusRequest, UpdateQuoteStatusUseCase
from core.use_cases.quotes.recalculate_quote import RecalculateQuoteRequest, RecalculateQuoteUseCase
from tests.conftest import FakePremiseRepository, FakeQuoteRepository


@pytest.fixture
def uc(quote_repo, premise_repo):
    return CreateQuoteUseCase(quote_repo, premise_repo)


async def test_create_quote_empty(uc, sample_tenant):
    req = CreateQuoteRequest(
        tenant_id=sample_tenant.id,
        title="Orçamento Teste",
    )
    quote = await uc.execute(req)

    assert quote.title == "Orçamento Teste"
    assert quote.status == QuoteStatus.DRAFT
    assert quote.items == []
    assert quote.applied_premises == []
    assert quote.total == 0.0
    assert quote.tenant_id == sample_tenant.id


async def test_create_quote_with_items(uc, sample_tenant):
    req = CreateQuoteRequest(
        tenant_id=sample_tenant.id,
        title="Instalação Elétrica",
        items=[
            QuoteItemInput(description="Cabo 10mm", quantity=100.0, unit_price=5.0),
            QuoteItemInput(description="Disjuntor", quantity=2.0, unit_price=80.0, discount=10.0),
        ],
    )
    quote = await uc.execute(req)

    assert len(quote.items) == 2
    # Cabo: 100 * 5 = 500
    # Disjuntor: 2 * 80 * 0.9 = 144
    assert quote.items_total == pytest.approx(644.0)


async def test_create_quote_with_premises(uc, sample_tenant, premise_repo):
    # Seed premises in repo
    iss = Premise.create(
        tenant_id=sample_tenant.id,
        name="ISS",
        type=PremiseType.PERCENTAGE,
        value=5.0,
    )
    comissao = Premise.create(
        tenant_id=sample_tenant.id,
        name="Comissão",
        type=PremiseType.PERCENTAGE,
        value=10.0,
    )
    await premise_repo.save(iss)
    await premise_repo.save(comissao)

    req = CreateQuoteRequest(
        tenant_id=sample_tenant.id,
        title="Com premissas",
        items=[QuoteItemInput(description="Serviço", quantity=1.0, unit_price=1000.0)],
        premise_ids=[iss.id, comissao.id],
    )
    quote = await uc.execute(req)

    assert quote.items_total == 1000.0
    assert len(quote.applied_premises) == 2
    # ISS: 5% of 1000 = 50, Comissão: 10% of 1000 = 100
    assert quote.premises_total == pytest.approx(150.0)
    assert quote.total == pytest.approx(1150.0)


async def test_update_quote_status(quote_repo, sample_tenant):
    # Create a draft quote first
    from core.domain.quote import Quote
    quote = Quote.create(tenant_id=sample_tenant.id, title="Q")
    await quote_repo.save(quote)

    uc = UpdateQuoteStatusUseCase(quote_repo)
    updated = await uc.execute(UpdateQuoteStatusRequest(
        tenant_id=sample_tenant.id,
        quote_id=quote.id,
        status="sent",
    ))
    assert updated.status == QuoteStatus.SENT


async def test_update_quote_status_invalid_transition(quote_repo, sample_tenant):
    from core.domain.quote import Quote
    quote = Quote.create(tenant_id=sample_tenant.id, title="Q")
    await quote_repo.save(quote)

    uc = UpdateQuoteStatusUseCase(quote_repo)
    with pytest.raises(ValueError, match="Cannot transition"):
        await uc.execute(UpdateQuoteStatusRequest(
            tenant_id=sample_tenant.id,
            quote_id=quote.id,
            status="approved",  # draft -> approved not allowed
        ))


async def test_recalculate_quote(quote_repo, premise_repo, sample_tenant):
    from core.domain.quote import Quote, QuoteItem
    quote = Quote.create(tenant_id=sample_tenant.id, title="Recalc")
    item = QuoteItem.create(quote_id=quote.id, description="Item", quantity=1.0, unit_price=500.0)
    quote.items.append(item)
    await quote_repo.save(quote)

    lucro = Premise.create(
        tenant_id=sample_tenant.id,
        name="Lucro",
        type=PremiseType.PERCENTAGE,
        value=20.0,
    )
    await premise_repo.save(lucro)

    uc = RecalculateQuoteUseCase(quote_repo, premise_repo)
    result = await uc.execute(RecalculateQuoteRequest(
        tenant_id=sample_tenant.id,
        quote_id=quote.id,
        premise_ids=[lucro.id],
    ))

    assert result.premises_total == pytest.approx(100.0)  # 20% of 500
    assert result.total == pytest.approx(600.0)

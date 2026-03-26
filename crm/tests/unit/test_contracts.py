import pytest

from core.domain.contract import ContractStatus
from core.domain.quote import Quote, QuoteStatus
from core.use_cases.contracts.create_contract import CreateContractRequest, CreateContractUseCase
from core.use_cases.contracts.list_contracts import ListContractsUseCase
from core.use_cases.contracts.update_contract_status import UpdateContractStatusRequest, UpdateContractStatusUseCase


async def test_create_contract_from_approved_quote(contract_repo, quote_repo, sample_tenant):
    quote = Quote.create(tenant_id=sample_tenant.id, title="Orcamento")
    quote.status = QuoteStatus.APPROVED
    await quote_repo.save(quote)

    uc = CreateContractUseCase(contract_repo, quote_repo)
    contract = await uc.execute(CreateContractRequest(
        tenant_id=sample_tenant.id,
        quote_id=quote.id,
        title="Contrato de Servico",
        content="Cláusulas...",
    ))

    assert contract.title == "Contrato de Servico"
    assert contract.status == ContractStatus.DRAFT
    assert contract.quote_id == quote.id
    assert contract.tenant_id == sample_tenant.id


async def test_create_contract_requires_approved_quote(contract_repo, quote_repo, sample_tenant):
    quote = Quote.create(tenant_id=sample_tenant.id, title="Orcamento")
    # Status is DRAFT by default
    await quote_repo.save(quote)

    uc = CreateContractUseCase(contract_repo, quote_repo)
    with pytest.raises(ValueError, match="approved quote"):
        await uc.execute(CreateContractRequest(
            tenant_id=sample_tenant.id,
            quote_id=quote.id,
            title="Contrato",
        ))


async def test_create_contract_duplicate_quote_raises(contract_repo, quote_repo, sample_tenant):
    quote = Quote.create(tenant_id=sample_tenant.id, title="Orcamento")
    quote.status = QuoteStatus.APPROVED
    await quote_repo.save(quote)

    uc = CreateContractUseCase(contract_repo, quote_repo)
    await uc.execute(CreateContractRequest(
        tenant_id=sample_tenant.id, quote_id=quote.id, title="Contrato 1"
    ))
    with pytest.raises(ValueError, match="already exists"):
        await uc.execute(CreateContractRequest(
            tenant_id=sample_tenant.id, quote_id=quote.id, title="Contrato 2"
        ))


async def test_create_contract_quote_not_found(contract_repo, quote_repo, sample_tenant):
    from uuid import uuid4
    uc = CreateContractUseCase(contract_repo, quote_repo)
    with pytest.raises(ValueError, match="Quote not found"):
        await uc.execute(CreateContractRequest(
            tenant_id=sample_tenant.id, quote_id=uuid4(), title="X"
        ))


async def test_update_contract_status_to_active(contract_repo, quote_repo, sample_tenant):
    quote = Quote.create(tenant_id=sample_tenant.id, title="Q")
    quote.status = QuoteStatus.APPROVED
    await quote_repo.save(quote)

    create_uc = CreateContractUseCase(contract_repo, quote_repo)
    contract = await create_uc.execute(CreateContractRequest(
        tenant_id=sample_tenant.id, quote_id=quote.id, title="C"
    ))

    update_uc = UpdateContractStatusUseCase(contract_repo)
    updated = await update_uc.execute(UpdateContractStatusRequest(
        tenant_id=sample_tenant.id,
        contract_id=contract.id,
        status="active",
    ))

    assert updated.status == ContractStatus.ACTIVE
    assert updated.signed_at is not None


async def test_update_contract_status_invalid_transition(contract_repo, quote_repo, sample_tenant):
    quote = Quote.create(tenant_id=sample_tenant.id, title="Q")
    quote.status = QuoteStatus.APPROVED
    await quote_repo.save(quote)

    create_uc = CreateContractUseCase(contract_repo, quote_repo)
    contract = await create_uc.execute(CreateContractRequest(
        tenant_id=sample_tenant.id, quote_id=quote.id, title="C"
    ))

    update_uc = UpdateContractStatusUseCase(contract_repo)
    with pytest.raises(ValueError, match="Cannot transition"):
        await update_uc.execute(UpdateContractStatusRequest(
            tenant_id=sample_tenant.id,
            contract_id=contract.id,
            status="completed",  # draft -> completed not allowed
        ))


async def test_list_contracts(contract_repo, quote_repo, sample_tenant):
    for i in range(3):
        quote = Quote.create(tenant_id=sample_tenant.id, title=f"Q{i}")
        quote.status = QuoteStatus.APPROVED
        await quote_repo.save(quote)
        from core.use_cases.contracts.create_contract import CreateContractUseCase as UC
        await UC(contract_repo, quote_repo).execute(
            CreateContractRequest(tenant_id=sample_tenant.id, quote_id=quote.id, title=f"C{i}")
        )

    uc = ListContractsUseCase(contract_repo)
    result = await uc.execute(sample_tenant.id)
    assert result.total == 3

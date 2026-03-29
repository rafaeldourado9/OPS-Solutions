from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.api.dependencies import (
    get_create_contract_uc,
    get_list_contracts_uc,
    get_update_contract_status_uc,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from adapters.outbound.persistence.database import get_session
from adapters.outbound.persistence.models.customer_model import CustomerModel
from adapters.outbound.persistence.models.quote_model import QuoteModel
from core.domain.contract import Contract
from core.use_cases.contracts.create_contract import CreateContractRequest, CreateContractUseCase
from core.use_cases.contracts.list_contracts import ListContractsUseCase
from core.use_cases.contracts.update_contract_status import UpdateContractStatusRequest, UpdateContractStatusUseCase

router = APIRouter(prefix="/api/v1/contracts", tags=["contracts"])


# --- Schemas ---

class ContractCreateBody(BaseModel):
    quote_id: str
    title: str
    content: str = ""
    expires_at: Optional[datetime] = None


class ContractStatusBody(BaseModel):
    status: str


class ContractOut(BaseModel):
    id: str
    tenant_id: str
    quote_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    title: str
    status: str
    value: float = 0.0
    content: str
    signed_at: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: str
    updated_at: str


class PaginatedContracts(BaseModel):
    items: list[ContractOut]
    total: int
    offset: int
    limit: int


def _compute_quote_value(quote: QuoteModel) -> float:
    items_total = sum(
        d["quantity"] * d["unit_price"] * (1 - d.get("discount", 0.0) / 100)
        for d in (quote.items_json or [])
    )
    premises_total = sum(d.get("amount", 0) for d in (quote.applied_premises_json or []))
    return round(items_total + premises_total, 2)


async def _enrich_contracts(
    contracts: list[Contract],
    session: AsyncSession,
    tenant_id: UUID,
) -> list[ContractOut]:
    # Batch-fetch customers and quotes to avoid N+1
    customer_ids = {c.customer_id for c in contracts if c.customer_id}
    quote_ids = {c.quote_id for c in contracts}

    customer_names: dict[UUID, str] = {}
    if customer_ids:
        cust_result = await session.execute(
            select(CustomerModel.id, CustomerModel.name).where(
                CustomerModel.id.in_(customer_ids),
                CustomerModel.tenant_id == tenant_id,
            )
        )
        customer_names = {row.id: row.name for row in cust_result}

    quote_values: dict[UUID, float] = {}
    if quote_ids:
        quote_result = await session.execute(
            select(QuoteModel).where(
                QuoteModel.id.in_(quote_ids),
                QuoteModel.tenant_id == tenant_id,
            )
        )
        for q in quote_result.scalars().all():
            quote_values[q.id] = _compute_quote_value(q)

    result = []
    for c in contracts:
        result.append(ContractOut(
            id=str(c.id),
            tenant_id=str(c.tenant_id),
            quote_id=str(c.quote_id),
            customer_id=str(c.customer_id) if c.customer_id else None,
            customer_name=customer_names.get(c.customer_id) if c.customer_id else None,
            title=c.title,
            status=c.status.value if hasattr(c.status, "value") else c.status,
            value=quote_values.get(c.quote_id, 0.0),
            content=c.content,
            signed_at=c.signed_at.isoformat() if c.signed_at else None,
            expires_at=c.expires_at.isoformat() if c.expires_at else None,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        ))
    return result


# --- Routes ---

@router.get("", response_model=PaginatedContracts)
async def list_contracts(
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListContractsUseCase = Depends(get_list_contracts_uc),
    session: AsyncSession = Depends(get_session),
):
    result = await uc.execute(
        current_user.tenant_id, status=status, offset=offset, limit=limit
    )
    enriched = await _enrich_contracts(result.items, session, current_user.tenant_id)
    return PaginatedContracts(
        items=enriched,
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post("", response_model=ContractOut, status_code=201)
async def create_contract(
    body: ContractCreateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: CreateContractUseCase = Depends(get_create_contract_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        contract = await uc.execute(CreateContractRequest(
            tenant_id=current_user.tenant_id,
            quote_id=UUID(body.quote_id),
            title=body.title,
            content=body.content,
            expires_at=body.expires_at,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await session.commit()
    enriched = await _enrich_contracts([contract], session, current_user.tenant_id)
    return enriched[0]


@router.patch("/{contract_id}/status", response_model=ContractOut)
async def update_contract_status(
    contract_id: UUID,
    body: ContractStatusBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: UpdateContractStatusUseCase = Depends(get_update_contract_status_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        contract = await uc.execute(UpdateContractStatusRequest(
            tenant_id=current_user.tenant_id,
            contract_id=contract_id,
            status=body.status,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await session.commit()
    enriched = await _enrich_contracts([contract], session, current_user.tenant_id)
    return enriched[0]

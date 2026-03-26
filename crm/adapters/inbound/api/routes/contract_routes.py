from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from adapters.inbound.api.dependencies import (
    get_create_contract_uc,
    get_list_contracts_uc,
    get_update_contract_status_uc,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
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
    title: str
    status: str
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


def _contract_out(c: Contract) -> ContractOut:
    return ContractOut(
        id=str(c.id),
        tenant_id=str(c.tenant_id),
        quote_id=str(c.quote_id),
        customer_id=str(c.customer_id) if c.customer_id else None,
        title=c.title,
        status=c.status.value if hasattr(c.status, "value") else c.status,
        content=c.content,
        signed_at=c.signed_at.isoformat() if c.signed_at else None,
        expires_at=c.expires_at.isoformat() if c.expires_at else None,
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat(),
    )


# --- Routes ---

@router.get("", response_model=PaginatedContracts)
async def list_contracts(
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListContractsUseCase = Depends(get_list_contracts_uc),
):
    result = await uc.execute(
        current_user.tenant_id, status=status, offset=offset, limit=limit
    )
    return PaginatedContracts(
        items=[_contract_out(c) for c in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post("", response_model=ContractOut, status_code=201)
async def create_contract(
    body: ContractCreateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: CreateContractUseCase = Depends(get_create_contract_uc),
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
    return _contract_out(contract)


@router.patch("/{contract_id}/status", response_model=ContractOut)
async def update_contract_status(
    contract_id: UUID,
    body: ContractStatusBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: UpdateContractStatusUseCase = Depends(get_update_contract_status_uc),
):
    try:
        contract = await uc.execute(UpdateContractStatusRequest(
            tenant_id=current_user.tenant_id,
            contract_id=contract_id,
            status=body.status,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _contract_out(contract)

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.api.dependencies import (
    get_create_customer_uc,
    get_customer_repo,
    get_list_customers_uc,
    get_update_customer_uc,
)
from adapters.inbound.api.middleware.auth import CurrentUser, get_current_user
from adapters.outbound.persistence.database import get_session
from core.ports.outbound.customer_repository import CustomerRepositoryPort
from core.use_cases.customers.create_customer import CreateCustomerRequest, CreateCustomerUseCase
from core.use_cases.customers.list_customers import ListCustomersUseCase
from core.use_cases.customers.update_customer import UpdateCustomerRequest, UpdateCustomerUseCase

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


# --- Schemas ---

class CustomerCreateBody(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    company_name: Optional[str] = None
    source: str = "manual"
    tags: Optional[list[str]] = None
    notes: str = ""


class CustomerUpdateBody(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    company_name: Optional[str] = None
    tags: Optional[list[str]] = None
    notes: Optional[str] = None
    address: Optional[dict] = None


class CustomerResponse(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    company_name: Optional[str] = None
    tags: list[str] = []
    notes: str = ""
    source: str = "manual"
    chat_id: Optional[str] = None
    is_active: bool = True
    created_at: str
    updated_at: str


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    offset: int
    limit: int


def _to_response(c) -> CustomerResponse:
    return CustomerResponse(
        id=str(c.id),
        name=c.name,
        phone=c.phone,
        email=c.email,
        cpf_cnpj=c.cpf_cnpj,
        company_name=c.company_name,
        tags=c.tags,
        notes=c.notes,
        source=c.source,
        chat_id=c.chat_id,
        is_active=c.is_active,
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat(),
    )


# --- Endpoints ---

@router.get("", response_model=CustomerListResponse)
async def list_customers(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user),
    uc: ListCustomersUseCase = Depends(get_list_customers_uc),
):
    result = await uc.execute(user.tenant_id, offset, limit, search)
    return CustomerListResponse(
        items=[_to_response(c) for c in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    body: CustomerCreateBody,
    user: CurrentUser = Depends(get_current_user),
    uc: CreateCustomerUseCase = Depends(get_create_customer_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        customer = await uc.execute(
            CreateCustomerRequest(
                tenant_id=user.tenant_id,
                name=body.name,
                phone=body.phone,
                email=body.email,
                cpf_cnpj=body.cpf_cnpj,
                company_name=body.company_name,
                source=body.source,
                tags=body.tags,
                notes=body.notes,
            )
        )
        await session.commit()
        return _to_response(customer)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    repo: CustomerRepositoryPort = Depends(get_customer_repo),
):
    customer = await repo.get_by_id(user.tenant_id, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return _to_response(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    body: CustomerUpdateBody,
    user: CurrentUser = Depends(get_current_user),
    uc: UpdateCustomerUseCase = Depends(get_update_customer_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        customer = await uc.execute(
            UpdateCustomerRequest(
                tenant_id=user.tenant_id,
                customer_id=customer_id,
                name=body.name,
                email=body.email,
                cpf_cnpj=body.cpf_cnpj,
                company_name=body.company_name,
                tags=body.tags,
                notes=body.notes,
                address=body.address,
            )
        )
        await session.commit()
        return _to_response(customer)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    repo: CustomerRepositoryPort = Depends(get_customer_repo),
    session: AsyncSession = Depends(get_session),
):
    deleted = await repo.delete(user.tenant_id, customer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Customer not found")
    await session.commit()

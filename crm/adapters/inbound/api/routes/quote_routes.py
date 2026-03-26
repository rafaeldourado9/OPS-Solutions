from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from adapters.inbound.api.dependencies import (
    get_create_quote_uc,
    get_get_quote_uc,
    get_list_quotes_uc,
    get_recalculate_quote_uc,
    get_update_quote_status_uc,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from core.domain.quote import AppliedPremise, Quote, QuoteItem
from core.use_cases.quotes.create_quote import CreateQuoteRequest, CreateQuoteUseCase, QuoteItemInput
from core.use_cases.quotes.get_quote import GetQuoteUseCase
from core.use_cases.quotes.list_quotes import ListQuotesUseCase
from core.use_cases.quotes.recalculate_quote import RecalculateQuoteRequest, RecalculateQuoteUseCase
from core.use_cases.quotes.update_quote_status import UpdateQuoteStatusRequest, UpdateQuoteStatusUseCase

router = APIRouter(prefix="/api/v1/quotes", tags=["quotes"])


# --- Schemas ---

class QuoteItemBody(BaseModel):
    description: str
    quantity: float
    unit_price: float
    discount: float = 0.0
    notes: str = ""


class QuoteCreateBody(BaseModel):
    title: str
    customer_id: Optional[str] = None
    lead_id: Optional[str] = None
    notes: str = ""
    valid_until: Optional[datetime] = None
    currency: str = "BRL"
    items: list[QuoteItemBody] = []
    premise_ids: list[str] = []


class QuoteStatusBody(BaseModel):
    status: str


class RecalculateBody(BaseModel):
    premise_ids: list[str] = []


class QuoteItemOut(BaseModel):
    id: str
    description: str
    quantity: float
    unit_price: float
    discount: float
    subtotal: float
    notes: str


class AppliedPremiseOut(BaseModel):
    premise_id: str
    name: str
    type: str
    value: float
    amount: float


class QuoteOut(BaseModel):
    id: str
    tenant_id: str
    customer_id: Optional[str] = None
    lead_id: Optional[str] = None
    title: str
    status: str
    items: list[QuoteItemOut]
    applied_premises: list[AppliedPremiseOut]
    items_total: float
    premises_total: float
    total: float
    notes: str
    valid_until: Optional[str] = None
    currency: str
    created_at: str
    updated_at: str


class PaginatedQuotes(BaseModel):
    items: list[QuoteOut]
    total: int
    offset: int
    limit: int


def _item_out(item: QuoteItem) -> QuoteItemOut:
    return QuoteItemOut(
        id=str(item.id),
        description=item.description,
        quantity=item.quantity,
        unit_price=item.unit_price,
        discount=item.discount,
        subtotal=item.subtotal,
        notes=item.notes,
    )


def _ap_out(ap: AppliedPremise) -> AppliedPremiseOut:
    return AppliedPremiseOut(
        premise_id=str(ap.premise_id),
        name=ap.name,
        type=ap.type,
        value=ap.value,
        amount=ap.amount,
    )


def _quote_out(q: Quote) -> QuoteOut:
    return QuoteOut(
        id=str(q.id),
        tenant_id=str(q.tenant_id),
        customer_id=str(q.customer_id) if q.customer_id else None,
        lead_id=str(q.lead_id) if q.lead_id else None,
        title=q.title,
        status=q.status.value if hasattr(q.status, "value") else q.status,
        items=[_item_out(i) for i in q.items],
        applied_premises=[_ap_out(ap) for ap in q.applied_premises],
        items_total=q.items_total,
        premises_total=q.premises_total,
        total=q.total,
        notes=q.notes,
        valid_until=q.valid_until.isoformat() if q.valid_until else None,
        currency=q.currency,
        created_at=q.created_at.isoformat(),
        updated_at=q.updated_at.isoformat(),
    )


# --- Routes ---

@router.get("", response_model=PaginatedQuotes)
async def list_quotes(
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    lead_id: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListQuotesUseCase = Depends(get_list_quotes_uc),
):
    result = await uc.execute(
        current_user.tenant_id,
        status=status,
        customer_id=UUID(customer_id) if customer_id else None,
        lead_id=UUID(lead_id) if lead_id else None,
        offset=offset,
        limit=limit,
    )
    return PaginatedQuotes(
        items=[_quote_out(q) for q in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post("", response_model=QuoteOut, status_code=201)
async def create_quote(
    body: QuoteCreateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: CreateQuoteUseCase = Depends(get_create_quote_uc),
):
    quote = await uc.execute(CreateQuoteRequest(
        tenant_id=current_user.tenant_id,
        title=body.title,
        customer_id=UUID(body.customer_id) if body.customer_id else None,
        lead_id=UUID(body.lead_id) if body.lead_id else None,
        notes=body.notes,
        valid_until=body.valid_until,
        currency=body.currency,
        items=[
            QuoteItemInput(
                description=i.description,
                quantity=i.quantity,
                unit_price=i.unit_price,
                discount=i.discount,
                notes=i.notes,
            )
            for i in body.items
        ],
        premise_ids=[UUID(p) for p in body.premise_ids],
    ))
    return _quote_out(quote)


@router.get("/{quote_id}", response_model=QuoteOut)
async def get_quote(
    quote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    uc: GetQuoteUseCase = Depends(get_get_quote_uc),
):
    try:
        quote = await uc.execute(current_user.tenant_id, quote_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Quote not found")
    return _quote_out(quote)


@router.patch("/{quote_id}/status", response_model=QuoteOut)
async def update_quote_status(
    quote_id: UUID,
    body: QuoteStatusBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: UpdateQuoteStatusUseCase = Depends(get_update_quote_status_uc),
):
    try:
        quote = await uc.execute(UpdateQuoteStatusRequest(
            tenant_id=current_user.tenant_id,
            quote_id=quote_id,
            status=body.status,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _quote_out(quote)


@router.post("/{quote_id}/recalculate", response_model=QuoteOut)
async def recalculate_quote(
    quote_id: UUID,
    body: RecalculateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: RecalculateQuoteUseCase = Depends(get_recalculate_quote_uc),
):
    try:
        quote = await uc.execute(RecalculateQuoteRequest(
            tenant_id=current_user.tenant_id,
            quote_id=quote_id,
            premise_ids=[UUID(p) for p in body.premise_ids],
        ))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _quote_out(quote)


@router.delete("/{quote_id}", status_code=204)
async def delete_quote(
    quote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    return None

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.api.dependencies import (
    get_create_quote_uc,
    get_generate_quotes_report_uc,
    get_generate_single_quote_pdf_uc,
    get_get_quote_uc,
    get_list_quotes_uc,
    get_quote_repo,
    get_recalculate_quote_uc,
    get_update_quote_status_uc,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from adapters.outbound.persistence.database import get_session, async_session_factory
from adapters.outbound.persistence.models.customer_model import CustomerModel
from adapters.outbound.persistence.models.user_model import UserModel
from adapters.outbound.persistence.models.tenant_model import TenantModel
from adapters.outbound.email.smtp_adapter import SmtpEmailAdapter
from adapters.outbound.email import templates as email_tmpl
from infrastructure.config import settings as app_settings
from core.ports.outbound.quote_repository import QuoteRepositoryPort
from core.domain.quote import AppliedPremise, Quote, QuoteItem
from sqlalchemy import select
from core.use_cases.quotes.create_quote import CreateQuoteRequest, CreateQuoteUseCase, QuoteItemInput
from core.use_cases.quotes.get_quote import GetQuoteUseCase
from core.use_cases.quotes.list_quotes import ListQuotesUseCase
from core.use_cases.quotes.recalculate_quote import RecalculateQuoteRequest, RecalculateQuoteUseCase
from core.use_cases.quotes.update_quote_status import UpdateQuoteStatusRequest, UpdateQuoteStatusUseCase
from core.use_cases.quotes.generate_quotes_report import GenerateQuotesReportUseCase
from core.use_cases.quotes.generate_single_quote_pdf import GenerateSingleQuotePdfUseCase

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
    sale_price: Optional[float] = None


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
    customer_name: Optional[str] = None
    lead_id: Optional[str] = None
    title: str
    status: str
    items: list[QuoteItemOut]
    applied_premises: list[AppliedPremiseOut]
    items_total: float
    premises_total: float
    sale_price: Optional[float] = None
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


def _quote_out(q: Quote, customer_name: Optional[str] = None) -> QuoteOut:
    return QuoteOut(
        id=str(q.id),
        tenant_id=str(q.tenant_id),
        customer_id=str(q.customer_id) if q.customer_id else None,
        customer_name=customer_name,
        lead_id=str(q.lead_id) if q.lead_id else None,
        title=q.title,
        status=q.status.value if hasattr(q.status, "value") else q.status,
        items=[_item_out(i) for i in q.items],
        applied_premises=[_ap_out(ap) for ap in q.applied_premises],
        items_total=q.items_total,
        premises_total=q.premises_total,
        sale_price=q.sale_price,
        total=q.total,
        notes=q.notes,
        valid_until=q.valid_until.isoformat() if q.valid_until else None,
        currency=q.currency,
        created_at=q.created_at.isoformat(),
        updated_at=q.updated_at.isoformat(),
    )


async def _resolve_customer_names(
    quotes: list[Quote],
    session: AsyncSession,
    tenant_id: UUID,
) -> dict[UUID, str]:
    customer_ids = {q.customer_id for q in quotes if q.customer_id}
    if not customer_ids:
        return {}
    result = await session.execute(
        select(CustomerModel.id, CustomerModel.name).where(
            CustomerModel.id.in_(customer_ids),
            CustomerModel.tenant_id == tenant_id,
        )
    )
    return {row.id: row.name for row in result}


from fastapi.responses import Response


@router.get("/report/pdf")
async def generate_quotes_report(
    current_user: CurrentUser = Depends(get_current_user),
    uc: GenerateQuotesReportUseCase = Depends(get_generate_quotes_report_uc),
    session: AsyncSession = Depends(get_session),
):
    # Resolve customer names for the report
    from adapters.outbound.persistence.models.customer_model import CustomerModel as CM
    result = await session.execute(
        select(CM.id, CM.name).where(CM.tenant_id == current_user.tenant_id)
    )
    customer_names = {row.id: row.name for row in result}

    try:
        pdf_bytes = await uc.execute(current_user.tenant_id, customer_names)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio-orcamentos.pdf"},
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
    session: AsyncSession = Depends(get_session),
):
    result = await uc.execute(
        current_user.tenant_id,
        status=status,
        customer_id=UUID(customer_id) if customer_id else None,
        lead_id=UUID(lead_id) if lead_id else None,
        offset=offset,
        limit=limit,
    )
    names = await _resolve_customer_names(result.items, session, current_user.tenant_id)
    return PaginatedQuotes(
        items=[_quote_out(q, names.get(q.customer_id)) for q in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post("", response_model=QuoteOut, status_code=201)
async def create_quote(
    body: QuoteCreateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: CreateQuoteUseCase = Depends(get_create_quote_uc),
    session: AsyncSession = Depends(get_session),
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
        sale_price=body.sale_price,
    ))
    await session.commit()
    names = await _resolve_customer_names([quote], session, current_user.tenant_id)
    return _quote_out(quote, names.get(quote.customer_id))


@router.get("/{quote_id}", response_model=QuoteOut)
async def get_quote(
    quote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    uc: GetQuoteUseCase = Depends(get_get_quote_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        quote = await uc.execute(current_user.tenant_id, quote_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Quote not found")
    names = await _resolve_customer_names([quote], session, current_user.tenant_id)
    return _quote_out(quote, names.get(quote.customer_id))


@router.patch("/{quote_id}/status", response_model=QuoteOut)
async def update_quote_status(
    quote_id: UUID,
    body: QuoteStatusBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: UpdateQuoteStatusUseCase = Depends(get_update_quote_status_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        quote = await uc.execute(UpdateQuoteStatusRequest(
            tenant_id=current_user.tenant_id,
            quote_id=quote_id,
            status=body.status,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await session.commit()
    names = await _resolve_customer_names([quote], session, current_user.tenant_id)

    # Fire-and-forget: notify admin when quote is accepted
    if body.status == "accepted":
        import asyncio as _asyncio

        _q, _names, _tid = quote, names, current_user.tenant_id

        async def _notify_accepted() -> None:
            try:
                async with async_session_factory() as s:
                    admin_res = await s.execute(
                        select(UserModel).where(
                            UserModel.tenant_id == _tid,
                            UserModel.role == "admin",
                            UserModel.is_active == True,
                        ).limit(1)
                    )
                    admin = admin_res.scalar_one_or_none()
                    tenant_res = await s.execute(
                        select(TenantModel).where(TenantModel.id == _tid)
                    )
                    tenant = tenant_res.scalar_one_or_none()
                    if not admin or not tenant:
                        return
                    subject, html = email_tmpl.quote_accepted(
                        name=admin.name,
                        tenant_name=tenant.name,
                        quote_title=_q.title,
                        customer_name=_names.get(_q.customer_id, "") or "",
                        total=_q.total,
                        quote_id=str(_q.id),
                        app_url=app_settings.app_url,
                    )
                    await SmtpEmailAdapter().send(to=admin.email, subject=subject, html=html)
            except Exception:
                pass

        _asyncio.create_task(_notify_accepted())

    return _quote_out(quote, names.get(quote.customer_id))


@router.post("/{quote_id}/recalculate", response_model=QuoteOut)
async def recalculate_quote(
    quote_id: UUID,
    body: RecalculateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: RecalculateQuoteUseCase = Depends(get_recalculate_quote_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        quote = await uc.execute(RecalculateQuoteRequest(
            tenant_id=current_user.tenant_id,
            quote_id=quote_id,
            premise_ids=[UUID(p) for p in body.premise_ids],
        ))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    await session.commit()
    names = await _resolve_customer_names([quote], session, current_user.tenant_id)
    return _quote_out(quote, names.get(quote.customer_id))


@router.get("/{quote_id}/pdf")
async def generate_single_quote_pdf(
    quote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    uc: GenerateSingleQuotePdfUseCase = Depends(get_generate_single_quote_pdf_uc),
    session: AsyncSession = Depends(get_session),
):
    # Resolve customer name for the PDF header
    from adapters.outbound.persistence.models.quote_model import QuoteModel
    from sqlalchemy import select as sa_select
    stmt = sa_select(QuoteModel).where(
        QuoteModel.id == quote_id,
        QuoteModel.tenant_id == current_user.tenant_id,
    )
    result = await session.execute(stmt)
    qmodel = result.scalar_one_or_none()
    customer_name: Optional[str] = None
    if qmodel and qmodel.customer_id:
        from adapters.outbound.persistence.models.customer_model import CustomerModel as CM2
        cresult = await session.execute(
            sa_select(CM2.name).where(
                CM2.id == qmodel.customer_id,
                CM2.tenant_id == current_user.tenant_id,
            )
        )
        customer_name = cresult.scalar_one_or_none()

    try:
        pdf_bytes = await uc.execute(current_user.tenant_id, quote_id, customer_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=proposta-{quote_id}.pdf"},
    )


@router.delete("/{quote_id}", status_code=204)
async def delete_quote(
    quote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    repo: QuoteRepositoryPort = Depends(get_quote_repo),
    session: AsyncSession = Depends(get_session),
):
    deleted = await repo.delete(current_user.tenant_id, quote_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Quote not found")
    await session.commit()

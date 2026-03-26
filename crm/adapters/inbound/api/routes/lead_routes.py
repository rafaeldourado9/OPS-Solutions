from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from adapters.inbound.api.dependencies import (
    get_create_lead_uc,
    get_lead_uc,
    get_list_leads_uc,
    get_move_lead_stage_uc,
    get_update_lead_uc,
)
from adapters.inbound.api.middleware.auth import CurrentUser, get_current_user
from core.domain.lead import Lead
from core.use_cases.leads.create_lead import CreateLeadRequest, CreateLeadUseCase
from core.use_cases.leads.get_lead import GetLeadUseCase
from core.use_cases.leads.list_leads import ListLeadsUseCase
from core.use_cases.leads.move_lead_stage import MoveLeadStageRequest, MoveLeadStageUseCase
from core.use_cases.leads.update_lead import UpdateLeadRequest, UpdateLeadUseCase

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])


# --- Schemas ---

class LeadCreateBody(BaseModel):
    title: str
    customer_id: Optional[str] = None
    value: float = 0.0
    source: str = "manual"
    assigned_to: Optional[str] = None
    notes: str = ""
    expected_close_date: Optional[datetime] = None
    tags: list[str] = []


class LeadUpdateBody(BaseModel):
    title: Optional[str] = None
    customer_id: Optional[str] = None
    value: Optional[float] = None
    source: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    expected_close_date: Optional[datetime] = None
    tags: Optional[list[str]] = None


class MoveStageBody(BaseModel):
    stage: str
    lost_reason: str = ""


class LeadOut(BaseModel):
    id: str
    tenant_id: str
    customer_id: Optional[str] = None
    title: str
    stage: str
    value: float
    currency: str
    source: str
    assigned_to: Optional[str] = None
    notes: str
    expected_close_date: Optional[str] = None
    closed_at: Optional[str] = None
    lost_reason: str
    tags: list[str]
    created_at: str
    updated_at: str


class PaginatedLeads(BaseModel):
    items: list[LeadOut]
    total: int
    offset: int
    limit: int


def _lead_out(lead: Lead) -> LeadOut:
    return LeadOut(
        id=str(lead.id),
        tenant_id=str(lead.tenant_id),
        customer_id=str(lead.customer_id) if lead.customer_id else None,
        title=lead.title,
        stage=lead.stage.value if hasattr(lead.stage, "value") else lead.stage,
        value=lead.value,
        currency=lead.currency,
        source=lead.source,
        assigned_to=str(lead.assigned_to) if lead.assigned_to else None,
        notes=lead.notes,
        expected_close_date=lead.expected_close_date.isoformat() if lead.expected_close_date else None,
        closed_at=lead.closed_at.isoformat() if lead.closed_at else None,
        lost_reason=lead.lost_reason,
        tags=lead.tags,
        created_at=lead.created_at.isoformat(),
        updated_at=lead.updated_at.isoformat(),
    )


# --- Routes ---

@router.get("", response_model=PaginatedLeads)
async def list_leads(
    stage: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListLeadsUseCase = Depends(get_list_leads_uc),
):
    result = await uc.execute(
        current_user.tenant_id,
        stage=stage,
        assigned_to=UUID(assigned_to) if assigned_to else None,
        search=search,
        offset=offset,
        limit=limit,
    )
    return PaginatedLeads(
        items=[_lead_out(l) for l in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post("", response_model=LeadOut, status_code=201)
async def create_lead(
    body: LeadCreateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: CreateLeadUseCase = Depends(get_create_lead_uc),
):
    lead = await uc.execute(CreateLeadRequest(
        tenant_id=current_user.tenant_id,
        title=body.title,
        customer_id=UUID(body.customer_id) if body.customer_id else None,
        value=body.value,
        source=body.source,
        assigned_to=UUID(body.assigned_to) if body.assigned_to else None,
        notes=body.notes,
        expected_close_date=body.expected_close_date,
        tags=body.tags,
    ))
    return _lead_out(lead)


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(
    lead_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    uc: GetLeadUseCase = Depends(get_lead_uc),
):
    try:
        lead = await uc.execute(current_user.tenant_id, lead_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _lead_out(lead)


@router.put("/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: UUID,
    body: LeadUpdateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: UpdateLeadUseCase = Depends(get_update_lead_uc),
):
    try:
        lead = await uc.execute(UpdateLeadRequest(
            tenant_id=current_user.tenant_id,
            lead_id=lead_id,
            title=body.title,
            customer_id=UUID(body.customer_id) if body.customer_id else None,
            value=body.value,
            source=body.source,
            assigned_to=UUID(body.assigned_to) if body.assigned_to else None,
            notes=body.notes,
            expected_close_date=body.expected_close_date,
            tags=body.tags,
        ))
    except ValueError:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _lead_out(lead)


@router.patch("/{lead_id}/stage", response_model=LeadOut)
async def move_lead_stage(
    lead_id: UUID,
    body: MoveStageBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: MoveLeadStageUseCase = Depends(get_move_lead_stage_uc),
):
    try:
        lead = await uc.execute(MoveLeadStageRequest(
            tenant_id=current_user.tenant_id,
            lead_id=lead_id,
            target_stage=body.stage,
            lost_reason=body.lost_reason,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _lead_out(lead)


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(
    lead_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    # Delete will be handled via dependency when needed
    # For now just return 204
    return None

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from adapters.inbound.api.dependencies import (
    get_create_premise_uc,
    get_delete_premise_uc,
    get_list_premises_uc,
    get_update_premise_uc,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from core.domain.premise import Premise
from core.use_cases.premises.create_premise import CreatePremiseRequest, CreatePremiseUseCase
from core.use_cases.premises.delete_premise import DeletePremiseUseCase
from core.use_cases.premises.list_premises import ListPremisesUseCase
from core.use_cases.premises.update_premise import UpdatePremiseRequest, UpdatePremiseUseCase

router = APIRouter(prefix="/api/v1/premises", tags=["premises"])


# --- Schemas ---

class PremiseCreateBody(BaseModel):
    name: str
    type: str  # "percentage" or "fixed"
    value: float
    description: str = ""


class PremiseUpdateBody(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    value: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PremiseOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    type: str
    value: float
    description: str
    is_active: bool
    created_at: str
    updated_at: str


def _premise_out(p: Premise) -> PremiseOut:
    return PremiseOut(
        id=str(p.id),
        tenant_id=str(p.tenant_id),
        name=p.name,
        type=p.type.value if hasattr(p.type, "value") else p.type,
        value=p.value,
        description=p.description,
        is_active=p.is_active,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


# --- Routes ---

@router.get("", response_model=list[PremiseOut])
async def list_premises(
    active_only: bool = Query(True),
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListPremisesUseCase = Depends(get_list_premises_uc),
):
    premises = await uc.execute(current_user.tenant_id, active_only=active_only)
    return [_premise_out(p) for p in premises]


@router.post("", response_model=PremiseOut, status_code=201)
async def create_premise(
    body: PremiseCreateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: CreatePremiseUseCase = Depends(get_create_premise_uc),
):
    try:
        premise = await uc.execute(CreatePremiseRequest(
            tenant_id=current_user.tenant_id,
            name=body.name,
            type=body.type,
            value=body.value,
            description=body.description,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _premise_out(premise)


@router.put("/{premise_id}", response_model=PremiseOut)
async def update_premise(
    premise_id: UUID,
    body: PremiseUpdateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: UpdatePremiseUseCase = Depends(get_update_premise_uc),
):
    try:
        premise = await uc.execute(UpdatePremiseRequest(
            tenant_id=current_user.tenant_id,
            premise_id=premise_id,
            name=body.name,
            type=body.type,
            value=body.value,
            description=body.description,
            is_active=body.is_active,
        ))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _premise_out(premise)


@router.delete("/{premise_id}", status_code=204)
async def delete_premise(
    premise_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    uc: DeletePremiseUseCase = Depends(get_delete_premise_uc),
):
    try:
        await uc.execute(current_user.tenant_id, premise_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

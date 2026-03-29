from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel

from adapters.inbound.api.dependencies import (
    get_upload_contract_template_uc,
    get_list_contract_templates_uc,
    get_delete_contract_template_uc,
    get_generate_contract_uc,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from core.use_cases.contracts.upload_contract_template import UploadContractTemplateUseCase
from core.use_cases.contracts.list_contract_templates import ListContractTemplatesUseCase
from core.use_cases.contracts.delete_contract_template import DeleteContractTemplateUseCase
from core.use_cases.contracts.generate_contract import GenerateContractUseCase

router = APIRouter(prefix="/api/v1/contract-templates", tags=["contract-templates"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class ContractTemplateOut(BaseModel):
    id: str
    name: str
    description: str
    variables: list[str]
    created_at: str


class GenerateContractBody(BaseModel):
    variable_values: dict[str, str] = {}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ContractTemplateOut, status_code=201)
async def upload_contract_template(
    name: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    uc: UploadContractTemplateUseCase = Depends(get_upload_contract_template_uc),
):
    docx_bytes = await file.read()
    try:
        template = await uc.execute(
            tenant_id=current_user.tenant_id,
            name=name,
            description=description,
            docx_bytes=docx_bytes,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ContractTemplateOut(
        id=str(template.id),
        name=template.name,
        description=template.description,
        variables=template.variables,
        created_at=template.created_at.isoformat(),
    )


@router.get("", response_model=list[ContractTemplateOut])
async def list_contract_templates(
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListContractTemplatesUseCase = Depends(get_list_contract_templates_uc),
):
    templates = await uc.execute(current_user.tenant_id)
    return [
        ContractTemplateOut(
            id=str(t.id),
            name=t.name,
            description=t.description,
            variables=t.variables,
            created_at=t.created_at.isoformat(),
        )
        for t in templates
    ]


@router.delete("/{template_id}", status_code=204)
async def delete_contract_template(
    template_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    uc: DeleteContractTemplateUseCase = Depends(get_delete_contract_template_uc),
):
    deleted = await uc.execute(current_user.tenant_id, template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contract template not found")


@router.post("/{template_id}/generate")
async def generate_contract(
    template_id: UUID,
    body: GenerateContractBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: GenerateContractUseCase = Depends(get_generate_contract_uc),
):
    try:
        pdf_bytes = await uc.execute(
            tenant_id=current_user.tenant_id,
            template_id=template_id,
            variable_values=body.variable_values,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate contract: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=contrato-{template_id}.pdf"},
    )

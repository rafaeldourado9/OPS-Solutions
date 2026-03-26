from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from adapters.inbound.api.dependencies import (
    get_delete_quote_template_uc,
    get_generate_quote_document_uc,
    get_list_quote_templates_uc,
    get_upload_quote_template_uc,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from core.domain.quote_template import QuoteTemplate
from core.use_cases.quotes.delete_quote_template import DeleteQuoteTemplateUseCase
from core.use_cases.quotes.generate_quote_document import GenerateQuoteDocumentRequest, GenerateQuoteDocumentUseCase
from core.use_cases.quotes.list_quote_templates import ListQuoteTemplatesUseCase
from core.use_cases.quotes.upload_quote_template import UploadQuoteTemplateRequest, UploadQuoteTemplateUseCase

router = APIRouter(prefix="/api/v1/quote-templates", tags=["quote-templates"])


# --- Schemas ---

class QuoteTemplateOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str
    placeholders: list[str]
    created_at: str
    updated_at: str


class GenerateDocumentBody(BaseModel):
    extra_context: dict[str, str] = {}


class GeneratedDocumentOut(BaseModel):
    quote_id: str
    template_id: str
    pdf_url: str
    docx_url: str


def _template_out(t: QuoteTemplate) -> QuoteTemplateOut:
    return QuoteTemplateOut(
        id=str(t.id),
        tenant_id=str(t.tenant_id),
        name=t.name,
        description=t.description,
        placeholders=t.placeholders,
        created_at=t.created_at.isoformat(),
        updated_at=t.updated_at.isoformat(),
    )


# --- Routes ---

@router.get("", response_model=list[QuoteTemplateOut])
async def list_quote_templates(
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListQuoteTemplatesUseCase = Depends(get_list_quote_templates_uc),
):
    templates = await uc.execute(current_user.tenant_id)
    return [_template_out(t) for t in templates]


@router.post("", response_model=QuoteTemplateOut, status_code=201)
async def upload_quote_template(
    name: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    uc: UploadQuoteTemplateUseCase = Depends(get_upload_quote_template_uc),
):
    if not file.filename or not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are accepted")

    docx_bytes = await file.read()
    try:
        template = await uc.execute(UploadQuoteTemplateRequest(
            tenant_id=current_user.tenant_id,
            name=name,
            description=description,
            docx_bytes=docx_bytes,
        ))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _template_out(template)


@router.delete("/{template_id}", status_code=204)
async def delete_quote_template(
    template_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    uc: DeleteQuoteTemplateUseCase = Depends(get_delete_quote_template_uc),
):
    try:
        await uc.execute(current_user.tenant_id, template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{template_id}/generate/{quote_id}", response_model=GeneratedDocumentOut)
async def generate_quote_document(
    template_id: UUID,
    quote_id: UUID,
    body: GenerateDocumentBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: GenerateQuoteDocumentUseCase = Depends(get_generate_quote_document_uc),
):
    try:
        doc = await uc.execute(GenerateQuoteDocumentRequest(
            tenant_id=current_user.tenant_id,
            quote_id=quote_id,
            template_id=template_id,
            extra_context=body.extra_context,
        ))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return GeneratedDocumentOut(
        quote_id=str(doc.quote_id),
        template_id=str(doc.template_id),
        pdf_url=doc.pdf_url,
        docx_url=doc.docx_url,
    )

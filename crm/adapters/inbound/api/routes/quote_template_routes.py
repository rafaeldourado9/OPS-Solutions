import json
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from adapters.inbound.api.dependencies import (
    get_analyze_template_fields_uc,
    get_delete_quote_template_uc,
    get_generate_quote_document_uc,
    get_list_quote_templates_uc,
    get_quote_template_repo,
    get_upload_quote_template_uc,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from core.domain.quote_template import QuoteTemplate, KNOWN_CRM_FIELDS
from core.ports.outbound.quote_template_repository import QuoteTemplateRepositoryPort
from core.use_cases.quotes.analyze_template_fields import (
    AnalyzeTemplateFieldsRequest,
    AnalyzeTemplateFieldsUseCase,
)
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
    field_mapping: dict[str, str]
    created_at: str
    updated_at: str


class UpdateMappingBody(BaseModel):
    field_mapping: dict[str, str]


class GenerateDocumentBody(BaseModel):
    extra_context: dict[str, str] = {}


class GeneratedDocumentOut(BaseModel):
    quote_id: str
    template_id: str
    pdf_url: str
    docx_url: str


class FieldSuggestionOut(BaseModel):
    original_text: str
    placeholder_key: str
    crm_field: str
    description: str
    confidence: float


class AnalyzeTemplateOut(BaseModel):
    suggestions: list[FieldSuggestionOut]
    document_text_preview: str


class CrmFieldOption(BaseModel):
    key: str
    label: str


def _template_out(t: QuoteTemplate) -> QuoteTemplateOut:
    return QuoteTemplateOut(
        id=str(t.id),
        tenant_id=str(t.tenant_id),
        name=t.name,
        description=t.description,
        placeholders=t.placeholders,
        field_mapping=t.field_mapping,
        created_at=t.created_at.isoformat(),
        updated_at=t.updated_at.isoformat(),
    )


# --- Routes ---

@router.get("/crm-fields", response_model=list[CrmFieldOption])
async def list_crm_fields(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return all known CRM fields available for placeholder mapping."""
    return [CrmFieldOption(key=k, label=v) for k, v in KNOWN_CRM_FIELDS.items()]


@router.post("/analyze", response_model=AnalyzeTemplateOut)
async def analyze_template_fields(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    uc: AnalyzeTemplateFieldsUseCase = Depends(get_analyze_template_fields_uc),
):
    """
    AI-powered analysis of a DOCX template.

    Upload any existing proposal DOCX (without {placeholders}) and receive
    AI suggestions for which text spans are variable fields and which CRM
    fields they map to. The document is NOT saved — this is a preview step.
    The user confirms/edits suggestions, then calls POST / with inject_suggestions.
    """
    if not file.filename or not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are accepted")

    docx_bytes = await file.read()
    result = await uc.execute(
        AnalyzeTemplateFieldsRequest(
            tenant_id=current_user.tenant_id,
            docx_bytes=docx_bytes,
        )
    )
    return AnalyzeTemplateOut(
        suggestions=[
            FieldSuggestionOut(
                original_text=s.original_text,
                placeholder_key=s.placeholder_key,
                crm_field=s.crm_field,
                description=s.description,
                confidence=s.confidence,
            )
            for s in result.suggestions
        ],
        document_text_preview=result.document_text_preview,
    )


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
    # JSON string: {"original_text": "placeholder_key", ...}
    # Populated when the user confirmed AI suggestions from /analyze.
    inject_suggestions: str = Form("{}"),
    current_user: CurrentUser = Depends(get_current_user),
    uc: UploadQuoteTemplateUseCase = Depends(get_upload_quote_template_uc),
):
    if not file.filename or not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are accepted")

    try:
        suggestions_dict: dict[str, str] = json.loads(inject_suggestions)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="inject_suggestions must be valid JSON")

    docx_bytes = await file.read()
    try:
        template = await uc.execute(UploadQuoteTemplateRequest(
            tenant_id=current_user.tenant_id,
            name=name,
            description=description,
            docx_bytes=docx_bytes,
            inject_suggestions=suggestions_dict,
        ))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _template_out(template)


@router.patch("/{template_id}/mapping", response_model=QuoteTemplateOut)
async def update_template_mapping(
    template_id: UUID,
    body: UpdateMappingBody,
    current_user: CurrentUser = Depends(get_current_user),
    repo: QuoteTemplateRepositoryPort = Depends(get_quote_template_repo),
):
    updated = await repo.update_mapping(current_user.tenant_id, template_id, body.field_mapping)
    if not updated:
        raise HTTPException(status_code=404, detail="Template not found")
    return _template_out(updated)


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

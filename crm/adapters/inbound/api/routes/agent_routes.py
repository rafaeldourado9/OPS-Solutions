from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from adapters.inbound.api.dependencies import (
    get_delete_rag_document_uc,
    get_get_agent_config_uc,
    get_list_rag_documents_uc,
    get_update_agent_config_uc,
    get_upload_rag_document_uc,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from core.use_cases.agents.delete_rag_document import DeleteRagDocumentRequest, DeleteRagDocumentUseCase
from core.use_cases.agents.get_agent_config import GetAgentConfigUseCase
from core.use_cases.agents.list_rag_documents import ListRagDocumentsUseCase
from core.use_cases.agents.update_agent_config import UpdateAgentConfigRequest, UpdateAgentConfigUseCase
from core.use_cases.agents.upload_rag_document import UploadRagDocumentRequest, UploadRagDocumentUseCase

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


# --- Schemas ---

class AgentConfigUpdateBody(BaseModel):
    updates: dict


class RagDocumentOut(BaseModel):
    name: str
    collection: str
    chunk_count: int
    ingested_at: str | None = None


# --- Config Routes ---

@router.get("/config")
async def get_agent_config(
    current_user: CurrentUser = Depends(get_current_user),
    uc: GetAgentConfigUseCase = Depends(get_get_agent_config_uc),
):
    try:
        return await uc.execute(current_user.tenant_id)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/config")
async def update_agent_config(
    body: AgentConfigUpdateBody,
    current_user: CurrentUser = Depends(get_current_user),
    uc: UpdateAgentConfigUseCase = Depends(get_update_agent_config_uc),
):
    try:
        return await uc.execute(UpdateAgentConfigRequest(
            tenant_id=current_user.tenant_id,
            updates=body.updates,
        ))
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- RAG Routes ---

@router.get("/rag/documents", response_model=list[RagDocumentOut])
async def list_rag_documents(
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListRagDocumentsUseCase = Depends(get_list_rag_documents_uc),
):
    try:
        docs = await uc.execute(current_user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [
        RagDocumentOut(
            name=d.name,
            collection=d.collection,
            chunk_count=d.chunk_count,
            ingested_at=d.ingested_at.isoformat() if d.ingested_at else None,
        )
        for d in docs
    ]


@router.post("/rag/documents", response_model=RagDocumentOut, status_code=201)
async def upload_rag_document(
    doc_name: str = Form(""),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    uc: UploadRagDocumentUseCase = Depends(get_upload_rag_document_uc),
):
    content = await file.read()
    try:
        doc = await uc.execute(UploadRagDocumentRequest(
            tenant_id=current_user.tenant_id,
            filename=file.filename or "document",
            content=content,
            doc_name=doc_name,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return RagDocumentOut(
        name=doc.name,
        collection=doc.collection,
        chunk_count=doc.chunk_count,
        ingested_at=doc.ingested_at.isoformat() if doc.ingested_at else None,
    )


@router.delete("/rag/documents/{doc_name}", status_code=204)
async def delete_rag_document(
    doc_name: str,
    current_user: CurrentUser = Depends(get_current_user),
    uc: DeleteRagDocumentUseCase = Depends(get_delete_rag_document_uc),
):
    try:
        await uc.execute(DeleteRagDocumentRequest(
            tenant_id=current_user.tenant_id,
            doc_name=doc_name,
        ))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

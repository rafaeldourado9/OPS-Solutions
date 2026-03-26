from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from adapters.inbound.api.dependencies import (
    get_conversation_messages_uc,
    get_end_takeover_uc,
    get_list_conversations_uc,
    get_send_operator_message_uc,
    get_start_takeover_uc,
)
from adapters.inbound.api.middleware.auth import CurrentUser, get_current_user
from core.use_cases.conversations.end_takeover import EndTakeoverUseCase
from core.use_cases.conversations.get_conversation_messages import GetConversationMessagesUseCase
from core.use_cases.conversations.list_conversations import ListConversationsUseCase
from core.use_cases.conversations.send_operator_message import SendOperatorMessageUseCase
from core.use_cases.conversations.start_takeover import StartTakeoverUseCase

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


# --- Schemas ---

class ConversationOut(BaseModel):
    id: str
    tenant_id: str
    chat_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: str
    agent_id: str
    last_message_preview: str
    last_message_at: Optional[str] = None
    unread_count: int
    is_takeover_active: bool
    takeover_operator_id: Optional[str] = None
    status: str
    created_at: str
    updated_at: str


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    chat_id: str
    role: str
    content: str
    sender_name: Optional[str] = None
    media_type: Optional[str] = None
    created_at: str


class PaginatedConversations(BaseModel):
    items: list[ConversationOut]
    total: int
    offset: int
    limit: int


class PaginatedMessages(BaseModel):
    items: list[MessageOut]
    total: int
    offset: int
    limit: int


class SendMessageRequest(BaseModel):
    content: str


# --- Routes ---

@router.get("", response_model=PaginatedConversations)
async def list_conversations(
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    uc: ListConversationsUseCase = Depends(get_list_conversations_uc),
):
    result = await uc.execute(current_user.tenant_id, status, offset, limit)
    return PaginatedConversations(
        items=[
            ConversationOut(
                id=str(c.id),
                tenant_id=str(c.tenant_id),
                chat_id=c.chat_id,
                customer_id=str(c.customer_id) if c.customer_id else None,
                customer_name=c.customer_name,
                customer_phone=c.customer_phone,
                agent_id=c.agent_id,
                last_message_preview=c.last_message_preview,
                last_message_at=c.last_message_at.isoformat() if c.last_message_at else None,
                unread_count=c.unread_count,
                is_takeover_active=c.is_takeover_active,
                takeover_operator_id=str(c.takeover_operator_id) if c.takeover_operator_id else None,
                status=c.status,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in result.items
        ],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.get("/{chat_id}/messages", response_model=PaginatedMessages)
async def get_conversation_messages(
    chat_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: CurrentUser = Depends(get_current_user),
    uc: GetConversationMessagesUseCase = Depends(get_conversation_messages_uc),
):
    try:
        result = await uc.execute(current_user.tenant_id, chat_id, offset, limit)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return PaginatedMessages(
        items=[
            MessageOut(
                id=str(m.id),
                conversation_id=str(m.conversation_id),
                chat_id=m.chat_id,
                role=m.role,
                content=m.content,
                sender_name=m.sender_name,
                media_type=m.media_type,
                created_at=m.created_at.isoformat(),
            )
            for m in result.items
        ],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post("/{chat_id}/takeover", status_code=200)
async def start_takeover(
    chat_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    uc: StartTakeoverUseCase = Depends(get_start_takeover_uc),
):
    try:
        await uc.execute(current_user.tenant_id, chat_id, current_user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "takeover_started", "chat_id": chat_id}


@router.delete("/{chat_id}/takeover", status_code=200)
async def end_takeover(
    chat_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    uc: EndTakeoverUseCase = Depends(get_end_takeover_uc),
):
    try:
        await uc.execute(current_user.tenant_id, chat_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "takeover_ended", "chat_id": chat_id}


@router.post("/{chat_id}/messages", response_model=MessageOut)
async def send_operator_message(
    chat_id: str,
    body: SendMessageRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uc: SendOperatorMessageUseCase = Depends(get_send_operator_message_uc),
):
    try:
        msg = await uc.execute(
            tenant_id=current_user.tenant_id,
            chat_id=chat_id,
            operator_id=current_user.user_id,
            operator_name=current_user.role,  # Will use user name from JWT in real scenario
            content=body.content,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MessageOut(
        id=str(msg.id),
        conversation_id=str(msg.conversation_id),
        chat_id=msg.chat_id,
        role=msg.role,
        content=msg.content,
        sender_name=msg.sender_name,
        media_type=msg.media_type,
        created_at=msg.created_at.isoformat(),
    )

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Conversation:
    id: UUID
    tenant_id: UUID
    chat_id: str
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    customer_phone: str = ""
    agent_id: str = ""
    last_message_preview: str = ""
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    is_takeover_active: bool = False
    takeover_operator_id: Optional[UUID] = None
    status: str = "active"  # active, waiting, closed
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        tenant_id: UUID,
        chat_id: str,
        agent_id: str,
        customer_phone: str = "",
        customer_name: Optional[str] = None,
        customer_id: Optional[UUID] = None,
    ) -> Conversation:
        now = datetime.utcnow()
        return Conversation(
            id=uuid4(),
            tenant_id=tenant_id,
            chat_id=chat_id,
            agent_id=agent_id,
            customer_phone=customer_phone,
            customer_name=customer_name,
            customer_id=customer_id,
            created_at=now,
            updated_at=now,
        )


@dataclass
class CRMMessage:
    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    chat_id: str
    role: str  # user, agent, operator, system
    content: str
    sender_name: Optional[str] = None
    media_type: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        tenant_id: UUID,
        conversation_id: UUID,
        chat_id: str,
        role: str,
        content: str,
        sender_name: Optional[str] = None,
    ) -> CRMMessage:
        return CRMMessage(
            id=uuid4(),
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            chat_id=chat_id,
            role=role,
            content=content,
            sender_name=sender_name,
        )


@dataclass
class TakeoverSession:
    id: UUID
    tenant_id: UUID
    chat_id: str
    operator_id: UUID
    reason: str = "manual"
    started_at: datetime = field(default_factory=lambda: datetime.utcnow())
    ended_at: Optional[datetime] = None

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.conversation_model import ConversationModel
from core.domain.conversation import Conversation
from core.ports.outbound.conversation_repository import ConversationRepositoryPort


class PgConversationRepository(ConversationRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, conversation: Conversation) -> None:
        model = self._to_model(conversation)
        self._session.add(model)
        await self._session.flush()

    async def update(self, conversation: Conversation) -> None:
        stmt = (
            update(ConversationModel)
            .where(
                ConversationModel.id == conversation.id,
                ConversationModel.tenant_id == conversation.tenant_id,
            )
            .values(
                last_message_preview=conversation.last_message_preview,
                last_message_at=conversation.last_message_at,
                unread_count=conversation.unread_count,
                is_takeover_active=conversation.is_takeover_active,
                takeover_operator_id=conversation.takeover_operator_id,
                status=conversation.status,
                customer_id=conversation.customer_id,
                customer_name=conversation.customer_name,
                updated_at=conversation.updated_at,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_by_chat_id(self, tenant_id: UUID, chat_id: str) -> Optional[Conversation]:
        stmt = select(ConversationModel).where(
            ConversationModel.tenant_id == tenant_id,
            ConversationModel.chat_id == chat_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_id(self, tenant_id: UUID, conversation_id: UUID) -> Optional[Conversation]:
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(
        self, tenant_id: UUID, status: Optional[str] = None, offset: int = 0, limit: int = 50
    ) -> tuple[list[Conversation], int]:
        base = select(ConversationModel).where(ConversationModel.tenant_id == tenant_id)

        if status:
            base = base.where(ConversationModel.status == status)

        count_stmt = select(func.count()).select_from(base.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        query = base.order_by(ConversationModel.last_message_at.desc().nullslast()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        items = [self._to_domain(m) for m in result.scalars().all()]

        return items, total

    @staticmethod
    def _to_model(c: Conversation) -> ConversationModel:
        return ConversationModel(
            id=c.id,
            tenant_id=c.tenant_id,
            chat_id=c.chat_id,
            customer_id=c.customer_id,
            customer_name=c.customer_name,
            customer_phone=c.customer_phone,
            agent_id=c.agent_id,
            last_message_preview=c.last_message_preview,
            last_message_at=c.last_message_at,
            unread_count=c.unread_count,
            is_takeover_active=c.is_takeover_active,
            takeover_operator_id=c.takeover_operator_id,
            status=c.status,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )

    @staticmethod
    def _to_domain(m: ConversationModel) -> Conversation:
        return Conversation(
            id=m.id,
            tenant_id=m.tenant_id,
            chat_id=m.chat_id,
            customer_id=m.customer_id,
            customer_name=m.customer_name,
            customer_phone=m.customer_phone,
            agent_id=m.agent_id,
            last_message_preview=m.last_message_preview,
            last_message_at=m.last_message_at,
            unread_count=m.unread_count,
            is_takeover_active=m.is_takeover_active,
            takeover_operator_id=m.takeover_operator_id,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

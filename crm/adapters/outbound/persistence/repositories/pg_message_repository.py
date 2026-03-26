from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.message_model import CRMMessageModel
from core.domain.conversation import CRMMessage
from core.ports.outbound.message_repository import MessageRepositoryPort


class PgMessageRepository(MessageRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, message: CRMMessage) -> None:
        model = CRMMessageModel(
            id=message.id,
            tenant_id=message.tenant_id,
            conversation_id=message.conversation_id,
            chat_id=message.chat_id,
            role=message.role,
            content=message.content,
            sender_name=message.sender_name,
            media_type=message.media_type,
            created_at=message.created_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def list_by_conversation(
        self, tenant_id: UUID, conversation_id: UUID, offset: int = 0, limit: int = 100
    ) -> tuple[list[CRMMessage], int]:
        base = select(CRMMessageModel).where(
            CRMMessageModel.tenant_id == tenant_id,
            CRMMessageModel.conversation_id == conversation_id,
        )

        count_stmt = select(func.count()).select_from(base.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        query = base.order_by(CRMMessageModel.created_at.asc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        items = [self._to_domain(m) for m in result.scalars().all()]

        return items, total

    @staticmethod
    def _to_domain(m: CRMMessageModel) -> CRMMessage:
        return CRMMessage(
            id=m.id,
            tenant_id=m.tenant_id,
            conversation_id=m.conversation_id,
            chat_id=m.chat_id,
            role=m.role,
            content=m.content,
            sender_name=m.sender_name,
            media_type=m.media_type,
            created_at=m.created_at,
        )

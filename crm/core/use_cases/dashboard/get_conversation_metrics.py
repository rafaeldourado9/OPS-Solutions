from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from core.ports.outbound.dashboard_repository import ConversationMetrics, DashboardRepositoryPort


@dataclass
class GetConversationMetricsRequest:
    tenant_id: UUID
    days: int = 30


class GetConversationMetricsUseCase:

    def __init__(self, repo: DashboardRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, req: GetConversationMetricsRequest) -> ConversationMetrics:
        since = datetime.utcnow() - timedelta(days=req.days)
        return await self._repo.get_conversation_metrics(req.tenant_id, since)

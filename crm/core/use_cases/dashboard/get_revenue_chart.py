from dataclasses import dataclass
from uuid import UUID

from core.ports.outbound.dashboard_repository import DashboardRepositoryPort, RevenueDataPoint


@dataclass
class GetRevenueChartRequest:
    tenant_id: UUID
    months: int = 6


class GetRevenueChartUseCase:

    def __init__(self, repo: DashboardRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, req: GetRevenueChartRequest) -> list[RevenueDataPoint]:
        months = max(1, min(req.months, 24))
        return await self._repo.get_revenue_chart(req.tenant_id, months)

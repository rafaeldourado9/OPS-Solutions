from dataclasses import dataclass
from uuid import UUID

from core.ports.outbound.dashboard_repository import DashboardRepositoryPort, SalesFunnelStage


@dataclass
class GetSalesFunnelRequest:
    tenant_id: UUID


class GetSalesFunnelUseCase:

    def __init__(self, repo: DashboardRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, req: GetSalesFunnelRequest) -> list[SalesFunnelStage]:
        return await self._repo.get_sales_funnel(req.tenant_id)

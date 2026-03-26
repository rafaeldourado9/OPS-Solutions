from dataclasses import dataclass
from uuid import UUID

from core.ports.outbound.dashboard_repository import DashboardRepositoryPort, InventoryAlert


@dataclass
class GetInventoryAlertsRequest:
    tenant_id: UUID


class GetInventoryAlertsUseCase:

    def __init__(self, repo: DashboardRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, req: GetInventoryAlertsRequest) -> list[InventoryAlert]:
        return await self._repo.get_inventory_alerts(req.tenant_id)

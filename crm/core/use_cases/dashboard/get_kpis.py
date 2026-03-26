from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from core.ports.outbound.dashboard_repository import DashboardRepositoryPort, KPIData


@dataclass
class GetKPIsRequest:
    tenant_id: UUID
    days: int = 30


class GetKPIsUseCase:

    def __init__(self, repo: DashboardRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, req: GetKPIsRequest) -> KPIData:
        since = datetime.now(timezone.utc) - timedelta(days=req.days)
        return await self._repo.get_kpis(req.tenant_id, since)

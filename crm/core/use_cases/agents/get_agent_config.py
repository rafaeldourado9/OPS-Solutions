from uuid import UUID

from core.ports.outbound.agent_config_port import AgentConfigPort
from core.ports.outbound.tenant_repository import TenantRepositoryPort


class GetAgentConfigUseCase:

    def __init__(
        self,
        tenant_repo: TenantRepositoryPort,
        config_port: AgentConfigPort,
    ) -> None:
        self._tenant_repo = tenant_repo
        self._config_port = config_port

    async def execute(self, tenant_id: UUID) -> dict:
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        if not self._config_port.exists(tenant.agent_id):
            raise FileNotFoundError(
                f"business.yml not found for agent '{tenant.agent_id}'"
            )

        return self._config_port.read(tenant.agent_id)

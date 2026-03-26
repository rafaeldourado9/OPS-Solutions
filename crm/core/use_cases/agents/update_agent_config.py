from dataclasses import dataclass, field
from uuid import UUID

from core.ports.outbound.agent_config_port import AgentConfigPort
from core.ports.outbound.tenant_repository import TenantRepositoryPort


@dataclass(frozen=True)
class UpdateAgentConfigRequest:
    tenant_id: UUID
    updates: dict = field(default_factory=dict)


def _deep_merge(base: dict, updates: dict) -> dict:
    """Recursively merges updates into base. Returns a new dict."""
    result = dict(base)
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class UpdateAgentConfigUseCase:

    def __init__(
        self,
        tenant_repo: TenantRepositoryPort,
        config_port: AgentConfigPort,
    ) -> None:
        self._tenant_repo = tenant_repo
        self._config_port = config_port

    async def execute(self, request: UpdateAgentConfigRequest) -> dict:
        tenant = await self._tenant_repo.get_by_id(request.tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        if not self._config_port.exists(tenant.agent_id):
            raise FileNotFoundError(
                f"business.yml not found for agent '{tenant.agent_id}'"
            )

        current = self._config_port.read(tenant.agent_id)
        updated = _deep_merge(current, request.updates)
        self._config_port.write(tenant.agent_id, updated)
        return updated

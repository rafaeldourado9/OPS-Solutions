from pathlib import Path

import yaml

from core.ports.outbound.agent_config_port import AgentConfigPort
from infrastructure.config import settings


class FilesystemAgentConfigAdapter(AgentConfigPort):
    """Reads and writes business.yml from the shared agents directory."""

    def __init__(self, agents_dir: str | None = None) -> None:
        self._base = Path(agents_dir or settings.agents_dir)

    def _path(self, agent_id: str) -> Path:
        return self._base / agent_id / "business.yml"

    def exists(self, agent_id: str) -> bool:
        return self._path(agent_id).exists()

    def read(self, agent_id: str) -> dict:
        path = self._path(agent_id)
        if not path.exists():
            raise FileNotFoundError(f"business.yml not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def write(self, agent_id: str, config: dict) -> None:
        path = self._path(agent_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

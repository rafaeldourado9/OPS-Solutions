from abc import ABC, abstractmethod


class AgentConfigPort(ABC):

    @abstractmethod
    def read(self, agent_id: str) -> dict:
        """Reads business.yml for agent_id and returns raw dict."""
        ...

    @abstractmethod
    def write(self, agent_id: str, config: dict) -> None:
        """Writes the config dict as business.yml for agent_id."""
        ...

    @abstractmethod
    def exists(self, agent_id: str) -> bool:
        """Returns True if business.yml exists for agent_id."""
        ...

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

    @abstractmethod
    def list_agents(self) -> list[str]:
        """Returns sorted list of agent_ids that have a business.yml."""
        ...

    @abstractmethod
    def create_agent(
        self,
        agent_id: str,
        template_id: str = "template",
        company_name: str = "",
        agent_name: str = "",
        persona: str = "",
    ) -> None:
        """Creates a new agent directory by copying from template."""
        ...

    @abstractmethod
    def delete_agent(self, agent_id: str) -> None:
        """Deletes the agent directory entirely."""
        ...

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

    def list_agents(self) -> list[str]:
        if not self._base.exists():
            return []
        return sorted(
            p.name for p in self._base.iterdir()
            if p.is_dir() and p.name != "template" and (p / "business.yml").exists()
        )

    def create_agent(
        self,
        agent_id: str,
        template_id: str = "template",
        company_name: str = "",
        agent_name: str = "",
    ) -> None:
        import shutil
        target = self._base / agent_id
        if target.exists():
            raise ValueError(f"Agent '{agent_id}' already exists")
        template = self._base / template_id
        if template.exists():
            shutil.copytree(str(template), str(target))
            # Fix collection names to be agent-specific (not inherited from template)
            cfg = self.read(agent_id)
            cfg.setdefault("memory", {})["qdrant_collection"] = f"{agent_id}_chats"
            cfg["memory"]["qdrant_rag_collection"] = f"{agent_id}_rules"
            if company_name:
                cfg.setdefault("agent", {})["company"] = company_name
            if agent_name:
                cfg.setdefault("agent", {})["name"] = agent_name
            # Interpolate {name} and {company} placeholders in persona
            persona = cfg.get("agent", {}).get("persona", "")
            if persona and ("{name}" in persona or "{company}" in persona):
                persona = persona.replace("{name}", agent_name or "Assistente")
                persona = persona.replace("{company}", company_name or "a empresa")
                cfg["agent"]["persona"] = persona
            self.write(agent_id, cfg)
        else:
            target.mkdir(parents=True)
            (target / "docs").mkdir(exist_ok=True)
            default_config = {
                "agent": {
                    "name": agent_name or agent_id,
                    "company": company_name,
                    "language": "pt-BR",
                    "persona": "Você é um assistente simpático e profissional. Responde com objetividade, em mensagens curtas, como numa conversa real no WhatsApp. Usa linguagem informal mas respeitosa. Quando não souber algo, diz que vai verificar com a equipe.",
                    "admin_phones": [],
                },
                "llm": {"provider": "gemini", "model": "gemini-2.0-flash", "temperature": 0.7, "max_tokens": 8192},
                "messaging": {"debounce_seconds": 2.5, "max_message_chars": 180, "typing_delay_per_char": 0.04, "min_pause_between_parts": 1.2, "max_pause_between_parts": 2.8},
                "memory": {"qdrant_collection": f"{agent_id}_chats", "qdrant_rag_collection": f"{agent_id}_rules", "semantic_k": 6, "max_recent_messages": 15, "embedding_model": "nomic-embed-text"},
                "anti_hallucination": {"rag_mandatory": False, "unknown_answer": "Não tenho essa informação no momento, mas posso verificar com nossa equipe!", "grounding_enabled": True},
                "media": {"audio_model": "gemini-2.0-flash", "image_model": "gemini-2.0-flash", "video_model": "gemini-2.0-flash", "video_frame_interval": 5, "tts_enabled": False, "tts_voice": "Puck", "tts_chance": 0.5},
                "crm": {"enabled": True, "events_webhook": "${CRM_WEBHOOK_URL}", "push_events": ["new_contact", "message_received", "agent_response_sent", "conversation_closed"]},
            }
            self.write(agent_id, default_config)

    def delete_agent(self, agent_id: str) -> None:
        import shutil
        path = self._base / agent_id
        if not path.exists():
            raise FileNotFoundError(f"Agent '{agent_id}' not found")
        shutil.rmtree(str(path))

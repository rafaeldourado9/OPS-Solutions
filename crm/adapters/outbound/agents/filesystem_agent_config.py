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
        persona: str = "",
    ) -> None:
        import shutil
        target = self._base / agent_id
        if target.exists():
            raise ValueError(f"Agent '{agent_id}' already exists")
        template = self._base / template_id
        if template.exists():
            shutil.copytree(str(template), str(target))
            cfg = self.read(agent_id)
            # Fix collection names to be agent-specific
            cfg.setdefault("memory", {})["qdrant_collection"] = f"{agent_id}_chats"
            cfg["memory"]["qdrant_rag_collection"] = f"{agent_id}_rules"
            if company_name:
                cfg.setdefault("agent", {})["company"] = company_name
            if agent_name:
                cfg.setdefault("agent", {})["name"] = agent_name
            # Persona from onboarding takes priority; otherwise interpolate placeholders
            if persona:
                cfg["agent"]["persona"] = persona
            else:
                p = cfg.get("agent", {}).get("persona", "")
                if p and ("{name}" in p or "{company}" in p):
                    p = p.replace("{name}", agent_name or "Assistente")
                    p = p.replace("{company}", company_name or "a empresa")
                    cfg["agent"]["persona"] = p
            self.write(agent_id, cfg)
        else:
            target.mkdir(parents=True)
            (target / "docs").mkdir(exist_ok=True)
            default_persona = persona or (
                f"Você é {agent_name or 'Assistente'}, assistente virtual"
                + (f" da {company_name}" if company_name else "") + ".\n\n"
                "Comportamento:\n"
                "- Mensagens curtas e objetivas — prefira várias mensagens curtas a uma longa\n"
                "- Tom natural, como uma pessoa real no WhatsApp\n\n"
                "Regras obrigatórias:\n"
                "- Pergunte o nome do cliente logo no início e use-o ao longo de toda a conversa\n"
                "- Nunca repita perguntas que você já fez\n"
                "- NUNCA invente informações. Se não sabe, diga 'vou confirmar com a equipe'\n"
                f"- NUNCA se identifique como IA ou robô. Você é {agent_name or 'Assistente'}\n"
            )
            default_config = {
                "agent": {
                    "name": agent_name or agent_id,
                    "company": company_name,
                    "language": "pt-BR",
                    "persona": default_persona,
                    "admin_phones": [],
                },
                "llm": {
                    "provider": "gemini",
                    "model": "gemini-2.0-flash",
                    "fallback_provider": "gemini",
                    "fallback_model": "gemini-2.0-flash-lite",
                    "temperature": 0.7,
                    "max_tokens": 8192,
                },
                "messaging": {
                    "debounce_seconds": 4.0,
                    "max_message_chars": 120,
                    "typing_delay_per_char": 0.04,
                    "min_pause_between_parts": 1.2,
                    "max_pause_between_parts": 2.8,
                },
                "memory": {
                    "qdrant_collection": f"{agent_id}_chats",
                    "qdrant_rag_collection": f"{agent_id}_rules",
                    "semantic_k": 6,
                    "max_recent_messages": 15,
                    "embedding_model": "nomic-embed-text",
                },
                "anti_hallucination": {
                    "rag_mandatory": False,
                    "unknown_answer": "Não tenho essa informação agora, mas posso verificar com a equipe e te retorno!",
                    "grounding_enabled": True,
                },
                "media": {
                    "audio_model": "gemini-2.0-flash",
                    "image_model": "gemini-2.0-flash",
                    "video_model": "gemini-2.0-flash",
                    "video_frame_interval": 5,
                    "tts_enabled": False,
                    "tts_chance": 0.75,
                },
                "crm": {
                    "enabled": True,
                    "events_webhook": "${CRM_WEBHOOK_URL}",
                    "push_events": ["new_contact", "message_received", "agent_response_sent", "conversation_closed"],
                },
            }
            self.write(agent_id, default_config)

    def delete_agent(self, agent_id: str) -> None:
        import shutil
        path = self._base / agent_id
        if not path.exists():
            raise FileNotFoundError(f"Agent '{agent_id}' not found")
        shutil.rmtree(str(path))


# Alias for backwards-compat with import sites that use the shorter name
FilesystemAgentConfig = FilesystemAgentConfigAdapter

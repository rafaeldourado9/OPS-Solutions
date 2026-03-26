"""
ProactiveScheduler — background service for proactive WhatsApp messages.

Responsibilities:
1. Daily motivational message at configured time (e.g., 18:00)
2. Inactivity warnings (2+ days without message → gentle check-in)
3. Inactivity alerts (5+ days without message → stronger reminder)
4. Calendar event reminders (2 days before each event)

All messages are sent directly via the agent's gateway, bypassing the debounce buffer
(these are outgoing, not incoming messages).
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone as tz
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Motivational messages pool
# ---------------------------------------------------------------------------

_MOTIVATIONAL_MESSAGES = [
    "Oi! Hora de dar uma estudada hoje 📚\nComo tá indo a faculdade?",
    "Boa tarde! Que tal revisitar aquela matéria que tá difícil?\nTô aqui se precisar de ajuda",
    "18h chegou — hora de abrir o caderno\nPor qual matéria você vai começar hoje?",
    "Ei, a futura dentista tá ativa?\nUm tempinho de estudo hoje faz diferença",
    "Bora estudar? Nem que seja 30 minutinhos\nO que tá na sua lista hoje?",
    "Oi! Lembra que cada hora de estudo hoje é um passo a menos na véspera da prova\nVai lá!",
    "Hora do check-in diário\nComo foi o dia na faculdade?",
    "Que tal uma sessão de Anki hoje?\nFlashcards salvam na hora da prova",
    "Boa tarde! Alguma prova chegando? Me conta a situação",
    "Ei, o cérebro absorve melhor quando descansado\nDescansou hoje? Agora vai estudar?",
]

_INACTIVITY_WARNING = [
    "Ei, faz alguns dias que não apareces por aqui\nTudo bem?",
    "Oi, sumiu!\nTá correndo ou conseguiu dar uma estudada essa semana?",
    "Faz um tempão que não converso contigo\nComo tá a faculdade?",
]

_INACTIVITY_ALERT = [
    "Ei, tô com saudade\nFaz vários dias que não apareces — me conta o que tá rolando",
    "Oi! Sei que a vida às vezes atropela tudo\nMas tô aqui quando precisar voltar aos estudos",
    "Passando pra dizer que tô aqui, tá?\nQuando quiser retomar, é só chamar",
]


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


class ProactiveScheduler:
    """
    Background scheduler for proactive messages.

    Args:
        agent_id:         Agent identifier.
        gateway:          GatewayPort to send messages.
        activity_tracker: ActivityTracker to check inactivity.
        calendar:         CalendarPort to check upcoming events.
        config:           ProactiveConfig from business.yml.
        target_chat_ids:  List of chat_ids to proactively message.
                          If empty, uses dynamically tracked chats.
        llm:              Optional LLMPort. Required when daily_message_type="llm".
        llm_system_prompt: Optional system prompt injected when generating LLM messages.
    """

    def __init__(
        self,
        agent_id: str,
        gateway,            # GatewayPort
        activity_tracker,   # ActivityTracker
        calendar,           # CalendarPort
        config,             # ProactiveConfig
        target_chat_ids: list[str] | None = None,
        llm=None,           # LLMPort | None
        llm_system_prompt: str = "",
    ) -> None:
        self._agent_id = agent_id
        self._gateway = gateway
        self._tracker = activity_tracker
        self._calendar = calendar
        self._config = config
        self._target_chat_ids = target_chat_ids or []
        self._llm = llm
        self._llm_system_prompt = llm_system_prompt
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        """Start the background scheduling loop."""
        if not getattr(self._config, 'enabled', False):
            logger.info("ProactiveScheduler disabled for agent=%s", self._agent_id)
            return
        self._task = asyncio.create_task(self._loop(), name=f"proactive_{self._agent_id}")
        logger.info("ProactiveScheduler started for agent=%s", self._agent_id)

    def stop(self) -> None:
        """Cancel the background task."""
        if self._task and not self._task.done():
            self._task.cancel()

    async def _loop(self) -> None:
        """Main scheduling loop — runs once at startup, then daily at target time."""
        try:
            while True:
                next_run = self._next_run_time()
                now = datetime.now()
                sleep_seconds = max(0, (next_run - now).total_seconds())
                logger.info(
                    "ProactiveScheduler[%s]: next run at %s (%.0fs)",
                    self._agent_id, next_run.strftime("%H:%M %d/%m"), sleep_seconds,
                )
                await asyncio.sleep(sleep_seconds)
                await self._run_daily_jobs()
        except asyncio.CancelledError:
            logger.info("ProactiveScheduler[%s] cancelled", self._agent_id)
        except Exception:
            logger.exception("ProactiveScheduler[%s] unexpected error", self._agent_id)

    def _next_run_time(self) -> datetime:
        """Calculate the next run time (today or tomorrow at target time)."""
        time_str = getattr(self._config, 'daily_motivation_time', '18:00')
        hour, minute = map(int, time_str.split(":"))
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    async def _run_daily_jobs(self) -> None:
        """Execute all daily proactive jobs."""
        logger.info("ProactiveScheduler[%s]: running daily jobs", self._agent_id)

        # Get all chat_ids to message
        chat_ids = self._target_chat_ids or await self._tracker.get_all_tracked_chats()
        if not chat_ids:
            logger.info("ProactiveScheduler[%s]: no chat_ids to message", self._agent_id)
            return

        for chat_id in chat_ids:
            try:
                await self._process_chat(chat_id)
                # Small delay between chats to avoid flooding
                await asyncio.sleep(2)
            except Exception:
                logger.exception("ProactiveScheduler error for chat_id=%s", chat_id)

    async def _process_chat(self, chat_id: str) -> None:
        """Decide what to send to a given chat_id based on inactivity and calendar."""
        seconds_inactive = await self._tracker.seconds_since_last_activity(chat_id)
        warning_threshold = getattr(self._config, 'inactivity_warning_days', 2) * 86400
        alert_threshold = getattr(self._config, 'inactivity_alert_days', 5) * 86400

        # --- Inactivity check ---
        if seconds_inactive is not None:
            if seconds_inactive >= alert_threshold:
                msg = random.choice(_INACTIVITY_ALERT)
                await self._send(chat_id, msg)
                return
            elif seconds_inactive >= warning_threshold:
                msg = random.choice(_INACTIVITY_WARNING)
                await self._send(chat_id, msg)
                return

        # --- Calendar reminders (2 days before event) ---
        reminder_days = getattr(self._config, 'calendar_reminder_days_before', 2)
        upcoming = await self._calendar.list_upcoming_events(days_ahead=reminder_days + 1)
        now = datetime.now()
        for event in upcoming:
            start = event.start
            if not start.tzinfo:
                start = start.replace(tzinfo=tz.utc)
            days_until = (start.astimezone(tz.utc).replace(tzinfo=None) - now).days
            if days_until == reminder_days:
                date_str = start.strftime("%d/%m às %H:%M")
                msg = (
                    f"Lembrete: {event.title} é daqui a {reminder_days} dias\n"
                    f"Data: {date_str}\n"
                    f"Bora revisar o conteúdo?"
                )
                await self._send(chat_id, msg)
                return  # One reminder per run per chat

        # --- Daily message ---
        # Only if inactive for at least 12h (don't spam active users)
        if seconds_inactive is None or seconds_inactive >= 43200:  # 12 hours
            if getattr(self._config, 'daily_message_type', 'static') == 'llm' and self._llm:
                msg = await self._generate_llm_message()
            else:
                msg = f"[MOTIVAÇÃO DO DIA]\n{random.choice(_MOTIVATIONAL_MESSAGES)}"
            await self._send(chat_id, msg)

    async def _generate_llm_message(self) -> str:
        """
        Generate a daily message using the LLM.

        Falls back to a random static message if the LLM call fails.
        """
        messages = []
        if self._llm_system_prompt:
            messages.append({"role": "system", "content": self._llm_system_prompt})
        messages.append({
            "role": "user",
            "content": (
                "Gere o insight técnico do dia. Escolha um tópico específico de arquitetura de software, "
                "system design, DDD, padrões de distribuição, decisões de banco de dados, trade-offs "
                "arquiteturais ou tendências emergentes. Prefira algo contraintuitivo, frequentemente "
                "mal entendido ou que cause reflexão real. Cite exemplos de empresas reais quando "
                "relevante (Netflix, Amazon, Uber, etc.). "
                "Formato WhatsApp: partes curtas separadas por linha em branco. Máximo 4 partes. "
                "Sem emojis. Sem markdown. Sem bullet points. Escreva direto, como quem está "
                "passando um conhecimento valioso de forma objetiva."
            ),
        })
        try:
            parts: list[str] = []
            async for chunk in self._llm.stream_response(messages):
                parts.append(chunk)
            result = "".join(parts).strip()
            if result:
                return result
        except Exception:
            logger.exception("ProactiveScheduler[%s]: LLM generation failed", self._agent_id)
        return random.choice(_MOTIVATIONAL_MESSAGES)

    async def _send(self, chat_id: str, text: str) -> None:
        """Send a message directly via gateway."""
        try:
            await self._gateway.send_message(chat_id, text)
            logger.info("ProactiveScheduler[%s]: sent to chat_id=%s", self._agent_id, chat_id)
        except Exception:
            logger.exception("ProactiveScheduler failed to send to chat_id=%s", chat_id)

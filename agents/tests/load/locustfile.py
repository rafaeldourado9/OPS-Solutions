"""
Locust load test for the WhatsApp Agent webhook endpoint.

Simulates concurrent users sending messages from different phone numbers.
Each "user" has its own chat_id so conversations are isolated.

Usage:
    # Install: pip install locust
    # Run headless (10 users, spawn 2/s, run 60s):
    locust -f tests/load/locustfile.py \
        --headless -u 10 -r 2 --run-time 60s \
        --host http://localhost:8000

    # Run with web UI:
    locust -f tests/load/locustfile.py --host http://localhost:8000
"""

from __future__ import annotations

import random
import uuid

from locust import HttpUser, between, task

# ---------------------------------------------------------------------------
# Message pool
# ---------------------------------------------------------------------------

_SIMPLE_MESSAGES = [
    "Olá, tudo bem?",
    "Oi!",
    "Boa tarde",
    "Preciso de ajuda",
    "Como vai?",
]

_COMPLEX_MESSAGES = [
    "Qual é o prazo de entrega para o meu pedido?",
    "Quanto custa o serviço de consultoria?",
    "Quero fazer um orçamento para minha empresa.",
    "Tive um problema com o produto que recebi, está danificado.",
    "Podem me explicar como funciona a garantia?",
    "Preciso cancelar meu contrato, como faço isso?",
    "Quero comparar os planos disponíveis.",
]

_SESSIONS = ["empresa_x", "empresa_y"]


# ---------------------------------------------------------------------------
# User classes
# ---------------------------------------------------------------------------


class WhatsAppUser(HttpUser):
    """
    Simulates a WhatsApp user sending messages to the agent webhook.

    Each user gets a unique phone number so conversations are isolated.
    """

    wait_time = between(1.0, 3.0)

    def on_start(self) -> None:
        """Assign a unique phone number and session to this virtual user."""
        phone = f"5511{random.randint(900000000, 999999999)}"
        self.chat_id = f"{phone}@c.us"
        self.session = random.choice(_SESSIONS)

    def _send_message(self, body: str) -> None:
        payload = {
            "event": "message",
            "session": self.session,
            "payload": {
                "id": str(uuid.uuid4()),
                "from": self.chat_id,
                "fromMe": False,
                "type": "chat",
                "body": body,
                "hasMedia": False,
            },
        }
        with self.client.post(
            "/webhook",
            json=payload,
            catch_response=True,
            name="/webhook [text]",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}: {resp.text[:100]}")

    @task(7)
    def send_simple_message(self) -> None:
        """Send a short, simple message (majority of traffic)."""
        self._send_message(random.choice(_SIMPLE_MESSAGES))

    @task(3)
    def send_complex_message(self) -> None:
        """Send a longer, complex message (minority of traffic)."""
        self._send_message(random.choice(_COMPLEX_MESSAGES))

    @task(1)
    def send_burst(self) -> None:
        """Simulate a user typing multiple messages quickly (debounce scenario)."""
        messages = random.sample(_SIMPLE_MESSAGES, k=min(3, len(_SIMPLE_MESSAGES)))
        for msg in messages:
            self._send_message(msg)

    @task(1)
    def check_health(self) -> None:
        """Periodically hit /health to verify liveness."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health",
        ) as resp:
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                resp.success()
            else:
                resp.failure(f"Health check failed: {resp.status_code}")

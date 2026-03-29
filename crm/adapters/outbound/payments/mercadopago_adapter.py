"""Mercado Pago adapter — recurring subscriptions via Preapproval API."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx
import structlog

from infrastructure.config import settings

logger = structlog.get_logger()

_MP_API = "https://api.mercadopago.com"


@dataclass
class SubscriptionResult:
    subscription_id: str
    init_point: str
    status: str


class MercadoPagoAdapter:
    def __init__(self) -> None:
        self._token = settings.mercadopago_access_token
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def create_subscription(
        self,
        plan: str,
        payer_email: str,
        tenant_id: str,
        back_url: str,
    ) -> SubscriptionResult:
        """Create a pending preapproval and return the checkout URL."""
        if plan == "pro":
            amount = settings.mp_pro_price
            reason = "Plano Pro — OPS Solutions CRM"
        else:
            amount = settings.mp_starter_price
            reason = "Plano Starter — OPS Solutions CRM"

        payload = {
            "reason": reason,
            "external_reference": tenant_id,
            "payer_email": payer_email,
            "auto_recurring": {
                "frequency": 1,
                "frequency_type": "months",
                "transaction_amount": amount,
                "currency_id": "BRL",
            },
            "back_url": back_url,
            "status": "pending",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_MP_API}/preapproval",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()

        return SubscriptionResult(
            subscription_id=data["id"],
            init_point=data["init_point"],
            status=data.get("status", "pending"),
        )

    async def get_subscription(self, subscription_id: str) -> dict:
        """Fetch preapproval details from MP."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_MP_API}/preapproval/{subscription_id}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def cancel_subscription(self, subscription_id: str) -> None:
        """Cancel an active preapproval."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.put(
                f"{_MP_API}/preapproval/{subscription_id}",
                json={"status": "cancelled"},
                headers=self._headers,
            )
            resp.raise_for_status()

    @staticmethod
    def plan_from_amount(amount: float) -> str:
        """Map transaction amount to plan slug."""
        if amount >= settings.mp_pro_price:
            return "pro"
        return "starter"

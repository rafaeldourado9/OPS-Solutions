"""Payment routes — Mercado Pago subscriptions + webhook."""
from __future__ import annotations

import hashlib
import hmac
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from adapters.outbound.payments.mercadopago_adapter import MercadoPagoAdapter
from adapters.outbound.persistence.database import get_session, async_session_factory
from adapters.outbound.persistence.models.tenant_model import TenantModel
from infrastructure.config import settings

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan: str  # "starter" | "pro"


class CheckoutResponse(BaseModel):
    checkout_url: str
    subscription_id: str


class SubscriptionOut(BaseModel):
    plan: str
    subscription_status: str | None
    mp_subscription_id: str | None
    mp_payer_email: str | None


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a Mercado Pago subscription checkout URL."""
    if body.plan not in ("starter", "pro"):
        raise HTTPException(status_code=400, detail="Plan must be 'starter' or 'pro'")

    if not settings.mercadopago_access_token:
        raise HTTPException(status_code=503, detail="Payment gateway not configured")

    # Fetch current user email for payer
    from adapters.outbound.persistence.models.user_model import UserModel
    result = await session.execute(
        select(UserModel).where(
            UserModel.id == current_user.user_id,
            UserModel.tenant_id == current_user.tenant_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    back_url = f"{settings.app_url}/app/settings"

    try:
        mp = MercadoPagoAdapter()
        sub = await mp.create_subscription(
            plan=body.plan,
            payer_email=user.email,
            tenant_id=str(current_user.tenant_id),
            back_url=back_url,
        )
    except Exception as exc:
        logger.error("mp_checkout_failed", error=str(exc), tenant_id=str(current_user.tenant_id))
        raise HTTPException(status_code=502, detail="Failed to create checkout")

    # Persist pending subscription
    tenant_res = await session.execute(
        select(TenantModel).where(TenantModel.id == current_user.tenant_id)
    )
    tenant = tenant_res.scalar_one_or_none()
    if tenant:
        tenant.mp_subscription_id = sub.subscription_id
        tenant.mp_payer_email = user.email
        tenant.subscription_status = "pending"
        await session.commit()

    return CheckoutResponse(
        checkout_url=sub.init_point,
        subscription_id=sub.subscription_id,
    )


@router.get("/current", response_model=SubscriptionOut)
async def get_current_subscription(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return current subscription info for the tenant."""
    result = await session.execute(
        select(TenantModel).where(TenantModel.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return SubscriptionOut(
        plan=tenant.plan,
        subscription_status=tenant.subscription_status,
        mp_subscription_id=tenant.mp_subscription_id,
        mp_payer_email=tenant.mp_payer_email,
    )


@router.post("/cancel", status_code=204)
async def cancel_subscription(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Cancel the active subscription."""
    result = await session.execute(
        select(TenantModel).where(TenantModel.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant or not tenant.mp_subscription_id:
        raise HTTPException(status_code=404, detail="No active subscription found")

    try:
        mp = MercadoPagoAdapter()
        await mp.cancel_subscription(tenant.mp_subscription_id)
    except Exception as exc:
        logger.error("mp_cancel_failed", error=str(exc))
        raise HTTPException(status_code=502, detail="Failed to cancel subscription")

    tenant.subscription_status = "cancelled"
    await session.commit()


# ─── Webhook (no auth — MP calls this) ───────────────────────────────────────

_webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@_webhook_router.post("/mercadopago")
async def mercadopago_webhook(request: Request):
    """Receive Mercado Pago subscription notifications."""
    body_bytes = await request.body()

    # Signature validation when secret is configured
    if settings.mercadopago_webhook_secret:
        sig_header = request.headers.get("x-signature", "")
        ts = ""
        received_hash = ""
        for part in sig_header.split(","):
            part = part.strip()
            if part.startswith("ts="):
                ts = part[3:]
            elif part.startswith("v1="):
                received_hash = part[3:]

        manifest = f"id:{request.query_params.get('data.id', '')};request-id:{request.headers.get('x-request-id', '')};ts:{ts};"
        expected = hmac.new(
            settings.mercadopago_webhook_secret.encode(),
            manifest.encode(),
            hashlib.sha256,
        ).hexdigest()  # type: ignore[attr-defined]
        if not hmac.compare_digest(expected, received_hash):
            logger.warning("mp_webhook_invalid_signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = await request.json()
    except Exception:
        return {"status": "ok"}

    event_type = payload.get("type", "")
    data = payload.get("data", {})
    resource_id = data.get("id")

    if event_type != "preapproval" or not resource_id:
        return {"status": "ok"}

    # Fetch subscription details from MP
    try:
        mp = MercadoPagoAdapter()
        sub = await mp.get_subscription(resource_id)
    except Exception as exc:
        logger.error("mp_webhook_fetch_failed", resource_id=resource_id, error=str(exc))
        return {"status": "ok"}

    external_ref = sub.get("external_reference", "")
    mp_status = sub.get("status", "")
    auto = sub.get("auto_recurring", {})
    amount = float(auto.get("transaction_amount", 0))
    payer_email = sub.get("payer_email", "")

    if not external_ref:
        return {"status": "ok"}

    # Map MP status → plan + subscription_status
    plan_map = {
        "authorized": MercadoPagoAdapter.plan_from_amount(amount),
        "paused": None,
        "cancelled": None,
        "pending": None,
    }

    async with async_session_factory() as session:
        try:
            tenant_id = UUID(external_ref)
        except ValueError:
            return {"status": "ok"}

        result = await session.execute(
            select(TenantModel).where(TenantModel.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            return {"status": "ok"}

        tenant.mp_subscription_id = resource_id
        tenant.mp_payer_email = payer_email or tenant.mp_payer_email
        tenant.subscription_status = mp_status

        if mp_status == "authorized":
            new_plan = MercadoPagoAdapter.plan_from_amount(amount)
            tenant.plan = new_plan
            # Remove trial restriction once paid
            tenant.trial_ends_at = None
            logger.info(
                "mp_subscription_activated",
                tenant_id=external_ref,
                plan=new_plan,
                amount=amount,
            )
        elif mp_status == "cancelled":
            tenant.plan = "starter"
            logger.info("mp_subscription_cancelled", tenant_id=external_ref)

        await session.commit()

    return {"status": "ok"}

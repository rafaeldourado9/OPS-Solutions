"""Background task: sends inactivity reminders for stale leads.

A lead is considered inactive when:
  - Stage is NOT terminal (won / lost)
  - updated_at < now - INACTIVE_THRESHOLD_DAYS
  - last_inactivity_email_at is NULL  OR  < now - RESEND_AFTER_DAYS
    (avoids spamming the same lead every day)
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import structlog

from adapters.outbound.email.smtp_adapter import SmtpEmailAdapter
from adapters.outbound.email import templates as tmpl
from adapters.outbound.persistence.database import async_session_factory
from infrastructure.config import settings

logger = structlog.get_logger()

INACTIVE_THRESHOLD_DAYS = 7   # lead counts as inactive after N days with no update
RESEND_AFTER_DAYS = 7         # don't re-send reminder for same lead within N days
_INTERVAL_SECONDS = 24 * 3600  # run once per day
_TERMINAL_STAGES = {"won", "lost"}


async def send_lead_reminders() -> None:
    from sqlalchemy import select, update as sa_update
    from adapters.outbound.persistence.models.lead_model import LeadModel
    from adapters.outbound.persistence.models.user_model import UserModel
    from adapters.outbound.persistence.models.customer_model import CustomerModel
    from adapters.outbound.persistence.models.tenant_model import TenantModel

    now = datetime.utcnow()
    inactive_cutoff = now - timedelta(days=INACTIVE_THRESHOLD_DAYS)
    resend_cutoff = now - timedelta(days=RESEND_AFTER_DAYS)

    mailer = SmtpEmailAdapter()

    async with async_session_factory() as session:
        # Fetch all stale, non-terminal leads
        result = await session.execute(
            select(LeadModel).where(
                LeadModel.updated_at < inactive_cutoff,
                LeadModel.stage.notin_(list(_TERMINAL_STAGES)),
            ).order_by(LeadModel.tenant_id, LeadModel.updated_at)
        )
        leads = result.scalars().all()

        processed: dict[str, tuple] = {}  # tenant_id → (admin, tenant)

        for lead in leads:
            # Skip if a reminder was sent recently
            if (
                lead.last_inactivity_email_at is not None
                and lead.last_inactivity_email_at > resend_cutoff
            ):
                continue

            tid = str(lead.tenant_id)

            # Cache tenant admin per tenant to avoid redundant queries
            if tid not in processed:
                admin_res = await session.execute(
                    select(UserModel).where(
                        UserModel.tenant_id == lead.tenant_id,
                        UserModel.role == "admin",
                        UserModel.is_active == True,
                    ).limit(1)
                )
                admin = admin_res.scalar_one_or_none()

                tenant_res = await session.execute(
                    select(TenantModel).where(TenantModel.id == lead.tenant_id)
                )
                tenant = tenant_res.scalar_one_or_none()

                processed[tid] = (admin, tenant)
            else:
                admin, tenant = processed[tid]

            if not admin or not tenant:
                continue

            # Resolve customer name if linked
            customer_name = ""
            if lead.customer_id:
                cust_res = await session.execute(
                    select(CustomerModel).where(
                        CustomerModel.id == lead.customer_id,
                        CustomerModel.tenant_id == lead.tenant_id,
                    )
                )
                cust = cust_res.scalar_one_or_none()
                if cust:
                    customer_name = cust.name

            days_inactive = (now - lead.updated_at).days

            subject, html = tmpl.lead_inactive(
                name=admin.name,
                tenant_name=tenant.name,
                lead_title=lead.title,
                customer_name=customer_name,
                days_inactive=days_inactive,
                stage=lead.stage,
                value=lead.value or 0.0,
                lead_id=str(lead.id),
                app_url=settings.app_url,
            )

            try:
                await mailer.send(to=admin.email, subject=subject, html=html)
                await session.execute(
                    sa_update(LeadModel)
                    .where(LeadModel.id == lead.id)
                    .values(last_inactivity_email_at=now)
                )
                logger.info(
                    "lead_inactivity_reminder_sent",
                    lead_id=str(lead.id),
                    tenant_id=tid,
                    days_inactive=days_inactive,
                )
            except Exception as exc:
                logger.error(
                    "lead_inactivity_reminder_failed",
                    lead_id=str(lead.id),
                    error=str(exc),
                )

        await session.commit()


async def run_lead_reminder_loop() -> None:
    logger.info("lead_reminder_loop_started", interval_hours=_INTERVAL_SECONDS / 3600)
    await asyncio.sleep(90)  # wait a bit after startup
    while True:
        try:
            await send_lead_reminders()
            logger.info("lead_reminder_cycle_done")
        except Exception as exc:
            logger.error("lead_reminder_cycle_failed", error=str(exc))
        await asyncio.sleep(_INTERVAL_SECONDS)

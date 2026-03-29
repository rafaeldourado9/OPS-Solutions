"""Background task: sends trial warning and expiry emails to tenant admins.

Milestones:
  - "7d"      → sent when 1 < days_remaining <= 7  (and not yet sent)
  - "1d"      → sent when 0 < days_remaining <= 1  (and not yet sent)
  - "expired" → sent when days_remaining == 0       (and not yet sent)

The sent milestones are persisted in tenant.settings["trial_reminders_sent"]
to guarantee at-most-once delivery even across restarts.
"""
from __future__ import annotations

import asyncio
from datetime import datetime

import structlog

from adapters.outbound.email.smtp_adapter import SmtpEmailAdapter
from adapters.outbound.email import templates as tmpl
from adapters.outbound.persistence.database import async_session_factory
from infrastructure.config import settings

logger = structlog.get_logger()

_INTERVAL_SECONDS = 12 * 3600  # run every 12 h


async def send_trial_reminders() -> None:
    """Query all tenants on trial and dispatch pending reminder emails."""
    from sqlalchemy import select, update as sa_update
    from adapters.outbound.persistence.models.tenant_model import TenantModel
    from adapters.outbound.persistence.models.user_model import UserModel

    mailer = SmtpEmailAdapter()

    async with async_session_factory() as session:
        # Load every active tenant that still has a trial_ends_at set
        result = await session.execute(
            select(TenantModel).where(
                TenantModel.is_active == True,
                TenantModel.trial_ends_at != None,  # noqa: E711
            )
        )
        tenants = result.scalars().all()

        for tenant in tenants:
            try:
                await _process_tenant(session, mailer, tenant)
            except Exception as exc:
                logger.error(
                    "trial_reminder_error",
                    tenant_id=str(tenant.id),
                    error=str(exc),
                )

        await session.commit()


async def _process_tenant(session, mailer: SmtpEmailAdapter, tenant) -> None:
    from sqlalchemy import select, update as sa_update
    from adapters.outbound.persistence.models.user_model import UserModel
    from adapters.outbound.persistence.models.tenant_model import TenantModel

    now = datetime.utcnow()
    delta = tenant.trial_ends_at - now
    days_remaining = max(int(delta.total_seconds() / 86400), 0)

    current_settings = dict(tenant.raw_settings or {})
    sent: list[str] = list(current_settings.get("trial_reminders_sent", []))

    # Determine which milestone applies right now
    milestone: str | None = None
    if days_remaining == 0 and "expired" not in sent:
        milestone = "expired"
    elif 0 < days_remaining <= 1 and "1d" not in sent:
        milestone = "1d"
    elif 1 < days_remaining <= 7 and "7d" not in sent:
        milestone = "7d"

    if milestone is None:
        return

    # Find admin user for this tenant
    result = await session.execute(
        select(UserModel).where(
            UserModel.tenant_id == tenant.id,
            UserModel.role == "admin",
            UserModel.is_active == True,
        ).limit(1)
    )
    admin = result.scalar_one_or_none()
    if admin is None:
        return

    # Build and send email
    app_url = settings.app_url
    if milestone == "expired":
        subject, html = tmpl.trial_expired(admin.name, tenant.name, app_url)
    else:
        subject, html = tmpl.trial_warning(admin.name, tenant.name, days_remaining, app_url)

    await mailer.send(to=admin.email, subject=subject, html=html)

    # Mark milestone as sent
    sent.append(milestone)
    current_settings["trial_reminders_sent"] = sent
    await session.execute(
        sa_update(TenantModel)
        .where(TenantModel.id == tenant.id)
        .values(settings=current_settings)
    )

    logger.info(
        "trial_reminder_sent",
        tenant_id=str(tenant.id),
        milestone=milestone,
        email=admin.email,
    )


async def run_trial_reminder_loop() -> None:
    """Infinite loop that fires send_trial_reminders every _INTERVAL_SECONDS."""
    logger.info("trial_reminder_loop_started", interval_hours=_INTERVAL_SECONDS / 3600)
    # Wait a bit before first run so the DB is fully ready
    await asyncio.sleep(60)
    while True:
        try:
            await send_trial_reminders()
            logger.info("trial_reminder_cycle_done")
        except Exception as exc:
            logger.error("trial_reminder_cycle_failed", error=str(exc))
        await asyncio.sleep(_INTERVAL_SECONDS)

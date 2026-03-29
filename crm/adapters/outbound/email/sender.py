"""Centralised async email sender — never raises, always logs."""
import structlog
from infrastructure.config import settings

logger = structlog.get_logger()


async def send_email(to: str, subject: str, html: str) -> bool:
    """Send an email. Returns True on success, False on failure or unconfigured."""
    if not settings.smtp_user:
        logger.debug("email_skipped_no_smtp", to=to)
        return False
    try:
        from adapters.outbound.email.smtp_adapter import SmtpEmailAdapter
        await SmtpEmailAdapter().send(to, subject, html)
        logger.info("email_sent", to=to, subject=subject)
        return True
    except Exception as exc:
        logger.warning("email_failed", to=to, subject=subject, error=str(exc))
        return False


async def send_welcome(email: str, name: str, tenant_name: str) -> None:
    from adapters.outbound.email.templates import welcome
    subject, html = welcome(name, tenant_name, settings.app_url)
    await send_email(email, subject, html)


async def send_new_login(email: str, name: str, tenant_name: str, ip: str) -> None:
    from adapters.outbound.email.templates import new_login
    subject, html = new_login(name, tenant_name, ip, settings.app_url)
    await send_email(email, subject, html)

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from infrastructure.config import settings


class SmtpEmailAdapter:
    async def send(self, to: str, subject: str, html: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.email_from
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._send_sync, to, msg)

    def _send_sync(self, to: str, msg: MIMEMultipart) -> None:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_tls:
                server.starttls()
            if settings.smtp_user and settings.smtp_pass:
                server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(settings.email_from, [to], msg.as_string())

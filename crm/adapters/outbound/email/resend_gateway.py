"""Email gateway using SMTP (Brevo, Gmail, Mailgun, etc.).

Setup (Brevo — recomendado, grátis 300 emails/dia):
1. Acesse https://app.brevo.com → crie conta gratuita
2. SMTP & API → SMTP → gere uma Master password (SMTP key)
3. No .env:
   SMTP_HOST=smtp-relay.brevo.com
   SMTP_PORT=587
   SMTP_USER=seu@email.com
   SMTP_PASS=xsmtpsib-xxxxxxxx...
   EMAIL_FROM=OPS Solutions <suporte@ops.solutions.com>

Setup (Gmail com App Password):
1. Ative verificação em 2 etapas na conta Google
2. myaccount.google.com → Segurança → Senhas de app → gere uma
3. No .env:
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=seugmail@gmail.com
   SMTP_PASS=xxxx xxxx xxxx xxxx
   EMAIL_FROM=OPS Solutions <seugmail@gmail.com>
"""
import asyncio
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

from infrastructure.config import settings

logger = structlog.get_logger()


def _send_smtp_sync(to: str, subject: str, html: str) -> bool:
    """Blocking SMTP send — runs in a thread so it doesn't block the event loop."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to
    msg.attach(MIMEText(html, "html", "utf-8"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_tls:
                server.starttls(context=context)
            server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(settings.email_from, [to], msg.as_string())
        return True
    except Exception as e:
        logger.error("smtp_send_error", to=to, error=str(e))
        return False


async def send_email(to: str, subject: str, html: str) -> bool:
    """Send email via SMTP in a thread pool. Returns True on success."""
    if not settings.smtp_user or not settings.smtp_pass:
        logger.warning("smtp_not_configured", to=to, subject=subject)
        return False

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None, _send_smtp_sync, to, subject, html
        )
        if result:
            logger.info("email_sent", to=to, subject=subject)
        return result
    except Exception as e:
        logger.error("email_send_error", to=to, error=str(e))
        return False


def beta_welcome_email(name: str, plan: str | None = None) -> str:
    plan_text = f" ({plan})" if plan else ""
    greeting = f", {name}" if name else ""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>Bem-vindo à OPS Solutions</title>
</head>
<body style="margin:0;padding:0;background:#F5F5F7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F5F7;padding:40px 20px;">
    <tr><td align="center">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg,#0ABAB5 0%,#089B97 100%);padding:40px 48px;text-align:center;">
            <div style="display:inline-block;background:rgba(255,255,255,0.15);border-radius:16px;padding:12px 20px;">
              <span style="color:#fff;font-size:20px;font-weight:700;letter-spacing:-0.5px;">OPS Solutions</span>
            </div>
            <p style="color:rgba(255,255,255,0.85);margin:16px 0 0;font-size:14px;">Plataforma B2B Unificada</p>
          </td>
        </tr>
        <tr>
          <td style="padding:48px;">
            <h1 style="margin:0 0 8px;font-size:26px;font-weight:700;color:#1D1D1F;letter-spacing:-0.5px;">
              Bem-vindo ao beta{greeting}! 🎉
            </h1>
            <p style="margin:0 0 24px;font-size:15px;color:#6B7280;line-height:1.6;">
              Você está na lista de beta testers{plan_text}. Seu acesso de
              <strong>14 dias grátis</strong> será ativado em breve.
            </p>
            <div style="background:#F0FFFE;border:1px solid #0ABAB5;border-radius:12px;padding:20px 24px;margin-bottom:32px;">
              <p style="margin:0 0 12px;font-size:13px;font-weight:600;color:#0ABAB5;text-transform:uppercase;letter-spacing:0.1em;">O que você vai ter acesso</p>
              <ul style="margin:0;padding:0 0 0 20px;color:#374151;font-size:14px;line-height:2;">
                <li>CRM completo com pipeline Kanban</li>
                <li>Agentes de IA no WhatsApp com RAG</li>
                <li>Conversas em tempo real com takeover humano</li>
                <li>Orçamentos automáticos com templates DOCX</li>
                <li>Dashboard de analytics e KPIs</li>
              </ul>
            </div>
            <p style="margin:0 0 32px;font-size:14px;color:#6B7280;line-height:1.6;">
              Entraremos em contato em até <strong>24 horas</strong> com suas credenciais.
              Dúvidas? Responda este e-mail diretamente.
            </p>
            <div style="text-align:center;">
              <a href="https://ops.solutions.com"
                 style="display:inline-block;background:#0ABAB5;color:#fff;font-size:15px;font-weight:600;padding:14px 36px;border-radius:100px;text-decoration:none;">
                Conhecer a plataforma
              </a>
            </div>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 48px;border-top:1px solid #F3F4F6;text-align:center;">
            <p style="margin:0;font-size:12px;color:#9CA3AF;">
              © 2026 OPS Solutions · suporte@ops.solutions.com
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

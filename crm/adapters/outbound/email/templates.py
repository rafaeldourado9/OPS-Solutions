"""HTML email templates for platform onboarding and trial lifecycle emails."""
from __future__ import annotations


def _base(title: str, body: str, app_url: str, cta_text: str, cta_url: str) -> tuple[str, str]:
    """Returns (subject, html)."""
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#F4F4F5;font-family:'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F4F5;padding:40px 0">
  <tr><td align="center">
    <table width="520" cellpadding="0" cellspacing="0"
           style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 2px 16px rgba(0,0,0,0.07)">

      <!-- Header -->
      <tr>
        <td style="background:#0A1628;padding:28px 40px;text-align:center">
          <table cellpadding="0" cellspacing="0" style="display:inline-table">
            <tr>
              <td style="padding-right:10px;vertical-align:middle">
                <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polygon points="16,2 28,9 28,23 16,30 4,23 4,9" stroke="#0ABAB5" stroke-width="2" fill="none"/>
                  <circle cx="16" cy="16" r="3" fill="#0ABAB5"/>
                  <line x1="16" y1="13" x2="16" y2="5" stroke="#0ABAB5" stroke-width="1.5"/>
                  <line x1="18.6" y1="14.5" x2="25.4" y2="10.5" stroke="#0ABAB5" stroke-width="1.5"/>
                  <line x1="18.6" y1="17.5" x2="25.4" y2="21.5" stroke="#0ABAB5" stroke-width="1.5"/>
                  <circle cx="16" cy="4.5" r="1.5" fill="#0ABAB5"/>
                  <circle cx="26.5" cy="10.5" r="1.5" fill="#0ABAB5"/>
                  <circle cx="26.5" cy="21.5" r="1.5" fill="#0ABAB5"/>
                </svg>
              </td>
              <td style="vertical-align:middle">
                <span style="color:#ffffff;font-weight:600;font-size:16px;letter-spacing:-0.3px">OPS Solutions</span>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- Body -->
      <tr>
        <td style="padding:40px 40px 32px">
          {body}
        </td>
      </tr>

      <!-- CTA -->
      <tr>
        <td style="padding:0 40px 40px;text-align:center">
          <a href="{cta_url}"
             style="display:inline-block;background:#0ABAB5;color:#ffffff;font-weight:600;
                    font-size:15px;text-decoration:none;padding:14px 32px;border-radius:10px;
                    letter-spacing:-0.2px">
            {cta_text}
          </a>
        </td>
      </tr>

      <!-- Footer -->
      <tr>
        <td style="background:#F9FAFB;padding:20px 40px;text-align:center;
                   border-top:1px solid #E4E4E7">
          <p style="margin:0;color:#A1A1AA;font-size:12px;line-height:1.6">
            OPS Solutions &mdash; Plataforma CRM White-Label<br/>
            <a href="{app_url}" style="color:#0ABAB5;text-decoration:none">{app_url}</a>
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""
    return title, html


def welcome(name: str, tenant_name: str, app_url: str) -> tuple[str, str]:
    first = name.split()[0]
    subject = f"Bem-vindo(a) ao OPS Solutions, {first}! Sua operação começa agora 🚀"
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#F4F4F5;font-family:'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F4F5;padding:32px 0 48px">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%">

  <!-- Logo bar -->
  <tr>
    <td align="center" style="padding-bottom:20px">
      <table cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding-right:8px;vertical-align:middle">
            <svg width="24" height="24" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polygon points="16,2 28,9 28,23 16,30 4,23 4,9" stroke="#0ABAB5" stroke-width="2" fill="none"/>
              <circle cx="16" cy="16" r="3" fill="#0ABAB5"/>
              <line x1="16" y1="13" x2="16" y2="5" stroke="#0ABAB5" stroke-width="1.5"/>
              <line x1="18.6" y1="14.5" x2="25.4" y2="10.5" stroke="#0ABAB5" stroke-width="1.5"/>
              <line x1="18.6" y1="17.5" x2="25.4" y2="21.5" stroke="#0ABAB5" stroke-width="1.5"/>
              <circle cx="16" cy="4.5" r="1.5" fill="#0ABAB5"/>
              <circle cx="26.5" cy="10.5" r="1.5" fill="#0ABAB5"/>
              <circle cx="26.5" cy="21.5" r="1.5" fill="#0ABAB5"/>
            </svg>
          </td>
          <td style="vertical-align:middle">
            <span style="color:#1D1D1F;font-weight:700;font-size:15px;letter-spacing:-0.3px">OPS Solutions</span>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- GIF hero -->
  <tr>
    <td style="border-radius:20px 20px 0 0;overflow:hidden;background:#0A1628;padding:0;line-height:0">
      <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExb2kxbzFjcHR0aXVpanA3dWlwNHc1NHBieXhtcHR3dGV3bWh6dGV3eSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l4FGni1RBAR2OWsGk/giphy.gif"
           alt="Bem-vindo!" width="560" style="width:100%;max-width:560px;display:block;border-radius:20px 20px 0 0"/>
    </td>
  </tr>

  <!-- Main card -->
  <tr>
    <td style="background:#ffffff;border-radius:0 0 20px 20px;padding:36px 40px 32px;box-shadow:0 4px 24px rgba(0,0,0,0.08)">

      <!-- Headline -->
      <h1 style="margin:0 0 6px;color:#1D1D1F;font-size:26px;font-weight:800;letter-spacing:-0.5px;line-height:1.2">
        Eaí, {first}! 👋<br/>Seja bem-vindo(a) ao OPS.
      </h1>
      <p style="margin:0 0 24px;color:#52525B;font-size:15px;line-height:1.7">
        A conta <strong style="color:#1D1D1F">{tenant_name}</strong> foi criada com sucesso.
        Você tem <strong style="color:#0ABAB5">14 dias grátis</strong> pra explorar tudo —
        sem cartão, sem pegadinha.
      </p>

      <!-- Trial badge -->
      <table cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:28px">
        <tr>
          <td style="background:linear-gradient(135deg,#0ABAB5,#089B97);border-radius:14px;padding:18px 24px">
            <table cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td>
                  <p style="margin:0 0 3px;color:rgba(255,255,255,0.75);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em">Seu trial ativo</p>
                  <p style="margin:0;color:#ffffff;font-size:20px;font-weight:800;letter-spacing:-0.3px">14 dias de acesso completo</p>
                </td>
                <td align="right" style="font-size:32px;line-height:1">🎯</td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- Features -->
      <p style="margin:0 0 14px;color:#1D1D1F;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em">O que você pode fazer agora</p>
      <table cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:28px">
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid #F4F4F5">
            <table cellpadding="0" cellspacing="0"><tr>
              <td style="font-size:20px;padding-right:14px;vertical-align:middle">🤖</td>
              <td style="vertical-align:middle">
                <p style="margin:0;font-size:14px;font-weight:600;color:#1D1D1F">Agente IA no WhatsApp</p>
                <p style="margin:0;font-size:12px;color:#71717A">Configure e conecte seu número em minutos</p>
              </td>
            </tr></table>
          </td>
        </tr>
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid #F4F4F5">
            <table cellpadding="0" cellspacing="0"><tr>
              <td style="font-size:20px;padding-right:14px;vertical-align:middle">📋</td>
              <td style="vertical-align:middle">
                <p style="margin:0;font-size:14px;font-weight:600;color:#1D1D1F">Pipeline de leads (Kanban)</p>
                <p style="margin:0;font-size:12px;color:#71717A">Do primeiro contato ao fechamento</p>
              </td>
            </tr></table>
          </td>
        </tr>
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid #F4F4F5">
            <table cellpadding="0" cellspacing="0"><tr>
              <td style="font-size:20px;padding-right:14px;vertical-align:middle">📄</td>
              <td style="vertical-align:middle">
                <p style="margin:0;font-size:14px;font-weight:600;color:#1D1D1F">Orçamentos em PDF</p>
                <p style="margin:0;font-size:12px;color:#71717A">Templates DOCX + geração automática</p>
              </td>
            </tr></table>
          </td>
        </tr>
        <tr>
          <td style="padding:10px 0">
            <table cellpadding="0" cellspacing="0"><tr>
              <td style="font-size:20px;padding-right:14px;vertical-align:middle">💬</td>
              <td style="vertical-align:middle">
                <p style="margin:0;font-size:14px;font-weight:600;color:#1D1D1F">Takeover humano em tempo real</p>
                <p style="margin:0;font-size:12px;color:#71717A">Assuma a conversa quando quiser</p>
              </td>
            </tr></table>
          </td>
        </tr>
      </table>

      <!-- CTA -->
      <table cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:28px">
        <tr>
          <td align="center">
            <a href="{app_url}/app/dashboard"
               style="display:inline-block;background:#0ABAB5;color:#ffffff;font-weight:700;
                      font-size:16px;text-decoration:none;padding:16px 40px;border-radius:12px;
                      letter-spacing:-0.2px;box-shadow:0 6px 20px rgba(10,186,181,0.35)">
              Acessar minha conta →
            </a>
          </td>
        </tr>
      </table>

      <!-- Fun GIF 2 -->
      <table cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:24px">
        <tr>
          <td align="center" style="border-radius:12px;overflow:hidden;background:#F8FAFC;padding:4px">
            <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHRjaGp5aGV5Z3pkeWlhNWd6cGlzNnp0NzVkMzBpeW10bGlrNzBrbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKtnuHOHHUjR38Y/giphy.gif"
                 alt="Let's go!" width="320" style="max-width:320px;width:100%;border-radius:10px;display:block;margin:0 auto"/>
          </td>
        </tr>
        <tr><td align="center" style="padding-top:8px">
          <p style="margin:0;font-size:12px;color:#A1A1AA;font-style:italic">você nos próximos 14 dias 👆</p>
        </td></tr>
      </table>

      <p style="margin:0;color:#A1A1AA;font-size:12px;line-height:1.7;text-align:center">
        Dúvidas? Só responder este e-mail — somos gente boa 😄<br/>
        <a href="{app_url}" style="color:#0ABAB5;text-decoration:none;font-weight:600">solutionsops.com.br</a>
      </p>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td align="center" style="padding-top:24px">
      <p style="margin:0;color:#C4C4C7;font-size:11px;line-height:1.6">
        OPS Solutions · Você está recebendo este e-mail porque criou uma conta.<br/>
        © 2026 OPS Solutions. Todos os direitos reservados.
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return subject, html


def trial_warning(name: str, tenant_name: str, days_remaining: int, app_url: str) -> tuple[str, str]:
    first = name.split()[0]
    urgency_color = "#F59E0B" if days_remaining > 1 else "#EF4444"
    days_label = f"{days_remaining} dia{'s' if days_remaining != 1 else ''}"
    body = f"""
      <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:10px;
                  padding:16px 20px;margin-bottom:24px">
        <p style="margin:0;color:{urgency_color};font-weight:600;font-size:14px">
          ⏰ Seu trial expira em {days_label}
        </p>
      </div>
      <h2 style="margin:0 0 8px;color:#1D1D1F;font-size:22px;font-weight:700;letter-spacing:-0.4px">
        Oi, {first}! Não perca o acesso.
      </h2>
      <p style="margin:0 0 16px;color:#52525B;font-size:15px;line-height:1.6">
        O trial da conta <strong>{tenant_name}</strong> se encerra em <strong>{days_label}</strong>.
        Para continuar usando o CRM sem interrupção, escolha um plano agora.
      </p>
      <p style="margin:0;color:#71717A;font-size:13px;line-height:1.6">
        Dúvidas? Basta responder este e-mail — estamos aqui para ajudar.
      </p>
    """
    subject = (
        f"Seu trial expira amanhã — garanta seu plano, {first}"
        if days_remaining <= 1
        else f"Faltam {days_label} para o fim do seu trial, {first}"
    )
    return _base(
        title=subject,
        body=body,
        app_url=app_url,
        cta_text="Escolher um plano",
        cta_url=f"{app_url}/app/settings",
    )


def trial_expired(name: str, tenant_name: str, app_url: str) -> tuple[str, str]:
    first = name.split()[0]
    body = f"""
      <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;
                  padding:16px 20px;margin-bottom:24px">
        <p style="margin:0;color:#EF4444;font-weight:600;font-size:14px">
          Trial encerrado
        </p>
      </div>
      <h2 style="margin:0 0 8px;color:#1D1D1F;font-size:22px;font-weight:700;letter-spacing:-0.4px">
        {first}, seu trial expirou.
      </h2>
      <p style="margin:0 0 16px;color:#52525B;font-size:15px;line-height:1.6">
        O período de trial da conta <strong>{tenant_name}</strong> chegou ao fim.
        Seus dados estão salvos — ative um plano para recuperar o acesso completo.
      </p>
      <p style="margin:0;color:#71717A;font-size:13px;line-height:1.6">
        Precisa de ajuda para escolher o plano certo? Responda este e-mail.
      </p>
    """
    return _base(
        title=f"Seu trial expirou, {first} — reative sua conta",
        body=body,
        app_url=app_url,
        cta_text="Reativar agora",
        cta_url=f"{app_url}/app/settings",
    )


def quote_accepted(
    name: str,
    tenant_name: str,
    quote_title: str,
    customer_name: str,
    total: float,
    quote_id: str,
    app_url: str,
) -> tuple[str, str]:
    """Sent to the tenant admin when a quote status changes to 'accepted'."""
    first = name.split()[0]
    total_fmt = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    body = f"""
      <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;
                  padding:16px 20px;margin-bottom:24px;display:flex;align-items:center;gap:12px">
        <span style="font-size:24px">🎉</span>
        <p style="margin:0;color:#15803D;font-weight:700;font-size:15px">
          Orçamento aprovado!
        </p>
      </div>
      <h2 style="margin:0 0 8px;color:#1D1D1F;font-size:22px;font-weight:700;letter-spacing:-0.4px">
        {first}, você fechou mais um negócio.
      </h2>
      <p style="margin:0 0 20px;color:#52525B;font-size:15px;line-height:1.6">
        O orçamento abaixo foi marcado como <strong>aprovado</strong> na conta
        <strong>{tenant_name}</strong>.
      </p>

      <!-- Quote card -->
      <table cellpadding="0" cellspacing="0" width="100%"
             style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                    overflow:hidden;margin-bottom:24px">
        <tr>
          <td style="padding:20px 24px;border-bottom:1px solid #E2E8F0">
            <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#94A3B8;
                      text-transform:uppercase;letter-spacing:0.1em">Orçamento</p>
            <p style="margin:0;font-size:17px;font-weight:700;color:#1D1D1F">{quote_title}</p>
          </td>
        </tr>
        <tr>
          <td>
            <table cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td style="padding:16px 24px;border-right:1px solid #E2E8F0;width:50%">
                  <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#94A3B8;
                            text-transform:uppercase;letter-spacing:0.1em">Cliente</p>
                  <p style="margin:0;font-size:14px;font-weight:600;color:#1D1D1F">
                    {customer_name or "—"}
                  </p>
                </td>
                <td style="padding:16px 24px;width:50%">
                  <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#94A3B8;
                            text-transform:uppercase;letter-spacing:0.1em">Valor total</p>
                  <p style="margin:0;font-size:22px;font-weight:800;color:#0ABAB5;
                            font-family:monospace;letter-spacing:-0.5px">
                    {total_fmt}
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <p style="margin:0;color:#71717A;font-size:13px;line-height:1.6">
        Acesse o CRM para gerar o contrato ou enviar o documento ao cliente.
      </p>
    """
    return _base(
        title=f"🎉 Orçamento aprovado — {total_fmt}",
        body=body,
        app_url=app_url,
        cta_text="Ver orçamento no CRM",
        cta_url=f"{app_url}/app/quotes",
    )


def lead_inactive(
    name: str,
    tenant_name: str,
    lead_title: str,
    customer_name: str,
    days_inactive: int,
    stage: str,
    value: float,
    lead_id: str,
    app_url: str,
) -> tuple[str, str]:
    """Sent to the tenant admin when a lead has been inactive for too long."""
    first = name.split()[0]
    value_fmt = f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if value else "—"
    days_label = f"{days_inactive} dias"
    urgency = days_inactive >= 14

    stage_labels = {
        "new": "Novo", "contacted": "Contactado", "qualified": "Qualificado",
        "proposal": "Proposta enviada", "negotiation": "Negociação",
    }
    stage_label = stage_labels.get(stage, stage.capitalize())

    body = f"""
      <div style="background:{'#FEF2F2' if urgency else '#FFFBEB'};
                  border:1px solid {'#FECACA' if urgency else '#FDE68A'};
                  border-radius:10px;padding:16px 20px;margin-bottom:24px">
        <p style="margin:0;color:{'#DC2626' if urgency else '#D97706'};font-weight:700;font-size:14px">
          ⏰ Lead parado há {days_label}
        </p>
      </div>
      <h2 style="margin:0 0 8px;color:#1D1D1F;font-size:22px;font-weight:700;letter-spacing:-0.4px">
        {first}, este lead precisa de atenção.
      </h2>
      <p style="margin:0 0 20px;color:#52525B;font-size:15px;line-height:1.6">
        O lead <strong>{lead_title}</strong> na conta <strong>{tenant_name}</strong>
        não teve nenhuma atualização nos últimos <strong>{days_label}</strong>.
      </p>

      <!-- Lead card -->
      <table cellpadding="0" cellspacing="0" width="100%"
             style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                    overflow:hidden;margin-bottom:24px">
        <tr>
          <td style="padding:20px 24px;border-bottom:1px solid #E2E8F0">
            <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#94A3B8;
                      text-transform:uppercase;letter-spacing:0.1em">Lead</p>
            <p style="margin:0;font-size:17px;font-weight:700;color:#1D1D1F">{lead_title}</p>
          </td>
        </tr>
        <tr>
          <td>
            <table cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td style="padding:14px 24px;border-right:1px solid #E2E8F0;width:33%">
                  <p style="margin:0 0 3px;font-size:11px;font-weight:700;color:#94A3B8;
                            text-transform:uppercase;letter-spacing:0.1em">Cliente</p>
                  <p style="margin:0;font-size:13px;font-weight:600;color:#1D1D1F">
                    {customer_name or "—"}
                  </p>
                </td>
                <td style="padding:14px 24px;border-right:1px solid #E2E8F0;width:33%">
                  <p style="margin:0 0 3px;font-size:11px;font-weight:700;color:#94A3B8;
                            text-transform:uppercase;letter-spacing:0.1em">Estágio</p>
                  <p style="margin:0;font-size:13px;font-weight:600;color:#1D1D1F">
                    {stage_label}
                  </p>
                </td>
                <td style="padding:14px 24px;width:33%">
                  <p style="margin:0 0 3px;font-size:11px;font-weight:700;color:#94A3B8;
                            text-transform:uppercase;letter-spacing:0.1em">Valor</p>
                  <p style="margin:0;font-size:13px;font-weight:700;color:#0ABAB5;font-family:monospace">
                    {value_fmt}
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <p style="margin:0;color:#71717A;font-size:13px;line-height:1.6">
        Retome o contato agora para não perder este negócio.
      </p>
    """
    return _base(
        title=f"Lead parado há {days_label}: {lead_title}",
        body=body,
        app_url=app_url,
        cta_text="Acessar lead no CRM",
        cta_url=f"{app_url}/app/leads",
    )


def new_login(name: str, tenant_name: str, ip: str, app_url: str) -> tuple[str, str]:
    from datetime import datetime
    first = name.split()[0]
    now = datetime.utcnow().strftime("%d/%m/%Y às %H:%M UTC")
    body = f"""
      <h2 style="margin:0 0 8px;color:#1D1D1F;font-size:22px;font-weight:700;letter-spacing:-0.4px">
        Novo acesso detectado, {first}.
      </h2>
      <p style="margin:0 0 20px;color:#52525B;font-size:15px;line-height:1.6">
        Um novo login foi realizado na conta <strong>{tenant_name}</strong>.
      </p>
      <table cellpadding="0" cellspacing="0" width="100%"
             style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;overflow:hidden;margin-bottom:24px">
        <tr>
          <td style="padding:14px 24px;border-bottom:1px solid #E2E8F0">
            <p style="margin:0 0 3px;font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:0.1em">Horário</p>
            <p style="margin:0;font-size:14px;font-weight:600;color:#1D1D1F">{now}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:14px 24px">
            <p style="margin:0 0 3px;font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:0.1em">IP de origem</p>
            <p style="margin:0;font-size:14px;font-weight:600;color:#1D1D1F;font-family:monospace">{ip}</p>
          </td>
        </tr>
      </table>
      <p style="margin:0;color:#71717A;font-size:13px;line-height:1.6">
        Se foi você, pode ignorar este e-mail. Se não reconhece este acesso,
        <strong>altere sua senha imediatamente</strong>.
      </p>
    """
    return _base(
        title=f"Novo login na conta {tenant_name}",
        body=body,
        app_url=app_url,
        cta_text="Alterar minha senha",
        cta_url=f"{app_url}/app/settings",
    )


def _feature_row(icon: str, text: str) -> str:
    return f"""
      <tr>
        <td style="padding:6px 0">
          <table cellpadding="0" cellspacing="0">
            <tr>
              <td style="font-size:16px;padding-right:12px;vertical-align:top">{icon}</td>
              <td style="color:#52525B;font-size:14px;line-height:1.5">{text}</td>
            </tr>
          </table>
        </td>
      </tr>"""

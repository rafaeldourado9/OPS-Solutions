"""User management routes — list, invite, update role, deactivate, delete."""
import secrets
import string
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.api.middleware.auth import CurrentUser, get_current_user
from adapters.outbound.persistence.database import get_session
from adapters.outbound.persistence.models.user_model import UserModel
from adapters.outbound.persistence.repositories.pg_user_repository import PgUserRepository
from core.domain.user import Role, User
from infrastructure.config import settings
from infrastructure.security import hash_password

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/users", tags=["users"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    created_at: str


class InviteUserBody(BaseModel):
    name: str
    email: EmailStr
    role: str = "operator"


class UpdateRoleBody(BaseModel):
    role: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_admin(current_user: CurrentUser) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem gerenciar usuários")


def _user_out(u: User) -> UserOut:
    return UserOut(
        id=str(u.id),
        name=u.name,
        email=u.email,
        role=u.role.value,
        is_active=u.is_active,
        created_at=u.created_at.isoformat(),
    )


def _gen_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def _send_invite_email(to: str, name: str, tenant_name: str, temp_password: str) -> None:
    if not settings.smtp_user:
        return
    try:
        from adapters.outbound.email.smtp_adapter import SmtpEmailAdapter
        from adapters.outbound.email.templates import _base

        first = name.split()[0]
        body = f"""
          <h2 style="margin:0 0 8px;color:#1D1D1F;font-size:22px;font-weight:700;letter-spacing:-0.4px">
            Olá, {first}! Você foi convidado(a).
          </h2>
          <p style="margin:0 0 16px;color:#52525B;font-size:15px;line-height:1.6">
            Você foi adicionado(a) à conta <strong>{tenant_name}</strong> no OPS Solutions CRM.
          </p>
          <table cellpadding="0" cellspacing="0" width="100%"
                 style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;overflow:hidden;margin-bottom:24px">
            <tr>
              <td style="padding:16px 24px;border-bottom:1px solid #E2E8F0">
                <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:0.1em">E-mail</p>
                <p style="margin:0;font-size:14px;font-weight:600;color:#1D1D1F">{to}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:16px 24px">
                <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:0.1em">Senha temporária</p>
                <p style="margin:0;font-size:18px;font-weight:800;color:#0ABAB5;font-family:monospace;letter-spacing:2px">{temp_password}</p>
              </td>
            </tr>
          </table>
          <p style="margin:0;color:#71717A;font-size:13px;line-height:1.6">
            Acesse o CRM e troque sua senha após o primeiro login.
          </p>
        """
        subject, html = _base(
            title=f"Convite para {tenant_name} — OPS Solutions",
            body=body,
            app_url=settings.app_url,
            cta_text="Acessar o CRM",
            cta_url=f"{settings.app_url}/auth/login",
        )
        await SmtpEmailAdapter().send(to, subject, html)
    except Exception as exc:
        logger.warning("invite_email_failed", to=to, error=str(exc))


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[UserOut])
async def list_users(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    repo = PgUserRepository(session)
    users = await repo.list_by_tenant(current_user.tenant_id)
    return [_user_out(u) for u in users]


@router.post("/invite", response_model=UserOut, status_code=201)
async def invite_user(
    body: InviteUserBody,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _require_admin(current_user)

    if body.role not in {r.value for r in Role}:
        raise HTTPException(status_code=400, detail=f"Role inválida. Use: {[r.value for r in Role]}")

    repo = PgUserRepository(session)
    existing = await repo.get_by_email(current_user.tenant_id, body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Já existe um usuário com este e-mail nesta conta")

    temp_password = _gen_temp_password()
    user = User.create(
        tenant_id=current_user.tenant_id,
        email=body.email,
        password_hash=hash_password(temp_password),
        name=body.name,
        role=Role(body.role),
    )
    await repo.save(user)
    await session.commit()

    # Fetch tenant name for e-mail
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
    tenant_repo = PgTenantRepository(session)
    tenant = await tenant_repo.get_by_id(current_user.tenant_id)
    tenant_name = tenant.name if tenant else "OPS Solutions"

    import asyncio
    asyncio.create_task(_send_invite_email(body.email, body.name, tenant_name, temp_password))

    logger.info("user_invited", invited_email=body.email, role=body.role, by=str(current_user.user_id))
    return _user_out(user)


@router.put("/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: str,
    body: UpdateRoleBody,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _require_admin(current_user)

    if body.role not in {r.value for r in Role}:
        raise HTTPException(status_code=400, detail=f"Role inválida. Use: {[r.value for r in Role]}")

    if str(current_user.user_id) == user_id:
        raise HTTPException(status_code=400, detail="Você não pode alterar sua própria role")

    repo = PgUserRepository(session)
    user = await repo.get_by_id(UUID(user_id))
    if not user or str(user.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    await session.execute(
        sa_update(UserModel)
        .where(UserModel.id == UUID(user_id))
        .values(role=body.role)
    )
    await session.commit()

    user = await repo.get_by_id(UUID(user_id))
    return _user_out(user)


@router.put("/{user_id}/deactivate", response_model=UserOut)
async def deactivate_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _require_admin(current_user)

    if str(current_user.user_id) == user_id:
        raise HTTPException(status_code=400, detail="Você não pode desativar sua própria conta")

    repo = PgUserRepository(session)
    user = await repo.get_by_id(UUID(user_id))
    if not user or str(user.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    await session.execute(
        sa_update(UserModel)
        .where(UserModel.id == UUID(user_id))
        .values(is_active=not user.is_active)
    )
    await session.commit()

    user = await repo.get_by_id(UUID(user_id))
    return _user_out(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _require_admin(current_user)

    if str(current_user.user_id) == user_id:
        raise HTTPException(status_code=400, detail="Você não pode excluir sua própria conta")

    repo = PgUserRepository(session)
    user = await repo.get_by_id(UUID(user_id))
    if not user or str(user.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    await session.execute(
        sa_update(UserModel)
        .where(UserModel.id == UUID(user_id))
        .values(is_active=False)
    )
    await session.commit()

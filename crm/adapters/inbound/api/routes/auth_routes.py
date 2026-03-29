from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.api.dependencies import (
    get_login_uc,
    get_refresh_token_uc,
    get_register_tenant_uc,
)
from adapters.inbound.api.middleware.auth import get_current_user, CurrentUser
from adapters.outbound.persistence.database import get_session
from core.ports.inbound.auth_service import LoginRequest, RegisterTenantRequest
from core.use_cases.auth.login import LoginUseCase
from core.use_cases.auth.refresh_token import RefreshTokenUseCase
from core.use_cases.auth.register_tenant import RegisterTenantUseCase

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# --- Request / Response schemas ---

class RegisterRequest(BaseModel):
    tenant_name: str
    tenant_slug: str
    name: str
    email: str
    password: str
    agent_id: Optional[str] = None


class LoginRequestBody(BaseModel):
    email: str
    password: str
    tenant_slug: Optional[str] = None


class RefreshRequest(BaseModel):
    token: str


class UserInfo(BaseModel):
    id: str
    name: str
    email: str
    role: str
    avatar_url: Optional[str] = None


class TenantInfo(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    effective_plan: str = "starter"
    trial_ends_at: Optional[str] = None
    trial_days_remaining: int = 999
    niche: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo
    tenant: TenantInfo


class TokenResponseInternal(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    user_id: str
    role: str


# --- Endpoints ---

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def register_tenant(
    body: RegisterRequest,
    uc: RegisterTenantUseCase = Depends(get_register_tenant_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await uc.execute(
            RegisterTenantRequest(
                tenant_name=body.tenant_name,
                tenant_slug=body.tenant_slug,
                agent_id=body.agent_id or body.tenant_slug,
                admin_email=body.email,
                admin_password=body.password,
                admin_name=body.name,
            )
        )
        await session.commit()

        from adapters.outbound.persistence.repositories.pg_user_repository import PgUserRepository
        from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
        from uuid import UUID

        user_repo = PgUserRepository(session)
        tenant_repo = PgTenantRepository(session)
        user = await user_repo.get_by_id(UUID(result.user_id))
        tenant = await tenant_repo.get_by_id(UUID(result.tenant_id))

        response = TokenResponse(
            access_token=result.access_token,
            user=UserInfo(id=result.user_id, name=user.name, email=user.email, role=result.role, avatar_url=user.avatar_url),
            tenant=TenantInfo(
                id=result.tenant_id, name=tenant.name, slug=tenant.slug, plan=tenant.plan,
                effective_plan=tenant.effective_plan,
                trial_ends_at=tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
                trial_days_remaining=tenant.trial_days_remaining,
                niche=tenant.raw_settings.get("niche"),
            ),
        )

        from adapters.outbound.email.sender import send_welcome
        await send_welcome(user.email, user.name, tenant.name)

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequestBody,
    request: Request,
    uc: LoginUseCase = Depends(get_login_uc),
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await uc.execute(
            LoginRequest(
                email=body.email,
                password=body.password,
                tenant_slug=body.tenant_slug or "",
            )
        )
        from adapters.outbound.persistence.repositories.pg_user_repository import PgUserRepository
        from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
        from uuid import UUID

        user_repo = PgUserRepository(session)
        tenant_repo = PgTenantRepository(session)

        tenant = await tenant_repo.get_by_id(UUID(result.tenant_id))
        user = await user_repo.get_by_id(UUID(result.user_id))

        if not user or not tenant:
            raise ValueError("Invalid credentials")

        # New login notification
        ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "desconhecido")
        from adapters.outbound.email.sender import send_new_login
        await send_new_login(user.email, user.name, tenant.name, ip)

        return TokenResponse(
            access_token=result.access_token,
            user=UserInfo(
                id=result.user_id,
                name=user.name,
                email=user.email,
                role=result.role,
                avatar_url=user.avatar_url,
            ),
            tenant=TenantInfo(
                id=result.tenant_id,
                name=tenant.name,
                slug=tenant.slug,
                plan=tenant.plan,
                effective_plan=tenant.effective_plan,
                trial_ends_at=tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
                trial_days_remaining=tenant.trial_days_remaining,
                niche=tenant.raw_settings.get("niche"),
            ),
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )


@router.get("/me", response_model=TokenResponse)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from adapters.outbound.persistence.repositories.pg_user_repository import PgUserRepository
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository

    user_repo = PgUserRepository(session)
    tenant_repo = PgTenantRepository(session)
    user = await user_repo.get_by_id(current_user.user_id)
    tenant = await tenant_repo.get_by_id(current_user.tenant_id)
    if not user or not tenant:
        raise HTTPException(status_code=404, detail="User or tenant not found")
    return TokenResponse(
        access_token="",
        user=UserInfo(id=str(user.id), name=user.name, email=user.email, role=user.role.value, avatar_url=user.avatar_url),
        tenant=TenantInfo(
            id=str(tenant.id), name=tenant.name, slug=tenant.slug, plan=tenant.plan,
            effective_plan=tenant.effective_plan,
            trial_ends_at=tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
            trial_days_remaining=tenant.trial_days_remaining,
        ),
    )


class UpdateProfileBody(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


@router.put("/me", response_model=UserInfo)
async def update_me(
    body: UpdateProfileBody,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import update as sa_update
    from adapters.outbound.persistence.models.user_model import UserModel
    from adapters.outbound.persistence.repositories.pg_user_repository import PgUserRepository

    values: dict = {}
    if body.name is not None:
        values["name"] = body.name
    if body.email is not None:
        values["email"] = body.email
    if values:
        await session.execute(
            sa_update(UserModel).where(UserModel.id == current_user.user_id).values(**values)
        )
        await session.commit()

    user_repo = PgUserRepository(session)
    user = await user_repo.get_by_id(current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserInfo(id=str(user.id), name=user.name, email=user.email, role=user.role.value, avatar_url=user.avatar_url)


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


@router.put("/me/password", status_code=204)
async def change_password(
    body: ChangePasswordBody,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import update as sa_update
    from adapters.outbound.persistence.models.user_model import UserModel
    from adapters.outbound.persistence.repositories.pg_user_repository import PgUserRepository
    from infrastructure.security import verify_password, hash_password

    user_repo = PgUserRepository(session)
    user = await user_repo.get_by_id(current_user.user_id)
    if not user or not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    new_hash = hash_password(body.new_password)
    await session.execute(
        sa_update(UserModel).where(UserModel.id == current_user.user_id).values(password_hash=new_hash)
    )
    await session.commit()


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import update as sa_update
    from adapters.outbound.persistence.models.user_model import UserModel
    from adapters.outbound.storage.minio_adapter import MinioStorageAdapter

    if file.content_type not in ("image/png", "image/jpeg", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Formato inválido. Use PNG, JPEG ou WebP.")

    data = await file.read()
    if len(data) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máx 2MB)")

    storage = MinioStorageAdapter()

    key = f"avatars/{current_user.user_id}/{file.filename or 'avatar.jpg'}"
    await storage.upload(key=key, data=data, content_type=file.content_type or "image/jpeg")
    avatar_url = await storage.get_url(key)

    await session.execute(
        sa_update(UserModel).where(UserModel.id == current_user.user_id).values(avatar_url=avatar_url)
    )
    await session.commit()
    return {"avatar_url": avatar_url}


class TenantOut(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    primary_color: str
    secondary_color: str
    logo_url: Optional[str] = None


class UpdateTenantBody(BaseModel):
    name: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    niche: Optional[str] = None


@router.get("/tenant", response_model=TenantOut)
async def get_tenant(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository

    repo = PgTenantRepository(session)
    tenant = await repo.get_by_id(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantOut(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        plan=tenant.plan,
        primary_color=tenant.primary_color,
        secondary_color=tenant.secondary_color,
        logo_url=tenant.logo_url,
    )


@router.put("/tenant", response_model=TenantOut)
async def update_tenant(
    body: UpdateTenantBody,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import update as sa_update
    from adapters.outbound.persistence.models.tenant_model import TenantModel
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository

    from sqlalchemy import select as sa_select

    values: dict = {}
    if body.name is not None:
        values["name"] = body.name
    if body.primary_color is not None:
        values["primary_color"] = body.primary_color
    if body.secondary_color is not None:
        values["secondary_color"] = body.secondary_color

    if values:
        await session.execute(
            sa_update(TenantModel).where(TenantModel.id == current_user.tenant_id).values(**values)
        )

    # Save niche into settings JSONB
    if body.niche is not None:
        result = await session.execute(sa_select(TenantModel).where(TenantModel.id == current_user.tenant_id))
        tenant_model = result.scalar_one_or_none()
        if tenant_model:
            current_settings = dict(tenant_model.settings or {})
            current_settings["niche"] = body.niche
            tenant_model.settings = current_settings

    if values or body.niche is not None:
        await session.commit()

    repo = PgTenantRepository(session)
    tenant = await repo.get_by_id(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantOut(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        plan=tenant.plan,
        primary_color=tenant.primary_color,
        secondary_color=tenant.secondary_color,
        logo_url=tenant.logo_url,
    )


class IntegrationsBody(BaseModel):
    # SMTP kept for internal system emails (password reset, notifications) but hidden from UI
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    email_from: Optional[str] = None
    gemini_api_key: Optional[str] = None
    webhook_url: Optional[str] = None


class IntegrationsOut(BaseModel):
    gemini_api_key: str
    gemini_api_key_set: bool = False
    webhook_url: str = ""


@router.get("/tenant/integrations", response_model=IntegrationsOut)
async def get_integrations(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository

    repo = PgTenantRepository(session)
    tenant = await repo.get_by_id(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    integrations = (tenant.raw_settings or {}).get("integrations", {})
    raw_gemini = integrations.get("gemini_api_key") or ""
    return IntegrationsOut(
        gemini_api_key="",  # never return raw key
        gemini_api_key_set=bool(raw_gemini),
        webhook_url=integrations.get("webhook_url") or "",
    )


@router.put("/tenant/integrations", response_model=IntegrationsOut)
async def update_integrations(
    body: IntegrationsBody,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import update as sa_update
    from adapters.outbound.persistence.models.tenant_model import TenantModel
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository

    repo = PgTenantRepository(session)
    tenant = await repo.get_by_id(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    current_settings = dict(tenant.raw_settings or {})
    current_integrations = dict(current_settings.get("integrations", {}))

    patch = body.model_dump(exclude_none=True)
    current_integrations.update(patch)
    current_settings["integrations"] = current_integrations

    await session.execute(
        sa_update(TenantModel)
        .where(TenantModel.id == current_user.tenant_id)
        .values(settings=current_settings)
    )
    await session.commit()

    raw_gemini = current_integrations.get("gemini_api_key") or ""

    # Synchronize agent's business.yml with the new Gemini API Key
    if raw_gemini:
        try:
            import os
            import httpx
            from adapters.outbound.agents.filesystem_agent_config import FilesystemAgentConfig

            agents_dir = os.environ.get("AGENTS_DIR", "/app/shared-agents")
            agent_config_port = FilesystemAgentConfig(agents_dir)
            agents_api_url = os.environ.get("AGENTS_API_URL", "http://agent:8000")

            for agent_id in tenant.get_owned_agents():
                if agent_config_port.exists(agent_id):
                    config = agent_config_port.read(agent_id)
                    if "llm" not in config:
                        config["llm"] = {}
                    config["llm"]["api_key"] = raw_gemini
                    agent_config_port.write(agent_id, config)

                    # Inform the agent process to reload this agent's config
                    async with httpx.AsyncClient() as client:
                        await client.post(f"{agents_api_url}/reload/{agent_id}", timeout=5.0)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Failed to sync agent config")

    return IntegrationsOut(
        gemini_api_key="",  # never return raw key
        gemini_api_key_set=bool(raw_gemini),
        webhook_url=current_integrations.get("webhook_url") or "",
    )


# ── Company profile ───────────────────────────────────────────────────────────

class CompanyProfileBody(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    cnpj: Optional[str] = None
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_complement: Optional[str] = None
    address_neighborhood: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None


class CompanyProfileOut(BaseModel):
    phone: str
    email: str
    website: str
    cnpj: str
    address_street: str
    address_number: str
    address_complement: str
    address_neighborhood: str
    address_city: str
    address_state: str
    address_zip: str


class BankingBody(BaseModel):
    bank_name: Optional[str] = None
    agency: Optional[str] = None
    account: Optional[str] = None
    account_type: Optional[str] = None
    pix_key: Optional[str] = None
    pix_key_type: Optional[str] = None
    beneficiary: Optional[str] = None


class BankingOut(BaseModel):
    bank_name: str
    agency: str
    account: str
    account_type: str
    pix_key: str
    pix_key_type: str
    beneficiary: str


def _get_company(settings_json: dict) -> CompanyProfileOut:
    c = settings_json.get("company", {})
    return CompanyProfileOut(
        phone=c.get("phone", ""),
        email=c.get("email", ""),
        website=c.get("website", ""),
        cnpj=c.get("cnpj", ""),
        address_street=c.get("address_street", ""),
        address_number=c.get("address_number", ""),
        address_complement=c.get("address_complement", ""),
        address_neighborhood=c.get("address_neighborhood", ""),
        address_city=c.get("address_city", ""),
        address_state=c.get("address_state", ""),
        address_zip=c.get("address_zip", ""),
    )


def _get_banking(settings_json: dict) -> BankingOut:
    b = settings_json.get("banking", {})
    return BankingOut(
        bank_name=b.get("bank_name", ""),
        agency=b.get("agency", ""),
        account=b.get("account", ""),
        account_type=b.get("account_type", "corrente"),
        pix_key=b.get("pix_key", ""),
        pix_key_type=b.get("pix_key_type", "cpf_cnpj"),
        beneficiary=b.get("beneficiary", ""),
    )


@router.get("/tenant/company", response_model=CompanyProfileOut)
async def get_company_profile(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
    repo = PgTenantRepository(session)
    tenant = await repo.get_by_id(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return _get_company(tenant.raw_settings or {})


@router.put("/tenant/company", response_model=CompanyProfileOut)
async def update_company_profile(
    body: CompanyProfileBody,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import update as sa_update
    from adapters.outbound.persistence.models.tenant_model import TenantModel
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
    repo = PgTenantRepository(session)
    tenant = await repo.get_by_id(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    current = dict(tenant.raw_settings or {})
    company = dict(current.get("company", {}))
    company.update({k: v for k, v in body.model_dump(exclude_none=True).items()})
    current["company"] = company
    await session.execute(
        sa_update(TenantModel).where(TenantModel.id == current_user.tenant_id).values(settings=current)
    )
    await session.commit()
    return _get_company(current)


@router.get("/tenant/banking", response_model=BankingOut)
async def get_banking(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
    repo = PgTenantRepository(session)
    tenant = await repo.get_by_id(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return _get_banking(tenant.raw_settings or {})


@router.put("/tenant/banking", response_model=BankingOut)
async def update_banking(
    body: BankingBody,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import update as sa_update
    from adapters.outbound.persistence.models.tenant_model import TenantModel
    from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
    repo = PgTenantRepository(session)
    tenant = await repo.get_by_id(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    current = dict(tenant.raw_settings or {})
    banking = dict(current.get("banking", {}))
    banking.update({k: v for k, v in body.model_dump(exclude_none=True).items()})
    current["banking"] = banking
    await session.execute(
        sa_update(TenantModel).where(TenantModel.id == current_user.tenant_id).values(settings=current)
    )
    await session.commit()
    return _get_banking(current)


@router.post("/tenant/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload logo image to MinIO and update tenant logo_url."""
    from sqlalchemy import update as sa_update
    from adapters.outbound.persistence.models.tenant_model import TenantModel
    from adapters.outbound.storage.minio_adapter import MinioStorageAdapter

    content_type = file.content_type or "image/png"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    ext = content_type.split("/")[-1].replace("svg+xml", "svg").replace("jpeg", "jpg")
    key = f"logos/{current_user.tenant_id}/logo.{ext}"
    data = await file.read()
    if len(data) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 2MB)")

    storage = MinioStorageAdapter()
    await storage.upload(key, data, content_type)
    logo_url = await storage.get_url(key, expires_in=365 * 24 * 3600)

    await session.execute(
        sa_update(TenantModel)
        .where(TenantModel.id == current_user.tenant_id)
        .values(logo_url=logo_url)
    )
    await session.commit()
    return {"logo_url": logo_url}


class ForgotPasswordBody(BaseModel):
    email: str


class ResetPasswordBody(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password", status_code=202)
async def forgot_password(
    body: ForgotPasswordBody,
    session: AsyncSession = Depends(get_session),
):
    """Send a password reset link to the given email (all matching accounts across tenants)."""
    import secrets
    from datetime import timedelta
    from sqlalchemy import select
    from uuid import uuid4

    from adapters.outbound.email.smtp_adapter import SmtpEmailAdapter
    from adapters.outbound.persistence.models.user_model import UserModel
    from adapters.outbound.persistence.models.password_reset_token_model import PasswordResetTokenModel
    from infrastructure.config import settings

    result = await session.execute(
        select(UserModel).where(UserModel.email == body.email, UserModel.is_active == True)
    )
    users = result.scalars().all()

    if not users:
        # Return 202 anyway to avoid user enumeration
        return {"detail": "Se o e-mail existir, um link será enviado."}

    mailer = SmtpEmailAdapter()

    for user in users:
        token_str = secrets.token_urlsafe(64)
        expires_at = datetime.utcnow() + timedelta(minutes=30)

        reset_token = PasswordResetTokenModel(
            id=uuid4(),
            user_id=user.id,
            token=token_str,
            expires_at=expires_at,
        )
        session.add(reset_token)

        reset_url = f"{settings.app_url}/auth/reset-password?token={token_str}"
        html = f"""
        <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px">
            <h2 style="color:#1D1D1F">Recuperação de senha</h2>
            <p style="color:#555">Recebemos uma solicitação para redefinir a senha da conta associada a este e-mail.</p>
            <p style="color:#555">Clique no botão abaixo para criar uma nova senha. O link expira em <strong>30 minutos</strong>.</p>
            <a href="{reset_url}"
               style="display:inline-block;margin:24px 0;padding:14px 28px;background:#0ABAB5;color:white;
                      text-decoration:none;border-radius:10px;font-weight:600">
                Redefinir senha
            </a>
            <p style="color:#888;font-size:13px">Se você não solicitou isso, ignore este e-mail. Sua senha permanece a mesma.</p>
        </div>
        """

        try:
            await mailer.send(to=user.email, subject="Recuperação de senha", html=html)
        except Exception:
            pass  # silently fail — do not reveal SMTP errors to the caller

    await session.commit()
    return {"detail": "Se o e-mail existir, um link será enviado."}


@router.post("/reset-password", status_code=204)
async def reset_password(
    body: ResetPasswordBody,
    session: AsyncSession = Depends(get_session),
):
    """Validate the reset token and update the user password."""
    from sqlalchemy import select, update as sa_update

    from adapters.outbound.persistence.models.user_model import UserModel
    from adapters.outbound.persistence.models.password_reset_token_model import PasswordResetTokenModel
    from infrastructure.security import hash_password

    result = await session.execute(
        select(PasswordResetTokenModel).where(PasswordResetTokenModel.token == body.token)
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token or reset_token.used or reset_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Link inválido ou expirado.")

    if len(body.new_password) < 6:
        raise HTTPException(status_code=422, detail="A senha deve ter pelo menos 6 caracteres.")

    new_hash = hash_password(body.new_password)

    await session.execute(
        sa_update(UserModel)
        .where(UserModel.id == reset_token.user_id)
        .values(password_hash=new_hash)
    )
    await session.execute(
        sa_update(PasswordResetTokenModel)
        .where(PasswordResetTokenModel.token == body.token)
        .values(used=True)
    )
    await session.commit()


@router.post("/refresh")
async def refresh_token(
    body: RefreshRequest,
    uc: RefreshTokenUseCase = Depends(get_refresh_token_uc),
):
    try:
        result = await uc.execute(body.token)
        return {
            "access_token": result.access_token,
            "token_type": result.token_type,
            "tenant_id": result.tenant_id,
            "user_id": result.user_id,
            "role": result.role,
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

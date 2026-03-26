from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.api.dependencies import (
    get_login_uc,
    get_refresh_token_uc,
    get_register_tenant_uc,
)
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
    agent_id: str
    admin_email: str
    admin_password: str
    admin_name: str


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


class TenantInfo(BaseModel):
    id: str
    name: str
    slug: str
    plan: str


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

@router.post("/register", status_code=status.HTTP_201_CREATED)
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
                agent_id=body.agent_id,
                admin_email=body.admin_email,
                admin_password=body.admin_password,
                admin_name=body.admin_name,
            )
        )
        await session.commit()
        return {
            "access_token": result.access_token,
            "token_type": result.token_type,
            "tenant_id": result.tenant_id,
            "user_id": result.user_id,
            "role": result.role,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequestBody,
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
        # Fetch user and tenant names for the response
        from adapters.outbound.persistence.repositories.pg_user_repository import PgUserRepository
        from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
        from uuid import UUID

        user_repo = PgUserRepository(session)
        tenant_repo = PgTenantRepository(session)

        tenant = await tenant_repo.get_by_id(UUID(result.tenant_id))
        user = await user_repo.get_by_id(UUID(result.user_id))

        if not user or not tenant:
            raise ValueError("Invalid credentials")

        return TokenResponse(
            access_token=result.access_token,
            user=UserInfo(
                id=result.user_id,
                name=user.name,
                email=user.email,
                role=result.role,
            ),
            tenant=TenantInfo(
                id=result.tenant_id,
                name=tenant.name,
                slug=tenant.slug,
                plan=tenant.plan,
            ),
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )


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

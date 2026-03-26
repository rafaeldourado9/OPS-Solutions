import structlog

from core.ports.inbound.auth_service import AuthToken, LoginRequest
from core.ports.outbound.tenant_repository import TenantRepositoryPort
from core.ports.outbound.user_repository import UserRepositoryPort
from infrastructure.security import create_access_token, verify_password

logger = structlog.get_logger()


class LoginUseCase:

    def __init__(
        self,
        tenant_repo: TenantRepositoryPort,
        user_repo: UserRepositoryPort,
    ) -> None:
        self._tenant_repo = tenant_repo
        self._user_repo = user_repo

    async def execute(self, request: LoginRequest) -> AuthToken:
        if request.tenant_slug:
            tenant = await self._tenant_repo.get_by_slug(request.tenant_slug)
            if not tenant:
                raise ValueError("Invalid credentials")
            user = await self._user_repo.get_by_email(tenant.id, request.email)
        else:
            # Find user across all tenants by email
            user = await self._user_repo.get_by_email_global(request.email)
            if not user:
                raise ValueError("Invalid credentials")
            tenant = await self._tenant_repo.get_by_id(user.tenant_id)
            if not tenant:
                raise ValueError("Invalid credentials")

        if not user or not user.is_active:
            raise ValueError("Invalid credentials")

        if not verify_password(request.password, user.password_hash):
            raise ValueError("Invalid credentials")

        logger.info("user_logged_in", user_id=str(user.id), tenant_id=str(tenant.id))

        token = create_access_token(tenant.id, user.id, user.role.value)
        return AuthToken(
            access_token=token,
            tenant_id=str(tenant.id),
            user_id=str(user.id),
            role=user.role.value,
        )

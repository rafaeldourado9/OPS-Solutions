import structlog

from core.domain.tenant import Tenant
from core.domain.user import Role, User
from core.ports.inbound.auth_service import AuthToken, RegisterTenantRequest
from core.ports.outbound.tenant_repository import TenantRepositoryPort
from core.ports.outbound.user_repository import UserRepositoryPort
from infrastructure.security import create_access_token, hash_password

logger = structlog.get_logger()


class RegisterTenantUseCase:

    def __init__(
        self,
        tenant_repo: TenantRepositoryPort,
        user_repo: UserRepositoryPort,
        email_adapter=None,
    ) -> None:
        self._tenant_repo = tenant_repo
        self._user_repo = user_repo
        self._email = email_adapter

    async def execute(self, request: RegisterTenantRequest) -> AuthToken:
        if await self._tenant_repo.exists_by_slug(request.tenant_slug):
            raise ValueError(f"Tenant slug '{request.tenant_slug}' already exists")

        tenant = Tenant.create(
            slug=request.tenant_slug,
            name=request.tenant_name,
            agent_id=request.agent_id,
            owned_agents=[request.agent_id],
        )
        await self._tenant_repo.save(tenant)

        user = User.create(
            tenant_id=tenant.id,
            email=request.admin_email,
            password_hash=hash_password(request.admin_password),
            name=request.admin_name,
            role=Role.ADMIN,
        )
        await self._user_repo.save(user)

        logger.info(
            "tenant_registered",
            tenant_id=str(tenant.id),
            slug=tenant.slug,
            admin_email=user.email,
        )

        # Welcome email — handled in auth_routes after commit

        token = create_access_token(tenant.id, user.id, user.role.value)
        return AuthToken(
            access_token=token,
            tenant_id=str(tenant.id),
            user_id=str(user.id),
            role=user.role.value,
        )

    async def _send_welcome(self, email: str, name: str, tenant_name: str) -> None:
        from adapters.outbound.email.templates import welcome
        from infrastructure.config import settings
        try:
            subject, html = welcome(name, tenant_name, settings.app_url)
            await self._email.send(email, subject, html)
            logger.info("welcome_email_sent", email=email)
        except Exception as exc:
            logger.warning("welcome_email_failed", email=email, error=str(exc))

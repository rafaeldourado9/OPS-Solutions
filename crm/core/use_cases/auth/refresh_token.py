from uuid import UUID

from core.ports.inbound.auth_service import AuthToken
from core.ports.outbound.user_repository import UserRepositoryPort
from infrastructure.security import create_access_token, decode_access_token


class RefreshTokenUseCase:

    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    async def execute(self, token: str) -> AuthToken:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])
        role = payload["role"]

        user = await self._user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("Invalid token")

        new_token = create_access_token(tenant_id, user_id, role)
        return AuthToken(
            access_token=new_token,
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            role=role,
        )

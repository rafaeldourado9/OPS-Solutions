from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RegisterTenantRequest:
    tenant_name: str
    tenant_slug: str
    agent_id: str
    admin_email: str
    admin_password: str
    admin_name: str


@dataclass(frozen=True)
class LoginRequest:
    email: str
    password: str
    tenant_slug: str = ""


@dataclass(frozen=True)
class AuthToken:
    access_token: str
    token_type: str = "bearer"
    tenant_id: str = ""
    user_id: str = ""
    role: str = ""


class AuthServicePort(ABC):

    @abstractmethod
    async def register_tenant(self, request: RegisterTenantRequest) -> AuthToken: ...

    @abstractmethod
    async def login(self, request: LoginRequest) -> AuthToken: ...

    @abstractmethod
    async def refresh_token(self, token: str) -> AuthToken: ...

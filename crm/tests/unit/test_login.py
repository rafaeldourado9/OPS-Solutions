import pytest

from core.domain.tenant import Tenant
from core.domain.user import Role, User
from core.ports.inbound.auth_service import LoginRequest
from core.use_cases.auth.login import LoginUseCase
from infrastructure.security import decode_access_token, hash_password


@pytest.fixture
async def seeded_repos(tenant_repo, user_repo):
    tenant = Tenant.create(slug="acme", name="Acme", agent_id="acme_agent")
    await tenant_repo.save(tenant)

    user = User.create(
        tenant_id=tenant.id,
        email="admin@acme.com",
        password_hash=hash_password("Senha123!"),
        name="Admin",
        role=Role.ADMIN,
    )
    await user_repo.save(user)

    return tenant, user


@pytest.fixture
def use_case(tenant_repo, user_repo):
    return LoginUseCase(tenant_repo, user_repo)


async def test_login_with_valid_credentials(use_case, seeded_repos):
    tenant, user = seeded_repos
    result = await use_case.execute(
        LoginRequest(email="admin@acme.com", password="Senha123!", tenant_slug="acme")
    )

    assert result.access_token
    assert result.tenant_id == str(tenant.id)
    assert result.user_id == str(user.id)
    assert result.role == "admin"

    payload = decode_access_token(result.access_token)
    assert payload["sub"] == str(user.id)


async def test_login_with_wrong_password(use_case, seeded_repos):
    with pytest.raises(ValueError, match="Invalid credentials"):
        await use_case.execute(
            LoginRequest(email="admin@acme.com", password="wrong", tenant_slug="acme")
        )


async def test_login_with_wrong_email(use_case, seeded_repos):
    with pytest.raises(ValueError, match="Invalid credentials"):
        await use_case.execute(
            LoginRequest(email="nope@acme.com", password="Senha123!", tenant_slug="acme")
        )


async def test_login_with_wrong_tenant(use_case, seeded_repos):
    with pytest.raises(ValueError, match="Invalid credentials"):
        await use_case.execute(
            LoginRequest(email="admin@acme.com", password="Senha123!", tenant_slug="nope")
        )

import pytest

from core.ports.inbound.auth_service import RegisterTenantRequest
from core.use_cases.auth.register_tenant import RegisterTenantUseCase
from infrastructure.security import decode_access_token


@pytest.fixture
def use_case(tenant_repo, user_repo):
    return RegisterTenantUseCase(tenant_repo, user_repo)


@pytest.fixture
def valid_request():
    return RegisterTenantRequest(
        tenant_name="Acme Corp",
        tenant_slug="acme",
        agent_id="acme_agent",
        admin_email="admin@acme.com",
        admin_password="Senha123!",
        admin_name="Admin",
    )


async def test_register_tenant_creates_tenant_and_user(use_case, valid_request, tenant_repo, user_repo):
    result = await use_case.execute(valid_request)

    assert result.access_token
    assert result.token_type == "bearer"
    assert result.role == "admin"

    # Tenant was saved
    tenant = await tenant_repo.get_by_slug("acme")
    assert tenant is not None
    assert tenant.name == "Acme Corp"
    assert tenant.agent_id == "acme_agent"

    # User was saved
    user = await user_repo.get_by_email(tenant.id, "admin@acme.com")
    assert user is not None
    assert user.name == "Admin"
    assert user.role.value == "admin"


async def test_register_tenant_returns_valid_jwt(use_case, valid_request):
    result = await use_case.execute(valid_request)

    payload = decode_access_token(result.access_token)
    assert payload["tenant_id"] == result.tenant_id
    assert payload["sub"] == result.user_id
    assert payload["role"] == "admin"


async def test_register_tenant_rejects_duplicate_slug(use_case, valid_request):
    await use_case.execute(valid_request)

    with pytest.raises(ValueError, match="already exists"):
        await use_case.execute(valid_request)

import pytest

from core.use_cases.customers.create_customer import CreateCustomerRequest, CreateCustomerUseCase


@pytest.fixture
def use_case(customer_repo):
    return CreateCustomerUseCase(customer_repo)


@pytest.fixture
def valid_request(sample_tenant):
    return CreateCustomerRequest(
        tenant_id=sample_tenant.id,
        name="Joao Silva",
        phone="5511999999999",
        email="joao@email.com",
        source="manual",
    )


async def test_create_customer_success(use_case, valid_request, customer_repo):
    customer = await use_case.execute(valid_request)

    assert customer.name == "Joao Silva"
    assert customer.phone == "5511999999999"
    assert customer.email == "joao@email.com"
    assert customer.source == "manual"
    assert customer.chat_id == "5511999999999"

    saved = await customer_repo.get_by_phone(valid_request.tenant_id, "5511999999999")
    assert saved is not None
    assert saved.id == customer.id


async def test_create_customer_duplicate_phone_raises(use_case, valid_request):
    await use_case.execute(valid_request)

    with pytest.raises(ValueError, match="already exists"):
        await use_case.execute(valid_request)


async def test_create_customer_with_tags(use_case, valid_request, customer_repo):
    valid_request = CreateCustomerRequest(
        tenant_id=valid_request.tenant_id,
        name="Maria",
        phone="5511888888888",
        tags=["vip", "premium"],
    )
    customer = await use_case.execute(valid_request)
    assert customer.tags == ["vip", "premium"]

import pytest

from core.use_cases.agents.get_agent_config import GetAgentConfigUseCase
from core.use_cases.agents.update_agent_config import UpdateAgentConfigRequest, UpdateAgentConfigUseCase


async def test_get_agent_config(tenant_repo, agent_config_port, sample_tenant):
    await tenant_repo.save(sample_tenant)
    uc = GetAgentConfigUseCase(tenant_repo, agent_config_port)
    config = await uc.execute(sample_tenant.id)

    assert config["agent"]["name"] == "Test Agent"
    assert "llm" in config
    assert "memory" in config


async def test_get_agent_config_tenant_not_found(tenant_repo, agent_config_port):
    from uuid import uuid4
    uc = GetAgentConfigUseCase(tenant_repo, agent_config_port)
    with pytest.raises(ValueError, match="Tenant not found"):
        await uc.execute(uuid4())


async def test_get_agent_config_missing_file(tenant_repo, sample_tenant):
    from tests.conftest import FakeAgentConfigPort
    await tenant_repo.save(sample_tenant)
    empty_port = FakeAgentConfigPort({})  # no configs
    uc = GetAgentConfigUseCase(tenant_repo, empty_port)
    with pytest.raises(FileNotFoundError):
        await uc.execute(sample_tenant.id)


async def test_update_agent_config_partial(tenant_repo, agent_config_port, sample_tenant):
    await tenant_repo.save(sample_tenant)
    uc = UpdateAgentConfigUseCase(tenant_repo, agent_config_port)

    updated = await uc.execute(UpdateAgentConfigRequest(
        tenant_id=sample_tenant.id,
        updates={"agent": {"name": "Sofia", "persona": "Consultora simpática"}},
    ))

    assert updated["agent"]["name"] == "Sofia"
    assert updated["agent"]["persona"] == "Consultora simpática"
    # Other fields preserved
    assert updated["agent"]["company"] == "Test Co"
    assert "llm" in updated


async def test_update_nested_config(tenant_repo, agent_config_port, sample_tenant):
    await tenant_repo.save(sample_tenant)
    uc = UpdateAgentConfigUseCase(tenant_repo, agent_config_port)

    updated = await uc.execute(UpdateAgentConfigRequest(
        tenant_id=sample_tenant.id,
        updates={"llm": {"temperature": 0.7, "max_tokens": 600}},
    ))

    assert updated["llm"]["temperature"] == 0.7
    assert updated["llm"]["max_tokens"] == 600
    # Other LLM fields preserved
    assert updated["llm"]["provider"] == "gemini"


async def test_update_config_persisted(tenant_repo, agent_config_port, sample_tenant):
    await tenant_repo.save(sample_tenant)
    uc = UpdateAgentConfigUseCase(tenant_repo, agent_config_port)

    await uc.execute(UpdateAgentConfigRequest(
        tenant_id=sample_tenant.id,
        updates={"agent": {"name": "Carlos"}},
    ))

    # Read back
    get_uc = GetAgentConfigUseCase(tenant_repo, agent_config_port)
    config = await get_uc.execute(sample_tenant.id)
    assert config["agent"]["name"] == "Carlos"

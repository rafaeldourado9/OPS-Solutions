import pytest

from core.use_cases.agents.delete_rag_document import DeleteRagDocumentRequest, DeleteRagDocumentUseCase
from core.use_cases.agents.list_rag_documents import ListRagDocumentsUseCase
from core.use_cases.agents.upload_rag_document import UploadRagDocumentRequest, UploadRagDocumentUseCase


async def test_upload_txt_document(tenant_repo, agent_config_port, rag_port, sample_tenant):
    await tenant_repo.save(sample_tenant)
    uc = UploadRagDocumentUseCase(tenant_repo, agent_config_port, rag_port)

    content = b"Este e o manual de vendas. " * 20  # enough for chunking
    doc = await uc.execute(UploadRagDocumentRequest(
        tenant_id=sample_tenant.id,
        filename="manual_vendas.txt",
        content=content,
        doc_name="Manual de Vendas",
    ))

    assert doc.name == "Manual de Vendas"
    assert doc.chunk_count >= 1
    assert f"{sample_tenant.agent_id}_rules" in doc.collection


async def test_upload_uses_filename_as_name_by_default(
    tenant_repo, agent_config_port, rag_port, sample_tenant
):
    await tenant_repo.save(sample_tenant)
    uc = UploadRagDocumentUseCase(tenant_repo, agent_config_port, rag_port)

    await uc.execute(UploadRagDocumentRequest(
        tenant_id=sample_tenant.id,
        filename="procedimentos_atendimento.txt",
        content=b"Procedimento 1: sempre cumprimentar o cliente. " * 10,
    ))

    list_uc = ListRagDocumentsUseCase(tenant_repo, agent_config_port, rag_port)
    docs = await list_uc.execute(sample_tenant.id)
    names = [d.name for d in docs]
    assert "procedimentos_atendimento" in names


async def test_upload_empty_file_raises(tenant_repo, agent_config_port, rag_port, sample_tenant):
    await tenant_repo.save(sample_tenant)
    uc = UploadRagDocumentUseCase(tenant_repo, agent_config_port, rag_port)

    with pytest.raises(ValueError, match="No text content"):
        await uc.execute(UploadRagDocumentRequest(
            tenant_id=sample_tenant.id,
            filename="empty.txt",
            content=b"   ",  # only whitespace
        ))


async def test_upload_unsupported_type_raises(
    tenant_repo, agent_config_port, rag_port, sample_tenant
):
    await tenant_repo.save(sample_tenant)
    uc = UploadRagDocumentUseCase(tenant_repo, agent_config_port, rag_port)

    with pytest.raises(ValueError, match="Unsupported file type"):
        await uc.execute(UploadRagDocumentRequest(
            tenant_id=sample_tenant.id,
            filename="data.xlsx",
            content=b"some bytes",
        ))


async def test_list_rag_documents(tenant_repo, agent_config_port, rag_port, sample_tenant):
    await tenant_repo.save(sample_tenant)
    upload_uc = UploadRagDocumentUseCase(tenant_repo, agent_config_port, rag_port)

    for name, content in [
        ("Doc A", b"Conteudo A. " * 15),
        ("Doc B", b"Conteudo B. " * 15),
    ]:
        await upload_uc.execute(UploadRagDocumentRequest(
            tenant_id=sample_tenant.id,
            filename="doc.txt",
            content=content,
            doc_name=name,
        ))

    list_uc = ListRagDocumentsUseCase(tenant_repo, agent_config_port, rag_port)
    docs = await list_uc.execute(sample_tenant.id)

    assert len(docs) == 2
    assert {d.name for d in docs} == {"Doc A", "Doc B"}


async def test_delete_rag_document(tenant_repo, agent_config_port, rag_port, sample_tenant):
    await tenant_repo.save(sample_tenant)
    upload_uc = UploadRagDocumentUseCase(tenant_repo, agent_config_port, rag_port)
    await upload_uc.execute(UploadRagDocumentRequest(
        tenant_id=sample_tenant.id,
        filename="to_delete.txt",
        content=b"Conteudo para deletar. " * 10,
        doc_name="Para Deletar",
    ))

    delete_uc = DeleteRagDocumentUseCase(tenant_repo, agent_config_port, rag_port)
    deleted = await delete_uc.execute(DeleteRagDocumentRequest(
        tenant_id=sample_tenant.id,
        doc_name="Para Deletar",
    ))
    assert deleted >= 1

    list_uc = ListRagDocumentsUseCase(tenant_repo, agent_config_port, rag_port)
    docs = await list_uc.execute(sample_tenant.id)
    assert all(d.name != "Para Deletar" for d in docs)


async def test_delete_nonexistent_document_raises(
    tenant_repo, agent_config_port, rag_port, sample_tenant
):
    await tenant_repo.save(sample_tenant)
    delete_uc = DeleteRagDocumentUseCase(tenant_repo, agent_config_port, rag_port)
    with pytest.raises(ValueError, match="not found"):
        await delete_uc.execute(DeleteRagDocumentRequest(
            tenant_id=sample_tenant.id,
            doc_name="inexistente",
        ))

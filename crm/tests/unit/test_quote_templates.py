import pytest

from core.domain.quote import Quote, QuoteItem
from core.use_cases.quotes.delete_quote_template import DeleteQuoteTemplateUseCase
from core.use_cases.quotes.generate_quote_document import GenerateQuoteDocumentRequest, GenerateQuoteDocumentUseCase
from core.use_cases.quotes.list_quote_templates import ListQuoteTemplatesUseCase
from core.use_cases.quotes.upload_quote_template import UploadQuoteTemplateRequest, UploadQuoteTemplateUseCase


def _make_upload_uc(quote_template_repo, storage, docx_engine):
    return UploadQuoteTemplateUseCase(quote_template_repo, storage, docx_engine)


def _make_generate_uc(quote_repo, quote_template_repo, storage, docx_engine, pdf_exporter):
    return GenerateQuoteDocumentUseCase(
        quote_repo=quote_repo,
        template_repo=quote_template_repo,
        storage=storage,
        docx_engine=docx_engine,
        pdf_exporter=pdf_exporter,
    )


async def test_upload_template_extracts_placeholders(
    quote_template_repo, storage, docx_engine, sample_tenant
):
    # Create fake DOCX content with placeholders
    fake_docx = b"Hello {nome_cliente}, total: {total}, date: {data_atual}"

    uc = _make_upload_uc(quote_template_repo, storage, docx_engine)
    template = await uc.execute(UploadQuoteTemplateRequest(
        tenant_id=sample_tenant.id,
        name="Proposta Padrao",
        docx_bytes=fake_docx,
        description="Template basico",
    ))

    assert template.name == "Proposta Padrao"
    assert "nome_cliente" in template.placeholders
    assert "total" in template.placeholders
    assert "data_atual" in template.placeholders
    assert template.tenant_id == sample_tenant.id

    # File should be stored
    stored = await storage.download(template.file_key)
    assert stored == fake_docx


async def test_upload_stores_file_with_unique_key(
    quote_template_repo, storage, docx_engine, sample_tenant
):
    fake_docx = b"Content A {x}"
    uc = _make_upload_uc(quote_template_repo, storage, docx_engine)

    t1 = await uc.execute(UploadQuoteTemplateRequest(
        tenant_id=sample_tenant.id, name="T1", docx_bytes=fake_docx
    ))
    t2 = await uc.execute(UploadQuoteTemplateRequest(
        tenant_id=sample_tenant.id, name="T2", docx_bytes=fake_docx
    ))

    assert t1.file_key != t2.file_key


async def test_list_templates(quote_template_repo, storage, docx_engine, sample_tenant):
    uc = _make_upload_uc(quote_template_repo, storage, docx_engine)
    await uc.execute(UploadQuoteTemplateRequest(
        tenant_id=sample_tenant.id, name="Orcamento A", docx_bytes=b"A {x}"
    ))
    await uc.execute(UploadQuoteTemplateRequest(
        tenant_id=sample_tenant.id, name="Orcamento B", docx_bytes=b"B {y}"
    ))

    list_uc = ListQuoteTemplatesUseCase(quote_template_repo)
    templates = await list_uc.execute(sample_tenant.id)

    assert len(templates) == 2
    assert templates[0].name == "Orcamento A"


async def test_delete_template_removes_from_storage(
    quote_template_repo, storage, docx_engine, sample_tenant
):
    uc = _make_upload_uc(quote_template_repo, storage, docx_engine)
    template = await uc.execute(UploadQuoteTemplateRequest(
        tenant_id=sample_tenant.id, name="Para deletar", docx_bytes=b"content {x}"
    ))
    file_key = template.file_key

    delete_uc = DeleteQuoteTemplateUseCase(quote_template_repo, storage)
    await delete_uc.execute(sample_tenant.id, template.id)

    assert file_key not in storage._store
    found = await quote_template_repo.get_by_id(sample_tenant.id, template.id)
    assert found is None


async def test_delete_template_not_found(quote_template_repo, storage, sample_tenant):
    from uuid import uuid4
    delete_uc = DeleteQuoteTemplateUseCase(quote_template_repo, storage)
    with pytest.raises(ValueError, match="not found"):
        await delete_uc.execute(sample_tenant.id, uuid4())


async def test_generate_document_fills_placeholders(
    quote_repo, quote_template_repo, storage, docx_engine, pdf_exporter, sample_tenant
):
    # Prepare quote
    quote = Quote.create(tenant_id=sample_tenant.id, title="Servico Eletrico")
    item = QuoteItem.create(quote_id=quote.id, description="Cabo", quantity=10.0, unit_price=50.0)
    quote.items.append(item)
    await quote_repo.save(quote)

    # Prepare template
    fake_docx = b"Cliente: {titulo}, Total: {total}, Data: {data_atual}"
    upload_uc = _make_upload_uc(quote_template_repo, storage, docx_engine)
    template = await upload_uc.execute(UploadQuoteTemplateRequest(
        tenant_id=sample_tenant.id, name="T", docx_bytes=fake_docx
    ))

    generate_uc = _make_generate_uc(quote_repo, quote_template_repo, storage, docx_engine, pdf_exporter)
    doc = await generate_uc.execute(GenerateQuoteDocumentRequest(
        tenant_id=sample_tenant.id,
        quote_id=quote.id,
        template_id=template.id,
    ))

    assert doc.pdf_url.startswith("http://fake-storage/")
    assert doc.docx_url.startswith("http://fake-storage/")

    # Verify filled DOCX stored
    filled_bytes = await storage.download(doc.docx_key)
    filled_text = filled_bytes.decode("utf-8", errors="ignore")
    assert "Servico Eletrico" in filled_text
    assert "R$" in filled_text

    # Verify PDF stored
    pdf_bytes = await storage.download(doc.pdf_key)
    assert pdf_bytes == b"%PDF-1.4 fake-pdf-content"


async def test_generate_document_quote_not_found(
    quote_repo, quote_template_repo, storage, docx_engine, pdf_exporter, sample_tenant
):
    from uuid import uuid4
    generate_uc = _make_generate_uc(quote_repo, quote_template_repo, storage, docx_engine, pdf_exporter)
    with pytest.raises(ValueError, match="Quote not found"):
        await generate_uc.execute(GenerateQuoteDocumentRequest(
            tenant_id=sample_tenant.id,
            quote_id=uuid4(),
            template_id=uuid4(),
        ))


async def test_generate_document_extra_context(
    quote_repo, quote_template_repo, storage, docx_engine, pdf_exporter, sample_tenant
):
    quote = Quote.create(tenant_id=sample_tenant.id, title="Q")
    await quote_repo.save(quote)

    fake_docx = b"Nome: {nome_cliente}, Endereco: {endereco}"
    upload_uc = _make_upload_uc(quote_template_repo, storage, docx_engine)
    template = await upload_uc.execute(UploadQuoteTemplateRequest(
        tenant_id=sample_tenant.id, name="T", docx_bytes=fake_docx
    ))

    generate_uc = _make_generate_uc(quote_repo, quote_template_repo, storage, docx_engine, pdf_exporter)
    await generate_uc.execute(GenerateQuoteDocumentRequest(
        tenant_id=sample_tenant.id,
        quote_id=quote.id,
        template_id=template.id,
        extra_context={"nome_cliente": "Joao Silva", "endereco": "Rua das Flores, 123"},
    ))

    filled = (await storage.download(f"generated/{sample_tenant.id}/{quote.id}.docx")).decode()
    assert "Joao Silva" in filled
    assert "Rua das Flores, 123" in filled

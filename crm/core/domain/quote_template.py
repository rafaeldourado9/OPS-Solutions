from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

# CRM fields available for placeholder auto-mapping.
# key → human label shown in the UI.
KNOWN_CRM_FIELDS: dict[str, str] = {
    # Quote fields
    "titulo": "Título do Orçamento",
    "status": "Status",
    "total": "Total (R$)",
    "itens_total": "Total dos Itens (R$)",
    "premissas_total": "Total das Premissas (R$)",
    "moeda": "Moeda",
    "validade": "Data de Validade",
    "notas": "Observações",
    "data_criacao": "Data de Criação",
    "data_atual": "Data Atual",
    # Customer fields
    "nome_cliente": "Nome do Cliente",
    "telefone_cliente": "Telefone do Cliente",
    "email_cliente": "E-mail do Cliente",
    "cidade_cliente": "Cidade do Cliente",
    "estado_cliente": "Estado do Cliente",
    "endereco_cliente": "Endereço do Cliente",
    # Special
    "__manual__": "Valor Manual (digitado na geração)",
}


@dataclass
class QuoteTemplate:
    id: UUID
    tenant_id: UUID
    name: str
    description: str
    file_key: str            # MinIO object key for the DOCX
    placeholders: list[str]  # detected at upload time
    # Maps placeholder key → CRM field name (or "__manual__")
    field_mapping: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        tenant_id: UUID,
        name: str,
        file_key: str,
        placeholders: list[str],
        description: str = "",
        field_mapping: dict[str, str] | None = None,
    ) -> QuoteTemplate:
        now = datetime.utcnow()
        return QuoteTemplate(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            file_key=file_key,
            placeholders=placeholders,
            field_mapping=field_mapping or {},
            created_at=now,
            updated_at=now,
        )

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class QuoteTemplate:
    id: UUID
    tenant_id: UUID
    name: str
    description: str
    file_key: str           # MinIO object key for the DOCX
    placeholders: list[str] # detected at upload time
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        tenant_id: UUID,
        name: str,
        file_key: str,
        placeholders: list[str],
        description: str = "",
    ) -> QuoteTemplate:
        now = datetime.utcnow()
        return QuoteTemplate(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            file_key=file_key,
            placeholders=placeholders,
            created_at=now,
            updated_at=now,
        )

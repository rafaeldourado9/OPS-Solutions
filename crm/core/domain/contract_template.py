from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ContractTemplate:
    id: UUID
    tenant_id: UUID
    name: str
    description: str
    file_key: str
    variables: list[str]
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(
        tenant_id: UUID,
        name: str,
        description: str,
        file_key: str,
        variables: list[str],
    ) -> ContractTemplate:
        now = datetime.utcnow()
        return ContractTemplate(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            file_key=file_key,
            variables=variables,
            created_at=now,
            updated_at=now,
        )

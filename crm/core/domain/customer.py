from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Address:
    street: str = ""
    number: str = ""
    complement: str = ""
    neighborhood: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""


@dataclass
class Customer:
    id: UUID
    tenant_id: UUID
    name: str
    phone: str
    email: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[Address] = None
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    source: str = "manual"
    chat_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        tenant_id: UUID,
        name: str,
        phone: str,
        source: str = "manual",
        chat_id: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Customer:
        now = datetime.utcnow()
        return Customer(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            phone=phone,
            source=source,
            chat_id=chat_id or phone,
            email=email,
            created_at=now,
            updated_at=now,
        )

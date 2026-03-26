from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"


@dataclass
class User:
    id: UUID
    tenant_id: UUID
    email: str
    password_hash: str
    name: str
    role: Role = Role.OPERATOR
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())

    @staticmethod
    def create(
        tenant_id: UUID,
        email: str,
        password_hash: str,
        name: str,
        role: Role = Role.ADMIN,
    ) -> User:
        return User(
            id=uuid4(),
            tenant_id=tenant_id,
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
        )

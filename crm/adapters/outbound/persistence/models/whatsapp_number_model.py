from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from adapters.outbound.persistence.database import Base


class WhatsAppNumberModel(Base):
    __tablename__ = "crm_whatsapp_numbers"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    session_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    connected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

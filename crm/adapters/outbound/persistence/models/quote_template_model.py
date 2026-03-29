from datetime import datetime
from uuid import uuid4

from sqlalchemy import ARRAY, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from adapters.outbound.persistence.database import Base


class QuoteTemplateModel(Base):
    __tablename__ = "crm_quote_templates"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)
    placeholders: Mapped[list] = mapped_column(ARRAY(String), default=list)
    field_mapping: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

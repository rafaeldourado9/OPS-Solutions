from datetime import datetime
from uuid import uuid4

from sqlalchemy import ARRAY, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from adapters.outbound.persistence.database import Base


class LeadModel(Base):
    __tablename__ = "crm_leads"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    customer_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), default="new")
    value: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="BRL")
    source: Mapped[str] = mapped_column(String(100), default="")
    assigned_to: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    expected_close_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lost_reason: Mapped[str] = mapped_column(String(500), default="")
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_inactivity_email_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from adapters.outbound.persistence.database import Base


class QuoteModel(Base):
    __tablename__ = "crm_quotes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    customer_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    lead_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    notes: Mapped[str] = mapped_column(Text, default="")
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="BRL")
    sale_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Store items and applied_premises as JSON for simplicity
    items_json: Mapped[dict] = mapped_column(JSON, default=list)
    applied_premises_json: Mapped[dict] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text  # noqa: F401 – String used in mp fields
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from adapters.outbound.persistence.database import Base


class TenantModel(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_color: Mapped[str] = mapped_column(String(7), default="#1a73e8")
    secondary_color: Mapped[str] = mapped_column(String(7), default="#ffffff")
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    gateway_session: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    gateway_url: Mapped[str] = mapped_column(Text, nullable=False, default="http://gateway:3000")
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="starter")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    mp_subscription_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    mp_payer_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    subscription_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

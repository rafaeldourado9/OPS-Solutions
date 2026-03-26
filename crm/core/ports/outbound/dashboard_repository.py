from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class KPIData:
    total_customers: int
    new_customers: int
    total_leads: int
    open_leads: int
    won_leads: int
    lost_leads: int
    win_rate: float  # 0.0 - 1.0
    total_revenue: float
    pipeline_value: float
    active_conversations: int
    takeover_active: int
    low_stock_products: int


@dataclass
class SalesFunnelStage:
    stage: str
    count: int
    total_value: float


@dataclass
class RevenueDataPoint:
    period: str  # "2025-01"
    revenue: float
    new_customers: int
    new_leads: int


@dataclass
class ConversationMetrics:
    total_conversations: int
    active_conversations: int
    waiting_conversations: int
    closed_conversations: int
    takeover_sessions_period: int
    avg_messages_per_conversation: float


@dataclass
class InventoryAlert:
    product_id: str
    product_name: str
    sku: str
    stock_quantity: float
    min_stock_alert: float


class DashboardRepositoryPort(ABC):

    @abstractmethod
    async def get_kpis(self, tenant_id: UUID, since: datetime) -> KPIData:
        ...

    @abstractmethod
    async def get_sales_funnel(self, tenant_id: UUID) -> list[SalesFunnelStage]:
        ...

    @abstractmethod
    async def get_revenue_chart(self, tenant_id: UUID, months: int) -> list[RevenueDataPoint]:
        ...

    @abstractmethod
    async def get_conversation_metrics(self, tenant_id: UUID, since: datetime) -> ConversationMetrics:
        ...

    @abstractmethod
    async def get_inventory_alerts(self, tenant_id: UUID) -> list[InventoryAlert]:
        ...

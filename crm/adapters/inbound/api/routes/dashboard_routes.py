from fastapi import APIRouter, Depends, Query

from adapters.inbound.api.dependencies import (
    get_conversation_metrics_uc,
    get_inventory_alerts_uc,
    get_kpis_uc,
    get_revenue_chart_uc,
    get_sales_funnel_uc,
)
from adapters.inbound.api.middleware.auth import CurrentUser, get_current_user
from core.ports.outbound.dashboard_repository import (
    ConversationMetrics,
    InventoryAlert,
    KPIData,
    RevenueDataPoint,
    SalesFunnelStage,
)
from core.use_cases.dashboard.get_conversation_metrics import (
    GetConversationMetricsRequest,
    GetConversationMetricsUseCase,
)
from core.use_cases.dashboard.get_inventory_alerts import GetInventoryAlertsRequest, GetInventoryAlertsUseCase
from core.use_cases.dashboard.get_kpis import GetKPIsRequest, GetKPIsUseCase
from core.use_cases.dashboard.get_revenue_chart import GetRevenueChartRequest, GetRevenueChartUseCase
from core.use_cases.dashboard.get_sales_funnel import GetSalesFunnelRequest, GetSalesFunnelUseCase
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


# --- Response Schemas ---

class KPIOut(BaseModel):
    total_customers: int
    new_customers: int
    total_leads: int
    open_leads: int
    won_leads: int
    lost_leads: int
    win_rate: float
    total_revenue: float
    pipeline_value: float
    active_conversations: int
    takeover_active: int
    low_stock_products: int


class SalesFunnelStageOut(BaseModel):
    stage: str
    count: int
    total_value: float


class RevenueDataPointOut(BaseModel):
    period: str
    revenue: float
    new_customers: int
    new_leads: int


class ConversationMetricsOut(BaseModel):
    total_conversations: int
    active_conversations: int
    waiting_conversations: int
    closed_conversations: int
    takeover_sessions_period: int
    avg_messages_per_conversation: float


class InventoryAlertOut(BaseModel):
    product_id: str
    product_name: str
    sku: str
    stock_quantity: float
    min_stock_alert: float


# --- Routes ---

@router.get("/kpis", response_model=KPIOut)
async def get_kpis(
    days: int = Query(30, ge=1, le=365, description="Lookback period in days"),
    current_user: CurrentUser = Depends(get_current_user),
    uc: GetKPIsUseCase = Depends(get_kpis_uc),
):
    data = await uc.execute(GetKPIsRequest(tenant_id=current_user.tenant_id, days=days))
    return KPIOut(**data.__dict__)


@router.get("/sales-funnel", response_model=list[SalesFunnelStageOut])
async def get_sales_funnel(
    current_user: CurrentUser = Depends(get_current_user),
    uc: GetSalesFunnelUseCase = Depends(get_sales_funnel_uc),
):
    stages = await uc.execute(GetSalesFunnelRequest(tenant_id=current_user.tenant_id))
    return [SalesFunnelStageOut(**s.__dict__) for s in stages]


@router.get("/revenue-chart", response_model=list[RevenueDataPointOut])
async def get_revenue_chart(
    months: int = Query(6, ge=1, le=24, description="Number of months to include"),
    current_user: CurrentUser = Depends(get_current_user),
    uc: GetRevenueChartUseCase = Depends(get_revenue_chart_uc),
):
    points = await uc.execute(GetRevenueChartRequest(tenant_id=current_user.tenant_id, months=months))
    return [RevenueDataPointOut(**p.__dict__) for p in points]


@router.get("/conversation-metrics", response_model=ConversationMetricsOut)
async def get_conversation_metrics(
    days: int = Query(30, ge=1, le=365, description="Lookback period in days"),
    current_user: CurrentUser = Depends(get_current_user),
    uc: GetConversationMetricsUseCase = Depends(get_conversation_metrics_uc),
):
    data = await uc.execute(GetConversationMetricsRequest(tenant_id=current_user.tenant_id, days=days))
    return ConversationMetricsOut(**data.__dict__)


@router.get("/inventory-alerts", response_model=list[InventoryAlertOut])
async def get_inventory_alerts(
    current_user: CurrentUser = Depends(get_current_user),
    uc: GetInventoryAlertsUseCase = Depends(get_inventory_alerts_uc),
):
    alerts = await uc.execute(GetInventoryAlertsRequest(tenant_id=current_user.tenant_id))
    return [InventoryAlertOut(**a.__dict__) for a in alerts]

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.models.conversation_model import ConversationModel
from adapters.outbound.persistence.models.customer_model import CustomerModel
from adapters.outbound.persistence.models.lead_model import LeadModel
from adapters.outbound.persistence.models.message_model import CRMMessageModel
from core.ports.outbound.dashboard_repository import (
    ConversationMetrics,
    DashboardRepositoryPort,
    KPIData,
    RevenueDataPoint,
    SalesFunnelStage,
)


class PgDashboardRepository(DashboardRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # KPIs
    # ------------------------------------------------------------------

    async def get_kpis(self, tenant_id: UUID, since: datetime) -> KPIData:
        tid = str(tenant_id)

        # Customers
        total_customers = await self._scalar(
            select(func.count()).where(CustomerModel.tenant_id == tenant_id)
        )
        new_customers = await self._scalar(
            select(func.count()).where(
                CustomerModel.tenant_id == tenant_id,
                CustomerModel.created_at >= since,
            )
        )

        # Leads
        total_leads = await self._scalar(
            select(func.count()).where(LeadModel.tenant_id == tenant_id)
        )
        open_stages = ("new", "contacted", "qualified", "proposal", "negotiation")
        open_leads = await self._scalar(
            select(func.count()).where(
                LeadModel.tenant_id == tenant_id,
                LeadModel.stage.in_(open_stages),
            )
        )
        won_leads = await self._scalar(
            select(func.count()).where(
                LeadModel.tenant_id == tenant_id,
                LeadModel.stage == "won",
                LeadModel.closed_at >= since,
            )
        )
        lost_leads = await self._scalar(
            select(func.count()).where(
                LeadModel.tenant_id == tenant_id,
                LeadModel.stage == "lost",
                LeadModel.closed_at >= since,
            )
        )
        closed_total = won_leads + lost_leads
        win_rate = won_leads / closed_total if closed_total > 0 else 0.0

        # Pipeline value (open leads)
        pipeline_result = await self._session.execute(
            select(func.coalesce(func.sum(LeadModel.value), 0.0)).where(
                LeadModel.tenant_id == tenant_id,
                LeadModel.stage.in_(open_stages),
            )
        )
        pipeline_value = pipeline_result.scalar() or 0.0

        # Revenue from won leads in period
        revenue_result = await self._session.execute(
            select(func.coalesce(func.sum(LeadModel.value), 0.0)).where(
                LeadModel.tenant_id == tenant_id,
                LeadModel.stage == "won",
                LeadModel.closed_at >= since,
            )
        )
        total_revenue = float(revenue_result.scalar() or 0.0)

        # Conversations
        active_conversations = await self._scalar(
            select(func.count()).where(
                ConversationModel.tenant_id == tenant_id,
                ConversationModel.status == "active",
            )
        )
        takeover_active = await self._scalar(
            select(func.count()).where(
                ConversationModel.tenant_id == tenant_id,
                ConversationModel.is_takeover_active == True,
            )
        )

        return KPIData(
            total_customers=total_customers,
            new_customers=new_customers,
            total_leads=total_leads,
            open_leads=open_leads,
            won_leads=won_leads,
            lost_leads=lost_leads,
            win_rate=round(win_rate, 4),
            total_revenue=round(total_revenue, 2),
            pipeline_value=round(float(pipeline_value), 2),
            active_conversations=active_conversations,
            takeover_active=takeover_active,
        )

    # ------------------------------------------------------------------
    # Sales Funnel
    # ------------------------------------------------------------------

    async def get_sales_funnel(self, tenant_id: UUID) -> list[SalesFunnelStage]:
        result = await self._session.execute(
            select(
                LeadModel.stage,
                func.count().label("cnt"),
                func.coalesce(func.sum(LeadModel.value), 0.0).label("total_value"),
            )
            .where(LeadModel.tenant_id == tenant_id)
            .group_by(LeadModel.stage)
        )
        stage_order = ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]
        rows = {row.stage: row for row in result}
        return [
            SalesFunnelStage(
                stage=stage,
                count=rows[stage].cnt if stage in rows else 0,
                total_value=round(float(rows[stage].total_value), 2) if stage in rows else 0.0,
            )
            for stage in stage_order
        ]

    # ------------------------------------------------------------------
    # Revenue Chart
    # ------------------------------------------------------------------

    async def get_revenue_chart(self, tenant_id: UUID, months: int) -> list[RevenueDataPoint]:
        # Generate monthly buckets via SQL for the last N months
        stmt = text(
            """
            SELECT
                TO_CHAR(gs.month, 'YYYY-MM') AS period,
                gs.month AS month_start,
                (gs.month + INTERVAL '1 month') AS month_end
            FROM generate_series(
                DATE_TRUNC('month', NOW() AT TIME ZONE 'UTC' - ((:months - 1) || ' months')::INTERVAL),
                DATE_TRUNC('month', NOW() AT TIME ZONE 'UTC'),
                INTERVAL '1 month'
            ) AS gs(month)
            ORDER BY gs.month
            """
        )
        months_result = await self._session.execute(stmt, {"months": months})
        buckets = months_result.fetchall()

        data_points: list[RevenueDataPoint] = []
        for row in buckets:
            period = row.period
            month_start = row.month_start
            month_end = row.month_end

            # Revenue: won leads closed in this month
            revenue_result = await self._session.execute(
                select(func.coalesce(func.sum(LeadModel.value), 0.0)).where(
                    LeadModel.tenant_id == tenant_id,
                    LeadModel.stage == "won",
                    LeadModel.closed_at >= month_start,
                    LeadModel.closed_at < month_end,
                )
            )
            revenue = float(revenue_result.scalar() or 0.0)

            # New customers
            new_customers = await self._scalar(
                select(func.count()).where(
                    CustomerModel.tenant_id == tenant_id,
                    CustomerModel.created_at >= month_start,
                    CustomerModel.created_at < month_end,
                )
            )

            # New leads
            new_leads = await self._scalar(
                select(func.count()).where(
                    LeadModel.tenant_id == tenant_id,
                    LeadModel.created_at >= month_start,
                    LeadModel.created_at < month_end,
                )
            )

            data_points.append(RevenueDataPoint(
                period=period,
                revenue=round(revenue, 2),
                new_customers=new_customers,
                new_leads=new_leads,
            ))

        return data_points

    # ------------------------------------------------------------------
    # Conversation Metrics
    # ------------------------------------------------------------------

    async def get_conversation_metrics(self, tenant_id: UUID, since: datetime) -> ConversationMetrics:
        total = await self._scalar(
            select(func.count()).where(ConversationModel.tenant_id == tenant_id)
        )
        active = await self._scalar(
            select(func.count()).where(
                ConversationModel.tenant_id == tenant_id,
                ConversationModel.status == "active",
            )
        )
        waiting = await self._scalar(
            select(func.count()).where(
                ConversationModel.tenant_id == tenant_id,
                ConversationModel.status == "waiting",
            )
        )
        closed = await self._scalar(
            select(func.count()).where(
                ConversationModel.tenant_id == tenant_id,
                ConversationModel.status == "closed",
            )
        )

        # Takeover sessions in period: count conversations with operator messages since `since`
        takeover_sessions = await self._scalar(
            select(func.count(func.distinct(CRMMessageModel.conversation_id))).where(
                CRMMessageModel.tenant_id == tenant_id,
                CRMMessageModel.role == "operator",
                CRMMessageModel.created_at >= since,
            )
        )

        # Avg messages per conversation
        total_messages = await self._scalar(
            select(func.count()).where(CRMMessageModel.tenant_id == tenant_id)
        )
        avg_messages = round(total_messages / total, 2) if total > 0 else 0.0

        return ConversationMetrics(
            total_conversations=total,
            active_conversations=active,
            waiting_conversations=waiting,
            closed_conversations=closed,
            takeover_sessions_period=takeover_sessions,
            avg_messages_per_conversation=avg_messages,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _scalar(self, stmt) -> int:
        result = await self._session.execute(stmt)
        return result.scalar() or 0

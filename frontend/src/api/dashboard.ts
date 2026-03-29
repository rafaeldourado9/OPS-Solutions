import { api } from './client'

// ── Types matching backend exactly ──────────────────────────────────────────

export interface KPIs {
  total_customers: number
  new_customers: number
  total_leads: number
  open_leads: number
  won_leads: number
  lost_leads: number
  win_rate: number
  total_revenue: number
  pipeline_value: number
  active_conversations: number
  takeover_active: number
  low_stock_products: number
}

export interface SalesFunnelItem {
  stage: string
  label: string
  count: number
  total_value: number
}

export interface RevenuePoint {
  period: string   // YYYY-MM
  month: string    // short label, e.g. "Mar"
  revenue: number
  new_customers: number
  new_leads: number
}

export interface ConversationMetrics {
  total_conversations: number
  active_conversations: number
  waiting_conversations: number
  closed_conversations: number
  takeover_sessions_period: number
  avg_messages_per_conversation: number
}

export interface InventoryAlert {
  product_id: string
  product_name: string
  sku: string
  stock_quantity: number
  min_stock_alert: number
}

// ── Mappers ──────────────────────────────────────────────────────────────────

const STAGE_LABELS: Record<string, string> = {
  new: 'Novos',
  contacted: 'Contatados',
  qualified: 'Qualificados',
  proposal: 'Proposta',
  negotiation: 'Negociação',
  won: 'Ganhos',
  lost: 'Perdidos',
}

const MONTH_LABELS_PT = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

function mapFunnelItem(s: any): SalesFunnelItem {
  return {
    stage: s.stage,
    label: STAGE_LABELS[s.stage] ?? s.stage,
    count: s.count ?? 0,
    total_value: s.total_value ?? 0,
  }
}

function mapRevenuePoint(p: any): RevenuePoint {
  // period is "YYYY-MM"
  const month = p.period ? MONTH_LABELS_PT[parseInt(p.period.slice(5, 7), 10) - 1] ?? p.period : ''
  return {
    period: p.period,
    month,
    revenue: p.revenue ?? 0,
    new_customers: p.new_customers ?? 0,
    new_leads: p.new_leads ?? 0,
  }
}

// ── API ──────────────────────────────────────────────────────────────────────

export const dashboardApi = {
  getKpis: () =>
    api.get<KPIs>('/api/v1/dashboard/kpis').then((r: any) => r.data as KPIs),

  getSalesFunnel: () =>
    api.get<any[]>('/api/v1/dashboard/sales-funnel')
      .then((r: any) => (r.data as any[]).map(mapFunnelItem)),

  getRevenueChart: () =>
    api.get<any[]>('/api/v1/dashboard/revenue-chart')
      .then((r: any) => (r.data as any[]).map(mapRevenuePoint)),

  getConvMetrics: () =>
    api.get<ConversationMetrics>('/api/v1/dashboard/conversation-metrics')
      .then((r: any) => r.data as ConversationMetrics),

  getInventoryAlerts: () =>
    api.get<InventoryAlert[]>('/api/v1/dashboard/inventory-alerts')
      .then((r: any) => r.data as InventoryAlert[]),
}

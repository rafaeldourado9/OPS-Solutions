import { api } from './client'

export interface KPIs {
  total_customers: number
  active_leads: number
  monthly_revenue: number
  conversion_rate: number
  active_conversations: number
  uptime_percent: number
}

export interface SalesFunnelItem {
  stage: string
  label: string
  count: number
  value: number
}

export interface RevenuePoint {
  month: string
  revenue: number
  target: number
}

export interface ConversationMetrics {
  messages_sent: number
  takeovers: number
  avg_response_seconds: number
}

export interface InventoryAlert {
  id: string
  name: string
  sku: string
  stock: number
  min_stock: number
}

export const dashboardApi = {
  getKpis: () => api.get<KPIs>('/api/v1/dashboard/kpis').then((r: any) => r.data),
  getSalesFunnel: () => api.get<SalesFunnelItem[]>('/api/v1/dashboard/sales-funnel').then((r: any) => r.data),
  getRevenueChart: () => api.get<RevenuePoint[]>('/api/v1/dashboard/revenue-chart').then((r: any) => r.data),
  getConvMetrics: () => api.get<ConversationMetrics>('/api/v1/dashboard/conversation-metrics').then((r: any) => r.data),
  getInventoryAlerts: () => api.get<InventoryAlert[]>('/api/v1/dashboard/inventory-alerts').then((r: any) => r.data),
}

import { api } from './client'

export type QuoteStatus = 'draft' | 'sent' | 'approved' | 'rejected' | 'expired'
export type Currency = 'BRL' | 'USD' | 'EUR'

export interface QuoteItem {
  id?: string
  description: string
  quantity: number
  unit_price: number
  discount_percent: number
  total: number
}

export interface AppliedPremise {
  premise_id: string
  name: string
  type: 'percent' | 'fixed'
  value: number
  calculated_amount: number
}

export interface Quote {
  id: string
  tenant_id: string
  title: string
  customer_id: string
  customer_name?: string
  lead_id?: string
  status: QuoteStatus
  currency: Currency
  items: QuoteItem[]
  applied_premises: AppliedPremise[]
  subtotal: number
  total: number
  notes?: string
  valid_until?: string
  created_at: string
  updated_at: string
}

export interface CreateQuotePayload {
  title: string
  customer_id: string
  lead_id?: string
  currency?: Currency
  notes?: string
  valid_until?: string
  items: Omit<QuoteItem, 'id' | 'total'>[]
  premise_ids?: string[]
}

export interface QuoteListParams {
  status?: QuoteStatus
  customer_id?: string
  lead_id?: string
  page?: number
  limit?: number
}

export const quotesApi = {
  list: (params?: QuoteListParams) =>
    api.get<Quote[]>('/api/v1/quotes', { params }).then((r: any) => r.data),
  get: (id: string) =>
    api.get<Quote>(`/api/v1/quotes/${id}`).then((r: any) => r.data),
  create: (data: CreateQuotePayload) =>
    api.post<Quote>('/api/v1/quotes', data).then((r: any) => r.data),
  updateStatus: (id: string, status: QuoteStatus) =>
    api.patch<Quote>(`/api/v1/quotes/${id}/status`, { status }).then((r: any) => r.data),
  recalculate: (id: string) =>
    api.post<Quote>(`/api/v1/quotes/${id}/recalculate`).then((r: any) => r.data),
  remove: (id: string) =>
    api.delete(`/api/v1/quotes/${id}`),
}

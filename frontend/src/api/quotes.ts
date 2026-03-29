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
  type: string
  value: number
  amount: number
}

export interface Quote {
  id: string
  tenant_id: string
  title: string
  customer_id?: string
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
  sale_price?: number
}

export interface QuoteListParams {
  status?: QuoteStatus
  customer_id?: string
  lead_id?: string
  page?: number
  limit?: number
}

function mapQuoteItem(item: any): QuoteItem {
  return {
    id: item.id,
    description: item.description,
    quantity: item.quantity,
    unit_price: item.unit_price,
    discount_percent: item.discount_percent ?? 0,
    total: item.total ?? item.unit_price * item.quantity,
  }
}

function mapQuote(q: any): Quote {
  return {
    id: q.id,
    tenant_id: q.tenant_id,
    title: q.title,
    customer_id: q.customer_id,
    customer_name: q.customer_name,
    lead_id: q.lead_id,
    status: q.status,
    currency: q.currency ?? 'BRL',
    items: (q.items ?? []).map(mapQuoteItem),
    applied_premises: q.applied_premises ?? [],
    subtotal: q.items_total ?? q.subtotal ?? 0,
    total: q.total ?? 0,
    notes: q.notes,
    valid_until: q.valid_until,
    created_at: q.created_at,
    updated_at: q.updated_at,
  }
}

export const quotesApi = {
  list: (params?: QuoteListParams) =>
    api.get('/api/v1/quotes', { params }).then((r: any) => {
      const d = r.data
      const items = Array.isArray(d) ? d : (d?.items ?? [])
      return items.map(mapQuote) as Quote[]
    }),
  get: (id: string) =>
    api.get(`/api/v1/quotes/${id}`).then((r: any) => mapQuote(r.data)),
  create: (data: CreateQuotePayload) =>
    api.post<Quote>('/api/v1/quotes', data).then((r: any) => mapQuote(r.data)),
  updateStatus: (id: string, status: QuoteStatus) =>
    api.patch<Quote>(`/api/v1/quotes/${id}/status`, { status }).then((r: any) => mapQuote(r.data)),
  recalculate: (id: string) =>
    api.post<Quote>(`/api/v1/quotes/${id}/recalculate`).then((r: any) => mapQuote(r.data)),
  remove: (id: string) =>
    api.delete(`/api/v1/quotes/${id}`),
  exportReport: () =>
    api.get('/api/v1/quotes/report/pdf', { responseType: 'arraybuffer' }).then((r: any) => r.data),
  downloadPdf: (id: string) =>
    api.get(`/api/v1/quotes/${id}/pdf`, { responseType: 'arraybuffer' }).then((r: any) => r.data as ArrayBuffer),
}

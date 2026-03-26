import { api } from './client'

export type LeadStage = 'new' | 'contacted' | 'qualified' | 'proposal' | 'negotiation' | 'won' | 'lost'

export interface Lead {
  id: string
  tenant_id: string
  customer_id?: string | null
  title: string
  stage: LeadStage
  value: number
  currency: string
  source: string
  assigned_to?: string | null
  notes: string
  expected_close_date?: string | null
  closed_at?: string | null
  lost_reason: string
  tags: string[]
  created_at: string
  updated_at: string
}

export interface LeadListParams {
  stage?: LeadStage
  assigned_to?: string
  search?: string
  offset?: number
  limit?: number
}

export interface LeadListResponse {
  items: Lead[]
  total: number
  offset: number
  limit: number
}

export interface CreateLeadPayload {
  title: string
  customer_id?: string
  value?: number
  source?: string
  assigned_to?: string
  notes?: string
  expected_close_date?: string
  tags?: string[]
}

export const leadsApi = {
  list: (params?: LeadListParams) =>
    api.get<LeadListResponse>('/api/v1/leads', { params }).then((r: any) => r.data),
  get: (id: string) =>
    api.get<Lead>(`/api/v1/leads/${id}`).then((r: any) => r.data),
  create: (data: CreateLeadPayload) =>
    api.post<Lead>('/api/v1/leads', data).then((r: any) => r.data),
  update: (id: string, data: Partial<CreateLeadPayload>) =>
    api.put<Lead>(`/api/v1/leads/${id}`, data).then((r: any) => r.data),
  moveStage: (id: string, stage: LeadStage, lost_reason?: string) =>
    api.patch<Lead>(`/api/v1/leads/${id}/stage`, { stage, lost_reason: lost_reason ?? '' }).then((r: any) => r.data),
  remove: (id: string) =>
    api.delete(`/api/v1/leads/${id}`),
}

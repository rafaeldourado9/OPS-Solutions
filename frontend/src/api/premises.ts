import { api } from './client'

export type PremiseType = 'percentage' | 'fixed' | 'multiplier'

export interface Premise {
  id: string
  tenant_id: string
  name: string
  type: PremiseType
  value: number   // % (0-100) | fixed R$ | multiplier factor (e.g. 2.5)
  cost: number    // base cost for multiplier type
  is_active: boolean
  description: string
  created_at: string
  updated_at: string
}

export interface CreatePremisePayload {
  name: string
  type: PremiseType
  value: number
  cost?: number
  description?: string
}

export const premisesApi = {
  list: () =>
    api.get<Premise[]>('/api/v1/premises').then((r: any) => r.data),
  create: (data: CreatePremisePayload) =>
    api.post<Premise>('/api/v1/premises', data).then((r: any) => r.data),
  update: (id: string, data: Partial<CreatePremisePayload> & { is_active?: boolean }) =>
    api.put<Premise>(`/api/v1/premises/${id}`, data).then((r: any) => r.data),
  remove: (id: string) =>
    api.delete(`/api/v1/premises/${id}`),
}

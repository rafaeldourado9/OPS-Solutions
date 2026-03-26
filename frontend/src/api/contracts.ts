import { api } from './client'

export type ContractStatus = 'draft' | 'active' | 'signed' | 'cancelled' | 'expired'

export interface Contract {
  id: string
  tenant_id: string
  title: string
  customer_id: string
  customer_name?: string
  quote_id?: string
  status: ContractStatus
  value: number
  signed_at?: string
  expires_at?: string
  created_at: string
  updated_at: string
}

export interface CreateContractPayload {
  title: string
  customer_id: string
  quote_id?: string
  value: number
  expires_at?: string
}

export const contractsApi = {
  list: (params?: { status?: ContractStatus; page?: number; limit?: number }) =>
    api.get<Contract[]>('/api/v1/contracts', { params }).then((r: any) => r.data),
  get: (id: string) =>
    api.get<Contract>(`/api/v1/contracts/${id}`).then((r: any) => r.data),
  create: (data: CreateContractPayload) =>
    api.post<Contract>('/api/v1/contracts', data).then((r: any) => r.data),
  updateStatus: (id: string, status: ContractStatus) =>
    api.patch<Contract>(`/api/v1/contracts/${id}/status`, { status }).then((r: any) => r.data),
}

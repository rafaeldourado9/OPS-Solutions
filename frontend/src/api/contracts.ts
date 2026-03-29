import { api } from './client'

export type ContractStatus = 'draft' | 'active' | 'completed' | 'cancelled'

export interface Contract {
  id: string
  tenant_id: string
  title: string
  customer_id?: string
  customer_name?: string
  quote_id: string
  status: ContractStatus
  value: number
  content?: string
  signed_at?: string
  expires_at?: string
  created_at: string
  updated_at: string
}

export interface CreateContractPayload {
  quote_id: string
  title: string
  content?: string
  expires_at?: string
}

function mapContract(c: any): Contract {
  return {
    id: c.id,
    tenant_id: c.tenant_id,
    title: c.title,
    customer_id: c.customer_id,
    customer_name: c.customer_name,
    quote_id: c.quote_id,
    status: c.status,
    value: c.value ?? 0,
    content: c.content,
    signed_at: c.signed_at,
    expires_at: c.expires_at,
    created_at: c.created_at,
    updated_at: c.updated_at,
  }
}

export const contractsApi = {
  list: (params?: { status?: ContractStatus; offset?: number; limit?: number }) =>
    api.get('/api/v1/contracts', { params }).then((r: any) => {
      const d = r.data
      const items = Array.isArray(d) ? d : (d?.items ?? [])
      return items.map(mapContract) as Contract[]
    }),
  get: (id: string) =>
    api.get(`/api/v1/contracts/${id}`).then((r: any) => mapContract(r.data)),
  create: (data: CreateContractPayload) =>
    api.post('/api/v1/contracts', data).then((r: any) => mapContract(r.data)),
  updateStatus: (id: string, status: ContractStatus) =>
    api.patch(`/api/v1/contracts/${id}/status`, { status }).then((r: any) => mapContract(r.data)),
}

import { api } from './client'

export interface Customer {
  id: string
  tenant_id: string
  name: string
  phone: string
  email?: string | null
  cpf_cnpj?: string | null
  company_name?: string | null
  notes: string
  tags: string[]
  source: 'whatsapp' | 'manual' | 'import'
  chat_id: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CustomerListParams {
  search?: string
  offset?: number
  limit?: number
}

export interface CustomerListResponse {
  items: Customer[]
  total: number
  offset: number
  limit: number
}

export interface CreateCustomerPayload {
  name: string
  phone: string
  email?: string
  company_name?: string
  cpf_cnpj?: string
  notes?: string
  source?: 'whatsapp' | 'manual' | 'import'
}

export const customersApi = {
  list: (params?: CustomerListParams) =>
    api.get<CustomerListResponse>('/api/v1/customers', { params }).then((r: any) => r.data),
  get: (id: string) =>
    api.get<Customer>(`/api/v1/customers/${id}`).then((r: any) => r.data),
  create: (data: CreateCustomerPayload) =>
    api.post<Customer>('/api/v1/customers', data).then((r: any) => r.data),
  update: (id: string, data: Partial<CreateCustomerPayload> & { is_active?: boolean }) =>
    api.put<Customer>(`/api/v1/customers/${id}`, data).then((r: any) => r.data),
  remove: (id: string) =>
    api.delete(`/api/v1/customers/${id}`),
}

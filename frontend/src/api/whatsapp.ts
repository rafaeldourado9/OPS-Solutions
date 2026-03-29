import { api } from './client'

export interface WhatsAppNumber {
  id: string
  session_name: string
  phone_number: string | null
  label: string | null
  agent_id: string | null
  is_active: boolean
  status: string
  connected_at: string | null
  created_at: string | null
}

export interface AddNumberPayload {
  label?: string
  agent_id?: string
}

export interface QrResponse {
  qr: string | null
  status: string
  phone: string | null
  circuit: string
  receivedAt?: number | null
  error?: string
}

export const whatsappApi = {
  listNumbers: () =>
    api.get<WhatsAppNumber[]>('/api/v1/whatsapp/numbers').then((r: any) => r.data),

  addNumber: (data: AddNumberPayload) =>
    api.post<WhatsAppNumber>('/api/v1/whatsapp/numbers', data).then((r: any) => r.data),

  removeNumber: (id: string) =>
    api.delete(`/api/v1/whatsapp/numbers/${encodeURIComponent(id)}`),

  updateNumber: (id: string, updates: AddNumberPayload) =>
    api.put<WhatsAppNumber>(`/api/v1/whatsapp/numbers/${encodeURIComponent(id)}`, updates).then((r: any) => r.data),

  getQr: (id: string) =>
    api.get<QrResponse>(`/api/v1/whatsapp/numbers/${encodeURIComponent(id)}/qr`).then((r: any) => r.data),

  getStatus: (id: string) =>
    api.get<{status: string, phone: string | null, uptime: number}>(`/api/v1/whatsapp/numbers/${encodeURIComponent(id)}/status`).then((r: any) => r.data),

  restart: (id: string) =>
    api.post<{ status: string }>(`/api/v1/whatsapp/numbers/${encodeURIComponent(id)}/restart`).then((r: any) => r.data),

  logout: (id: string) =>
    api.post<{ status: string }>(`/api/v1/whatsapp/numbers/${encodeURIComponent(id)}/logout`).then((r: any) => r.data),
}

import { api } from './client'

export type ConversationStatus = 'active' | 'takeover' | 'closed' | 'waiting'

export interface Conversation {
  chat_id: string
  tenant_id: string
  customer_id?: string
  customer_name: string
  customer_phone: string
  status: ConversationStatus
  last_message?: string
  last_message_at?: string
  unread_count: number
  takeover_active: boolean
  operator_id?: string
  operator_name?: string
}

export type MessageRole = 'user' | 'agent' | 'operator'

export interface Message {
  id: string
  chat_id: string
  role: MessageRole
  content: string
  timestamp: string
  operator_name?: string
}

export interface ConversationListParams {
  status?: ConversationStatus
  page?: number
  limit?: number
}

export const conversationsApi = {
  list: (params?: ConversationListParams) =>
    api.get<Conversation[]>('/api/v1/conversations', { params }).then((r: any) => r.data),
  getMessages: (chatId: string, params?: { page?: number; limit?: number }) =>
    api.get<Message[]>(`/api/v1/conversations/${chatId}/messages`, { params }).then((r: any) => r.data),
  startTakeover: (chatId: string) =>
    api.post(`/api/v1/conversations/${chatId}/takeover`).then((r: any) => r.data),
  endTakeover: (chatId: string) =>
    api.delete(`/api/v1/conversations/${chatId}/takeover`).then((r: any) => r.data),
  sendMessage: (chatId: string, content: string) =>
    api.post<Message>(`/api/v1/conversations/${chatId}/messages`, { content }).then((r: any) => r.data),
}

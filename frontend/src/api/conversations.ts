import { api } from './client'

export type ConversationStatus = 'active' | 'takeover' | 'closed' | 'waiting'

export interface Conversation {
  id: string
  chat_id: string
  tenant_id: string
  agent_id: string
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

function mapConversation(c: any): Conversation {
  return {
    id: c.id,
    chat_id: c.chat_id,
    tenant_id: c.tenant_id,
    agent_id: c.agent_id ?? '',
    customer_id: c.customer_id,
    customer_name: c.customer_name ?? 'Desconhecido',
    customer_phone: c.customer_phone ?? '',
    status: c.status,
    last_message: c.last_message_preview ?? c.last_message,
    last_message_at: c.last_message_at,
    unread_count: c.unread_count ?? 0,
    takeover_active: c.is_takeover_active ?? c.takeover_active ?? false,
    operator_id: c.takeover_operator_id ?? c.operator_id,
    operator_name: c.operator_name,
  }
}

function mapMessage(m: any): Message {
  return {
    id: m.id,
    chat_id: m.chat_id,
    role: m.role,
    content: m.content,
    timestamp: m.created_at ?? m.timestamp,
    operator_name: m.sender_name ?? m.operator_name,
  }
}

export interface MessagePage {
  items: Message[]
  total: number
  offset: number
  limit: number
}

export interface ConversationPage {
  items: Conversation[]
  total: number
  offset: number
  limit: number
}

export const conversationsApi = {
  list: (params?: { status?: ConversationStatus; agent_id?: string; offset?: number; limit?: number }) =>
    api.get('/api/v1/conversations', { params }).then((r: any): ConversationPage => {
      const data = r.data
      if (Array.isArray(data)) return { items: data.map(mapConversation), total: data.length, offset: 0, limit: data.length }
      return {
        items: (data?.items ?? []).map(mapConversation),
        total: data?.total ?? 0,
        offset: data?.offset ?? 0,
        limit: data?.limit ?? 50,
      }
    }),

  getMessages: (chatId: string, params?: { offset?: number; limit?: number; order?: 'asc' | 'desc'; agent_id?: string }) =>
    api.get(`/api/v1/conversations/${chatId}/messages`, { params }).then((r: any): MessagePage => {
      const data = r.data
      if (Array.isArray(data)) return { items: data.map(mapMessage), total: data.length, offset: 0, limit: data.length }
      return {
        items: (data?.items ?? []).map(mapMessage),
        total: data?.total ?? 0,
        offset: data?.offset ?? 0,
        limit: data?.limit ?? 50,
      }
    }),

  startTakeover: (chatId: string, agentId?: string) =>
    api.post(`/api/v1/conversations/${chatId}/takeover`, null, { params: agentId ? { agent_id: agentId } : undefined }).then((r: any) => r.data),

  endTakeover: (chatId: string, agentId?: string) =>
    api.delete(`/api/v1/conversations/${chatId}/takeover`, { params: agentId ? { agent_id: agentId } : undefined }).then((r: any) => r.data),

  sendMessage: (chatId: string, content: string, agentId?: string) =>
    api.post(`/api/v1/conversations/${chatId}/messages`, { content }, { params: agentId ? { agent_id: agentId } : undefined }).then((r: any) => mapMessage(r.data)),

  deleteConversation: (chatId: string, agentId?: string) =>
    api.delete(`/api/v1/conversations/${chatId}`, { params: agentId ? { agent_id: agentId } : undefined }),

  renameContact: (chatId: string, name: string, agentId?: string) =>
    api.patch(`/api/v1/conversations/${chatId}/rename`, { name }, { params: agentId ? { agent_id: agentId } : undefined }).then((r: any) => r.data),
}

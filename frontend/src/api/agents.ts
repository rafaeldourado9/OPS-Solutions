import { api } from './client'

export interface AgentInstance {
  agent_id: string
  name: string
  company: string
  active: boolean
}

export interface AgentConfig {
  agent: {
    name: string
    company: string
    language: string
    persona: string
    admin_phones: string[]
    waha_url?: string
    waha_session?: string
  }
  llm: {
    provider: string
    model: string
    fallback_provider: string
    fallback_model: string
    temperature: number
    max_tokens: number
    api_key_set?: boolean  // true if a key is stored — never the key itself
  }
  messaging: {
    debounce_seconds: number
    max_message_chars: number
    typing_delay_per_char: number
    min_pause_between_parts: number
    max_pause_between_parts: number
  }
  memory: {
    qdrant_collection: string
    qdrant_rag_collection: string
    semantic_k: number
    max_recent_messages: number
    embedding_model: string
  }
  anti_hallucination: {
    rag_mandatory: boolean
    unknown_answer: string
    grounding_enabled: boolean
  }
  media: {
    audio_model: string
    image_model: string
    video_model: string
    video_frame_interval: number
    tts_enabled: boolean
    tts_voice: string
    tts_voices: string[]
    tts_chance: number
  }
  crm: {
    enabled: boolean
    events_webhook: string
    push_events: string[]
  }
}

export interface RagDocument {
  name: string
  collection: string
  chunk_count: number
  ingested_at: string | null
}

export interface WhatsAppStatus {
  status: string
  circuit: string
  phone: string | null
  uptime: number
  error?: string
}

export interface QrResponse {
  qr: string | null
  status: string
  phone: string | null
  circuit: string
  receivedAt?: number | null
  error?: string
}

export interface LlmModelsResponse {
  provider: string
  models: string[]
}

export const agentsApi = {
  // Instances
  listInstances: () =>
    api.get<AgentInstance[]>('/api/v1/agents/instances').then((r: any) => r.data),

  createInstance: (data: { agent_id: string; name?: string; company?: string }) =>
    api.post<AgentInstance>('/api/v1/agents/instances', data).then((r: any) => r.data),

  deleteInstance: (agent_id: string) =>
    api.delete(`/api/v1/agents/instances/${encodeURIComponent(agent_id)}`),

  activateInstance: (agent_id: string) =>
    api.post<{ agent_id: string; active: boolean }>(`/api/v1/agents/instances/${encodeURIComponent(agent_id)}/activate`).then((r: any) => r.data),

  // Config
  getConfig: () =>
    api.get<AgentConfig>('/api/v1/agents/config').then((r: any) => r.data),

  updateConfig: (updates: Record<string, unknown>) =>
    api.put<AgentConfig>('/api/v1/agents/config', { updates }).then((r: any) => r.data),

  // RAG documents
  listDocs: (agentId?: string) =>
    api.get<RagDocument[]>('/api/v1/agents/rag/documents', {
      params: agentId ? { agent_id: agentId } : undefined,
    }).then((r: any) => r.data),

  uploadDoc: (file: File, agentId: string, docName?: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('agent_id', agentId)
    if (docName) form.append('doc_name', docName)
    return api.post<RagDocument>('/api/v1/agents/rag/documents', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r: any) => r.data)
  },

  deleteDoc: (name: string, agentId?: string) =>
    api.delete(`/api/v1/agents/rag/documents/${encodeURIComponent(name)}`, {
      params: agentId ? { agent_id: agentId } : undefined,
    }),

  // WhatsApp
  getWhatsAppStatus: () =>
    api.get<WhatsAppStatus>('/api/v1/agents/whatsapp/status').then((r: any) => r.data),

  getWhatsAppQr: () =>
    api.get<QrResponse>('/api/v1/agents/whatsapp/qr').then((r: any) => r.data),

  restartWhatsApp: () =>
    api.post<{ status: string }>('/api/v1/agents/whatsapp/restart').then((r: any) => r.data),

  logoutWhatsApp: () =>
    api.post<{ status: string }>('/api/v1/agents/whatsapp/logout').then((r: any) => r.data),

  // LLM models
  listLlmModels: (provider: string) =>
    api.get<LlmModelsResponse>(`/api/v1/agents/llm/models?provider=${provider}`).then((r: any) => r.data),
}

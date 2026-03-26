import { api } from './client'

export interface AgentConfig {
  name: string
  persona: string
  instructions: string
  model: string
  temperature: number
  max_tokens: number
}

export interface RagDocument {
  name: string
  size_bytes: number
  uploaded_at: string
  chunks?: number
}

export const agentsApi = {
  getConfig: () =>
    api.get<AgentConfig>('/api/v1/agents/config').then((r: any) => r.data),
  updateConfig: (data: Partial<AgentConfig>) =>
    api.put<AgentConfig>('/api/v1/agents/config', data).then((r: any) => r.data),
  listDocs: () =>
    api.get<RagDocument[]>('/api/v1/agents/rag/documents').then((r: any) => r.data),
  uploadDoc: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<RagDocument>('/api/v1/agents/rag/documents', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r: any) => r.data)
  },
  deleteDoc: (name: string) =>
    api.delete(`/api/v1/agents/rag/documents/${encodeURIComponent(name)}`),
}

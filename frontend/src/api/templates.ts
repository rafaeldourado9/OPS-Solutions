import { api } from './client'

export interface QuoteTemplate {
  id: string
  tenant_id: string
  name: string
  filename: string
  placeholders: string[]
  created_at: string
}

export const templatesApi = {
  list: () =>
    api.get<QuoteTemplate[]>('/api/v1/quote-templates').then((r: any) => r.data),
  upload: (file: File, name?: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('name', name || file.name.replace('.docx', ''))
    form.append('description', '')
    return api.post<QuoteTemplate>('/api/v1/quote-templates', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r: any) => r.data)
  },
  remove: (id: string) =>
    api.delete(`/api/v1/quote-templates/${id}`),
  generate: (templateId: string, quoteId: string) =>
    api.post(
      `/api/v1/quote-templates/${templateId}/generate/${quoteId}`,
      {},
      { responseType: 'blob' }
    ).then(r => r.data as Blob),
}

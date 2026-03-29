import { api } from './client'

export interface QuoteTemplate {
  id: string
  tenant_id: string
  name: string
  description?: string
  placeholders: string[]
  field_mapping: Record<string, string>
  created_at: string
  updated_at?: string
}

export interface CrmFieldOption {
  key: string
  label: string
}

export interface GeneratedDocument {
  quote_id: string
  template_id: string
  pdf_url: string
  docx_url: string
}

export interface FieldSuggestion {
  original_text: string
  placeholder_key: string
  crm_field: string
  description: string
  confidence: number
}

export interface AnalyzeTemplateResult {
  suggestions: FieldSuggestion[]
  document_text_preview: string
}

export const templatesApi = {
  list: () =>
    api.get<QuoteTemplate[]>('/api/v1/quote-templates').then((r: any) => r.data as QuoteTemplate[]),

  /** Step 1: analyze only — does NOT save. Returns AI suggestions. */
  analyze: (file: File): Promise<AnalyzeTemplateResult> => {
    const form = new FormData()
    form.append('file', file)
    return api.post<AnalyzeTemplateResult>('/api/v1/quote-templates/analyze', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r: any) => r.data as AnalyzeTemplateResult)
  },

  /** Step 2: upload with optional AI injections confirmed by the user. */
  upload: (file: File, name?: string, injectSuggestions?: Record<string, string>) => {
    const form = new FormData()
    form.append('file', file)
    form.append('name', name || file.name.replace('.docx', ''))
    form.append('description', '')
    form.append('inject_suggestions', JSON.stringify(injectSuggestions ?? {}))
    return api.post<QuoteTemplate>('/api/v1/quote-templates', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r: any) => r.data as QuoteTemplate)
  },

  remove: (id: string) =>
    api.delete(`/api/v1/quote-templates/${id}`),

  updateMapping: (id: string, fieldMapping: Record<string, string>): Promise<QuoteTemplate> =>
    api.patch<QuoteTemplate>(`/api/v1/quote-templates/${id}/mapping`, { field_mapping: fieldMapping })
      .then((r: any) => r.data as QuoteTemplate),

  listCrmFields: (): Promise<CrmFieldOption[]> =>
    api.get<CrmFieldOption[]>('/api/v1/quote-templates/crm-fields')
      .then((r: any) => r.data as CrmFieldOption[]),

  generate: (templateId: string, quoteId: string, extraContext?: Record<string, string>): Promise<GeneratedDocument> =>
    api.post<GeneratedDocument>(
      `/api/v1/quote-templates/${templateId}/generate/${quoteId}`,
      { extra_context: extraContext ?? {} }
    ).then((r: any) => r.data as GeneratedDocument),
}

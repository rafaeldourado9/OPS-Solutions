import { api } from './client'

export interface ContractTemplate {
  id: string
  name: string
  description: string
  variables: string[]
  created_at: string
}

export const contractTemplatesApi = {
  list: () =>
    api.get<ContractTemplate[]>('/api/v1/contract-templates').then((r: any) => r.data as ContractTemplate[]),

  upload: (file: File, name: string, description?: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('name', name)
    form.append('description', description ?? '')
    return api.post<ContractTemplate>('/api/v1/contract-templates', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r: any) => r.data as ContractTemplate)
  },

  remove: (id: string) =>
    api.delete(`/api/v1/contract-templates/${id}`),

  generate: (id: string, variableValues: Record<string, string>): Promise<ArrayBuffer> =>
    api.post(
      `/api/v1/contract-templates/${id}/generate`,
      { variable_values: variableValues },
      { responseType: 'arraybuffer' },
    ).then((r: any) => r.data as ArrayBuffer),
}

import { api } from './client'

export interface TeamMember {
  id: string
  name: string
  email: string
  role: 'admin' | 'manager' | 'operator'
  is_active: boolean
  created_at: string
}

export const usersApi = {
  list: () =>
    api.get<TeamMember[]>('/api/v1/users').then(r => r.data),

  invite: (data: { name: string; email: string; role: string }) =>
    api.post<TeamMember>('/api/v1/users/invite', data).then(r => r.data),

  updateRole: (id: string, role: string) =>
    api.put<TeamMember>(`/api/v1/users/${id}/role`, { role }).then(r => r.data),

  toggleActive: (id: string) =>
    api.put<TeamMember>(`/api/v1/users/${id}/deactivate`).then(r => r.data),

  delete: (id: string) =>
    api.delete(`/api/v1/users/${id}`),
}

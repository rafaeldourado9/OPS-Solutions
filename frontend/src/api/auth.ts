import { api } from './client'

export interface RegisterPayload {
  tenant_name: string
  tenant_slug: string
  user_name: string
  email: string
  password: string
  plan?: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: { id: string; name: string; email: string; role: string }
  tenant: { id: string; name: string; slug: string; plan: string }
}

export const authApi = {
  register: (data: RegisterPayload) =>
    api.post<AuthResponse>('/api/v1/auth/register', data).then(r => r.data),
  login: (data: LoginPayload) =>
    api.post<AuthResponse>('/api/v1/auth/login', data).then(r => r.data),
}

import { api } from './client'

export interface UserProfile {
  id: string
  name: string
  email: string
  role: string
  avatar_url?: string | null
}

export interface TenantProfile {
  id: string
  name: string
  slug: string
  plan: string
  primary_color: string
  secondary_color: string
  logo_url: string | null
}

export interface Integrations {
  gemini_api_key: string
  gemini_api_key_set?: boolean
  webhook_url?: string
}

export interface CompanyProfile {
  phone: string
  email: string
  website: string
  cnpj: string
  address_street: string
  address_number: string
  address_complement: string
  address_neighborhood: string
  address_city: string
  address_state: string
  address_zip: string
}

export interface BankingData {
  bank_name: string
  agency: string
  account: string
  account_type: string
  pix_key: string
  pix_key_type: string
  beneficiary: string
}

export const settingsApi = {
  getMe: () =>
    api.get<{ user: UserProfile; tenant: { id: string; name: string; slug: string; plan: string } }>('/api/v1/auth/me')
      .then((r: any) => r.data),

  updateMe: (data: { name?: string; email?: string }) =>
    api.put<UserProfile>('/api/v1/auth/me', data).then((r: any) => r.data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    api.put('/api/v1/auth/me/password', data),

  uploadAvatar: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post<{ avatar_url: string }>('/api/v1/auth/me/avatar', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r: any) => r.data)
  },

  getTenant: () =>
    api.get<TenantProfile>('/api/v1/auth/tenant').then((r: any) => r.data),

  updateTenant: (data: { name?: string; primary_color?: string; secondary_color?: string }) =>
    api.put<TenantProfile>('/api/v1/auth/tenant', data).then((r: any) => r.data),

  getIntegrations: () =>
    api.get<Integrations>('/api/v1/auth/tenant/integrations').then((r: any) => r.data),

  updateIntegrations: (data: Partial<Integrations>) =>
    api.put<Integrations>('/api/v1/auth/tenant/integrations', data).then((r: any) => r.data),

  testWebhook: () =>
    api.post<{ status: string; http_status: number; url: string }>('/api/v1/auth/tenant/integrations/test-webhook').then((r: any) => r.data),

  getCompany: () =>
    api.get<CompanyProfile>('/api/v1/auth/tenant/company').then((r: any) => r.data),

  updateCompany: (data: Partial<CompanyProfile>) =>
    api.put<CompanyProfile>('/api/v1/auth/tenant/company', data).then((r: any) => r.data),

  getBanking: () =>
    api.get<BankingData>('/api/v1/auth/tenant/banking').then((r: any) => r.data),

  updateBanking: (data: Partial<BankingData>) =>
    api.put<BankingData>('/api/v1/auth/tenant/banking', data).then((r: any) => r.data),

  uploadLogo: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post<{ logo_url: string }>('/api/v1/auth/tenant/logo', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r: any) => r.data as { logo_url: string })
  },
}

export interface SubscriptionInfo {
  plan: string
  subscription_status: string | null
  mp_subscription_id: string | null
  mp_payer_email: string | null
}

export const subscriptionApi = {
  getCurrent: () =>
    api.get<SubscriptionInfo>('/api/v1/subscriptions/current').then((r: any) => r.data),

  checkout: (plan: 'starter' | 'pro') =>
    api.post<{ checkout_url: string; subscription_id: string }>('/api/v1/subscriptions/checkout', { plan })
      .then((r: any) => r.data),

  cancel: () =>
    api.post('/api/v1/subscriptions/cancel'),
}

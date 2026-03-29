import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User { id: string; name: string; email: string; role: string; avatar_url?: string | null }
interface Tenant { id: string; name: string; slug: string; plan: string; effective_plan?: string; trial_ends_at?: string | null; trial_days_remaining?: number; subscription_status?: string | null; mp_payer_email?: string | null; niche?: string | null }

interface AuthState {
  token: string | null
  user: User | null
  tenant: Tenant | null
  setAuth: (token: string, user: User, tenant: Tenant) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    set => ({
      token: null,
      user: null,
      tenant: null,
      setAuth: (token, user, tenant) => set({ token, user, tenant }),
      logout: () => {
        set({ token: null, user: null, tenant: null })
        window.location.href = '/'
      },
    }),
    { name: 'ops-auth' }
  )
)

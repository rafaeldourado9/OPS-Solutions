import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User { id: string; name: string; email: string; role: string }
interface Tenant { id: string; name: string; slug: string; plan: string }

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

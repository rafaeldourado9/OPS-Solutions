import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

function isExpired(trialEndsAt?: string | null): boolean {
  if (!trialEndsAt) return false
  return new Date(trialEndsAt) < new Date()
}

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token)
  const tenant = useAuthStore(s => s.tenant)

  if (!token) return <Navigate to="/auth/login" replace />

  if (isExpired(tenant?.trial_ends_at)) {
    return <Navigate to="/app/trial-expired" replace />
  }

  return <>{children}</>
}

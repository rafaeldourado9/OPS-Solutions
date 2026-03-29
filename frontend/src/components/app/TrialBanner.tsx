import { Warning, X } from '@phosphor-icons/react'
import { useState } from 'react'
import { useAuthStore } from '../../store/authStore'

function daysRemaining(trialEndsAt?: string | null): number {
  if (!trialEndsAt) return 999
  const ms = new Date(trialEndsAt).getTime() - Date.now()
  return Math.max(Math.ceil(ms / (1000 * 60 * 60 * 24)), 0)
}

export default function TrialBanner() {
  const tenant = useAuthStore(s => s.tenant)
  const storageKey = `trial_banner_dismissed_${tenant?.id}`
  const [dismissed, setDismissed] = useState(() => {
    if (!tenant?.id) return false
    return localStorage.getItem(`trial_banner_dismissed_${tenant.id}`) === '1'
  })

  function dismiss() {
    localStorage.setItem(storageKey, '1')
    setDismissed(true)
  }

  const days = daysRemaining(tenant?.trial_ends_at)

  if (!tenant?.trial_ends_at || days === 0 || dismissed) return null

  const isUrgent = days <= 1
  const isExpiring = days <= 7

  // Show a green "welcome to Pro trial" banner for the first days (> 7 days left)
  if (!isExpiring) {
    return (
      <div className="w-full flex items-center justify-between gap-3 px-4 py-2.5 text-sm font-medium bg-[#0ABAB5] text-white">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Warning size={15} weight="fill" className="shrink-0" />
          <span className="truncate">
            Você tem acesso completo ao plano <strong>Pro</strong> durante os {days} dias de teste gratuito.{' '}
            <a href="/app/settings?tab=assinatura" className="underline underline-offset-2 text-white">
              Ver planos
            </a>
          </span>
        </div>
        <button onClick={dismiss} aria-label="Fechar aviso" className="shrink-0 opacity-70 hover:opacity-100 transition-opacity">
          <X size={14} weight="bold" />
        </button>
      </div>
    )
  }

  const label = days === 1 ? 'amanhã' : `em ${days} dias`

  return (
    <div
      className={`w-full flex items-center justify-between gap-3 px-4 py-2.5 text-sm font-medium ${
        isUrgent
          ? 'bg-red-500 text-white'
          : 'bg-amber-400 text-amber-950'
      }`}
    >
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <Warning size={15} weight="fill" className="shrink-0" />
        <span className="truncate">
          Seu trial Pro expira <strong>{label}</strong>.{' '}
          <a
            href="/app/settings?tab=assinatura"
            className={`underline underline-offset-2 ${isUrgent ? 'text-white' : 'text-amber-950'}`}
          >
            Escolher um plano
          </a>
        </span>
      </div>
      <button
        onClick={dismiss}
        aria-label="Fechar aviso"
        className="shrink-0 opacity-70 hover:opacity-100 transition-opacity"
      >
        <X size={14} weight="bold" />
      </button>
    </div>
  )
}

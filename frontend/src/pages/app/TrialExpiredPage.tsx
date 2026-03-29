import { useState } from 'react'
import { ChatCircleDots, Clock, ArrowRight, SpinnerGap } from '@phosphor-icons/react'
import { useAuthStore } from '../../store/authStore'
import { subscriptionApi } from '../../api/settings'

const PLANS = [
  {
    key: 'starter' as const,
    name: 'Starter',
    price: 'R$ 297',
    period: '/mês',
    features: ['CRM completo (clientes, leads)', 'Conversas WhatsApp', 'Orçamentos básicos', 'Contratos básicos', 'Identidade visual', 'Até 3 usuários'],
  },
  {
    key: 'pro' as const,
    name: 'Pro',
    price: 'R$ 497',
    period: '/mês',
    highlight: true,
    badge: 'Recomendado',
    features: ['Tudo do Starter', 'Estoque & Inventário', 'Relatórios PDF exportáveis', 'Templates DOCX personalizados', 'Múltiplos agentes WhatsApp', 'RAG / documentos IA', 'Dashboard avançado', 'Usuários ilimitados', 'Suporte prioritário'],
  },
]

export default function TrialExpiredPage() {
  const { user, tenant, logout } = useAuthStore(s => ({ user: s.user, tenant: s.tenant, logout: s.logout }))
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState('')

  async function handleCheckout(plan: 'starter' | 'pro') {
    setLoading(plan)
    setError('')
    try {
      const res = await subscriptionApi.checkout(plan)
      window.location.href = res.checkout_url
    } catch {
      setError('Não foi possível processar o pagamento. Tente novamente.')
      setLoading(null)
    }
  }

  return (
    <div className="min-h-[100dvh] flex flex-col items-center justify-center bg-white px-6 py-16">
      {/* Header */}
      <div className="text-center mb-10 max-w-lg">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-amber-50 border border-amber-100 mb-5">
          <Clock size={26} weight="duotone" className="text-amber-500" />
        </div>
        <h1 className="text-3xl font-bold text-[#1D1D1F] tracking-tight mb-3">
          Seu trial encerrou, {user?.name.split(' ')[0]}.
        </h1>
        <p className="text-zinc-500 text-base leading-relaxed">
          O período gratuito de <strong>{tenant?.name}</strong> chegou ao fim.
          Seus dados estão preservados — escolha um plano para retomar de onde parou.
        </p>
      </div>

      {/* Plans */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 w-full max-w-xl mb-10">
        {PLANS.map(plan => (
          <div
            key={plan.key}
            className={`rounded-2xl p-6 flex flex-col border ${
              plan.highlight
                ? 'bg-[#1D1D1F] border-transparent text-white'
                : 'bg-white border-zinc-200'
            }`}
          >
            {plan.badge && (
              <span className="inline-block mb-3 text-[10px] font-bold uppercase tracking-wider bg-[#0ABAB5] text-white px-3 py-1 rounded-full w-fit">
                {plan.badge}
              </span>
            )}
            <p className={`text-xs font-bold uppercase tracking-wider mb-2 ${plan.highlight ? 'text-zinc-400' : 'text-zinc-400'}`}>
              {plan.name}
            </p>
            <div className="flex items-end gap-1 mb-4">
              <span className={`text-3xl font-bold tracking-tight ${plan.highlight ? 'text-white' : 'text-[#1D1D1F]'}`}>
                {plan.price}
              </span>
              <span className={`text-sm mb-1 ${plan.highlight ? 'text-zinc-400' : 'text-zinc-400'}`}>{plan.period}</span>
            </div>
            <ul className="space-y-2 mb-6 flex-1">
              {plan.features.map(f => (
                <li key={f} className={`text-xs flex items-center gap-2 ${plan.highlight ? 'text-zinc-300' : 'text-zinc-600'}`}>
                  <span className="w-1 h-1 rounded-full bg-[#0ABAB5] shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleCheckout(plan.key)}
              disabled={!!loading}
              className={`flex items-center justify-center gap-2 text-sm font-semibold py-3 rounded-xl transition-all disabled:opacity-60 active:scale-95 ${
                plan.highlight
                  ? 'bg-[#0ABAB5] text-white hover:bg-[#089B97]'
                  : 'border border-zinc-200 text-zinc-700 hover:bg-zinc-50'
              }`}
            >
              {loading === plan.key ? (
                <SpinnerGap size={14} className="animate-spin" />
              ) : (
                <ArrowRight size={14} weight="bold" />
              )}
              {loading === plan.key ? 'Redirecionando...' : `Assinar ${plan.name}`}
            </button>
          </div>
        ))}
      </div>

      {error && (
        <p className="text-sm text-red-500 mb-6">{error}</p>
      )}

      {/* Enterprise strip */}
      <div className="w-full max-w-xl bg-zinc-50 border border-zinc-100 rounded-2xl p-5 flex flex-col sm:flex-row items-center gap-4 mb-8">
        <div className="flex-1 text-center sm:text-left">
          <p className="text-sm font-bold text-[#1D1D1F]">Precisa de Enterprise?</p>
          <p className="text-xs text-zinc-400 mt-0.5">Agentes e usuários ilimitados, customização completa, SLA dedicado.</p>
        </div>
        <a
          href="https://wa.me/5511947880561"
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 flex items-center gap-2 text-xs font-semibold py-2.5 px-5 rounded-full bg-[#1D1D1F] text-white hover:bg-zinc-800 transition-all"
        >
          <ChatCircleDots size={13} weight="fill" />
          Falar no WhatsApp
        </a>
      </div>

      <button
        onClick={logout}
        className="text-xs text-zinc-400 hover:text-zinc-600 transition-colors"
      >
        Sair da conta
      </button>
    </div>
  )
}

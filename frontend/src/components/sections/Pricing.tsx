import { useState } from 'react'
import { Check, ChatCircleDots, Lightning, Star, Buildings, Robot } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'

interface Plan {
  key: string
  name: string
  icon: React.ReactNode
  price: string | null
  priceAnnual: string | null
  period: string
  sub: string
  badge?: string
  highlight?: boolean
  features: string[]
  limits: string[]
  cta: string
  ctaHref: string
  ctaStyle: 'primary' | 'outline' | 'dark' | 'teal-outline'
}

const PLANS: Plan[] = [
  {
    key: 'agent',
    name: 'Agente Solo',
    icon: <Robot size={16} weight="duotone" />,
    price: 'R$ 162',
    priceAnnual: 'R$ 121',
    period: '/mês',
    sub: '= R$ 5,40/dia — sem CRM',
    features: [
      'Agente IA no WhatsApp 24/7',
      'Personalizado para seu nicho',
      'Base de conhecimento (RAG)',
      'Respostas ilimitadas',
      'Entrega em até 5 dias úteis',
      'Suporte por WhatsApp',
    ],
    limits: [
      'Sem painel CRM',
      'Sem pipeline de leads',
      '1 número de WhatsApp',
    ],
    cta: 'Quero meu agente',
    ctaHref: 'https://wa.me/5511947880561?text=Quero+o+plano+Agente+Solo',
    ctaStyle: 'teal-outline',
  },
  {
    key: 'starter',
    name: 'Starter',
    icon: <Lightning size={16} weight="duotone" />,
    price: 'R$ 297',
    priceAnnual: 'R$ 222',
    period: '/mês',
    sub: 'CRM + agente IA incluso',
    features: [
      'Agente IA no WhatsApp',
      'Pipeline Kanban de leads',
      'Propostas comerciais em PDF',
      'Gerador de contratos',
      'Estoque e produtos',
      'Dashboard básico',
      'Relatórios simples',
    ],
    limits: [
      'Até 3 usuários',
      '1 número de WhatsApp',
      'Sem RAG nos agentes',
    ],
    cta: 'Começar 14 dias grátis',
    ctaHref: '/auth/signup?plan=starter',
    ctaStyle: 'outline',
  },
  {
    key: 'pro',
    name: 'Pro',
    icon: <Star size={16} weight="duotone" />,
    price: 'R$ 497',
    priceAnnual: 'R$ 372',
    period: '/mês',
    sub: 'Para times que querem escalar',
    badge: 'Mais popular',
    highlight: true,
    features: [
      'Tudo do Starter',
      'RAG nos agentes (base de conhecimento)',
      'Até 3 números de WhatsApp',
      'Até 4 agentes IA simultâneos',
      'Takeover humano em tempo real',
      'Usuários ilimitados',
      'Dashboard & analytics avançados',
      'Relatórios completos exportáveis',
      'Suporte prioritário',
    ],
    limits: [],
    cta: 'Começar 14 dias grátis',
    ctaHref: '/auth/signup?plan=pro',
    ctaStyle: 'primary',
  },
  {
    key: 'enterprise',
    name: 'Enterprise',
    icon: <Buildings size={16} weight="duotone" />,
    price: null,
    priceAnnual: null,
    period: '',
    sub: 'CRM modelado para o seu nicho',
    features: [
      'Tudo do Pro',
      'Agentes e usuários ilimitados',
      'Customização completa para o nicho',
      'Reunião de acompanhamento mensal',
      'Opção self-hosted (código-fonte incluso)',
      'IA local com Ollama (VPS inclusa)',
      'SLA dedicado com resposta em 2h',
      'Onboarding com apoio da equipe',
    ],
    limits: [],
    cta: 'Agendar conversa no WhatsApp',
    ctaHref: 'https://wa.me/5511947880561?text=Quero+saber+sobre+o+Enterprise',
    ctaStyle: 'dark',
  },
]

function PlanCard({ plan, annual }: { plan: Plan; annual: boolean }) {
  const displayPrice = annual ? plan.priceAnnual : plan.price

  let discountText = null
  if (annual && plan.price && plan.priceAnnual) {
    const pMonth = parseInt(plan.price.replace(/\D/g, ''), 10)
    const pAnnual = parseInt(plan.priceAnnual.replace(/\D/g, ''), 10)
    if (pMonth && pAnnual && pMonth > pAnnual) {
      const pct = Math.round(((pMonth - pAnnual) / pMonth) * 100)
      discountText = `economia de ${pct}%`
    }
  }

  const ctaClass = {
    primary: 'bg-[#0ABAB5] text-white hover:bg-[#089B97] hover:shadow-[0_6px_24px_rgba(10,186,181,0.45)]',
    outline: 'border border-zinc-200 text-zinc-700 hover:bg-zinc-50 hover:border-zinc-300',
    dark: 'bg-white/10 text-white border border-white/20 hover:bg-white/20',
    'teal-outline': 'border border-[#0ABAB5]/40 text-[#0ABAB5] hover:bg-[#0ABAB5]/5',
  }[plan.ctaStyle]

  if (plan.highlight) {
    return (
      <div className="relative bg-[#1D1D1F] text-white rounded-2xl p-8 flex flex-col h-full glow-featured">
        {plan.badge && (
          <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-[#0ABAB5] text-white text-xs font-bold px-5 py-1 rounded-full whitespace-nowrap shadow-lg shadow-[#0ABAB5]/30">
            {plan.badge}
          </span>
        )}

        <div className="flex items-center gap-2 mb-5">
          <span className="text-[#0ABAB5]">{plan.icon}</span>
          <p className="text-xs font-bold text-zinc-400 uppercase tracking-wider">{plan.name}</p>
        </div>

        <div className="mb-2">
          {displayPrice ? (
            <div className="flex items-end gap-1">
              <span className="text-5xl font-bold tracking-tight">{displayPrice}</span>
              <span className="text-base text-zinc-400 mb-2">{plan.period}</span>
            </div>
          ) : (
            <p className="text-3xl font-bold">Sob consulta</p>
          )}
          {annual && displayPrice && (
            <p className="text-xs font-semibold text-[#0ABAB5] mt-1">
              Cobrado anualmente{discountText ? ` — ${discountText}` : ''}
            </p>
          )}
        </div>
        <p className="text-sm text-zinc-400 mb-6">{plan.sub}</p>

        <ul className="space-y-3 mb-8 flex-1">
          {plan.features.map(f => (
            <li key={f} className="flex items-start gap-2.5 text-sm">
              <Check size={13} weight="bold" className="text-[#0ABAB5] shrink-0 mt-0.5" />
              <span className="text-zinc-300">{f}</span>
            </li>
          ))}
        </ul>

        {plan.ctaHref.startsWith('http') ? (
          <a href={plan.ctaHref} target="_blank" rel="noopener noreferrer"
            className={`block text-center font-semibold py-3.5 rounded-full text-sm transition-all active:scale-[0.97] ${ctaClass}`}>
            {plan.cta}
          </a>
        ) : (
          <Link to={annual && !plan.ctaHref.startsWith('http') ? `${plan.ctaHref}&billing=annual` : plan.ctaHref}
            className={`block text-center font-semibold py-3.5 rounded-full text-sm transition-all active:scale-[0.97] ${ctaClass}`}>
            {plan.cta}
          </Link>
        )}
      </div>
    )
  }

  const isDark = plan.ctaStyle === 'dark'

  return (
    <div className={`rounded-2xl p-6 flex flex-col h-full card-lift border ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-white border-zinc-200'}`}>
      <div className="flex items-center gap-2 mb-5">
        <span className="text-[#0ABAB5]">{plan.icon}</span>
        <p className={`text-xs font-bold uppercase tracking-wider ${isDark ? 'text-[#0ABAB5]' : 'text-zinc-400'}`}>{plan.name}</p>
      </div>

      <div className="mb-2">
        {displayPrice ? (
          <div className="flex items-end gap-1">
            <span className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-[#1D1D1F]'}`}>{displayPrice}</span>
            <span className={`text-sm mb-1.5 ${isDark ? 'text-zinc-400' : 'text-zinc-400'}`}>{plan.period}</span>
          </div>
        ) : (
          <p className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-[#1D1D1F]'}`}>Sob consulta</p>
        )}
        {annual && displayPrice && (
          <p className="text-[11px] font-semibold text-[#0ABAB5] mt-0.5">
            Cobrado anualmente{discountText ? ` — ${discountText}` : ''}
          </p>
        )}
      </div>
      <p className={`text-xs mb-5 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{plan.sub}</p>

      <ul className="space-y-2.5 mb-6 flex-1">
        {plan.features.map(f => (
          <li key={f} className={`flex items-start gap-2 text-xs ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
            <Check size={11} weight="bold" className="text-[#0ABAB5] shrink-0 mt-0.5" />
            {f}
          </li>
        ))}
        {plan.limits.length > 0 && (
          <>
            <li className="pt-1">
              <p className={`text-[10px] font-bold uppercase tracking-wider mb-2 ${isDark ? 'text-zinc-600' : 'text-zinc-300'}`}>Limites</p>
            </li>
            {plan.limits.map(l => (
              <li key={l} className={`flex items-start gap-2 text-xs ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>
                <span className="text-zinc-300 shrink-0 mt-0.5 text-[10px]">—</span>
                {l}
              </li>
            ))}
          </>
        )}
      </ul>

      {plan.ctaHref.startsWith('http') ? (
        <a href={plan.ctaHref} target="_blank" rel="noopener noreferrer"
          className={`flex items-center justify-center gap-1.5 text-xs font-semibold py-2.5 rounded-full transition-all active:scale-[0.97] ${ctaClass}`}>
          {plan.ctaStyle === 'dark' && <ChatCircleDots size={13} weight="fill" />}
          {plan.cta}
        </a>
      ) : (
        <Link to={annual && !plan.ctaHref.startsWith('http') ? `${plan.ctaHref}&billing=annual` : plan.ctaHref}
          className={`block text-center text-xs font-semibold py-2.5 rounded-full transition-all active:scale-[0.97] ${ctaClass}`}>
          {plan.cta}
        </Link>
      )}
    </div>
  )
}

export default function Pricing() {
  const [annual, setAnnual] = useState(false)

  return (
    <section className="bg-white py-28 px-6" id="planos">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12 fade-in">
          <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-[0.2em] mb-4">Planos</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-[#1D1D1F] mb-4">
            Do agente solo ao CRM completo.
          </h2>
          <p className="text-lg text-zinc-500 mb-8">14 dias grátis nos planos CRM. Sem cartão de crédito. Cancele quando quiser.</p>

          {/* Billing toggle */}
          <div className="inline-flex items-center gap-3 bg-zinc-100 rounded-full p-1">
            <button
              onClick={() => setAnnual(false)}
              className={`text-sm font-semibold px-5 py-2 rounded-full transition-all ${!annual ? 'bg-white shadow-sm text-[#1D1D1F]' : 'text-zinc-500'}`}
            >
              Mensal
            </button>
            <button
              onClick={() => setAnnual(true)}
              className={`text-sm font-semibold px-5 py-2 rounded-full transition-all flex items-center gap-2 ${annual ? 'bg-white shadow-sm text-[#1D1D1F]' : 'text-zinc-500'}`}
            >
              Anual
              <span className="text-[10px] font-bold bg-[#0ABAB5] text-white px-2 py-0.5 rounded-full">-25%</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5 items-stretch">
          {PLANS.map(plan => (
            <div key={plan.key} className={`fade-in ${plan.highlight ? 'sm:-mt-4 sm:mb-4' : ''}`}>
              <PlanCard plan={plan} annual={annual} />
            </div>
          ))}
        </div>

        {/* Annual savings callout */}
        {annual && (
          <div className="mt-8 text-center fade-in">
            <p className="text-sm text-zinc-500">
              No plano Pro anual você economiza{' '}
              <strong className="text-[#0ABAB5]">R$ 1.500/ano</strong> em relação ao mensal.
            </p>
          </div>
        )}

        <div className="mt-12 bg-zinc-50 rounded-2xl border border-zinc-100 p-6 flex flex-col sm:flex-row items-center gap-4 fade-in">
          <div className="flex-1 text-center sm:text-left">
            <p className="text-sm font-bold text-[#1D1D1F] mb-1">Enterprise ou self-hosted? Vamos conversar.</p>
            <p className="text-xs text-zinc-400">
              Modelamos o sistema para o nicho da sua empresa, com agentes ilimitados, IA local com Ollama, código-fonte incluso e até 60% de desconto em integrações.
            </p>
          </div>
          <a
            href="https://wa.me/5511947880561?text=Quero+saber+sobre+Enterprise"
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 flex items-center gap-2 text-sm font-semibold py-3 px-6 rounded-full bg-[#1D1D1F] text-white hover:bg-zinc-800 transition-all"
          >
            <ChatCircleDots size={15} weight="fill" />
            Agendar no WhatsApp
          </a>
        </div>
      </div>
    </section>
  )
}

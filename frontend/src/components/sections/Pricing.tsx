import { useState } from 'react'
import { Check, ChatCircleDots } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'

// Visible plan changes based on billing toggle
const MONTHLY_PLAN = {
  name: 'CRM Profissional',
  slug: 'professional',
  price: 'R$ 150',
  period: '/mês',
  sub: 'Tudo que sua equipe precisa para vender mais',
  features: [
    'Contatos ilimitados',
    '5 agentes WhatsApp com IA + RAG',
    'Pipeline Kanban completo',
    'Takeover humano em tempo real',
    'Templates DOCX + geração de PDF',
    'Contratos, estoque e premissas',
    'Dashboard & analytics',
    'Até 15 usuários',
    'Suporte prioritário',
  ],
  badge: 'Mensal',
  highlight: true,
}

const ANNUAL_PLAN = {
  name: 'CRM Profissional',
  slug: 'professional-annual',
  price: 'R$ 120',
  period: '/mês',
  sub: 'Cobrado anualmente — R$ 1.440/ano',
  savings: 'Economia de R$ 360 no ano',
  features: [
    'Tudo do plano mensal',
    'Economia de 20%',
    'Onboarding personalizado',
    'Relatórios avançados',
    'Acesso antecipado a novos recursos',
    'Suporte com SLA garantido',
  ],
  badge: 'Anual · Mais econômico',
  highlight: true,
}

export default function Pricing() {
  const [annual, setAnnual] = useState(false)

  const plan = annual ? ANNUAL_PLAN : MONTHLY_PLAN

  return (
    <section className="bg-white py-28 px-6" id="planos">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12 fade-in">
          <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-[0.2em] mb-4">Planos</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-[#1D1D1F] mb-4">
            Simples. Transparente.
          </h2>
          <p className="text-lg text-zinc-500 mb-8">14 dias grátis. Sem cartão de crédito. Cancele quando quiser.</p>

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
              <span className="text-[10px] font-bold bg-[#0ABAB5] text-white px-2 py-0.5 rounded-full">-20%</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
          {/* Main plan card */}
          <div
            key={plan.name + plan.badge}
            className="lg:col-span-2 fade-in relative bg-[#1D1D1F] text-white rounded-2xl p-8 glow-featured flex flex-col"
          >
            {plan.badge && (
              <span className="absolute -top-3.5 left-8 bg-[#0ABAB5] text-white text-xs font-bold px-4 py-1 rounded-full whitespace-nowrap shadow-lg shadow-[#0ABAB5]/30">
                {plan.badge}
              </span>
            )}

            <div className="mb-6">
              <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wide mb-3">{plan.name}</p>
              <div className="flex items-end gap-1 mb-1">
                <span className="text-5xl font-bold tracking-tight text-white">{plan.price}</span>
                <span className="text-base text-zinc-400 mb-2">{plan.period}</span>
              </div>
              {annual && 'savings' in plan && (
                <p className="text-sm font-semibold text-[#0ABAB5] mb-1">{(plan as typeof ANNUAL_PLAN).savings}</p>
              )}
              <p className="text-sm text-zinc-400">{plan.sub}</p>
            </div>

            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mb-8 flex-1">
              {plan.features.map(f => (
                <li key={f} className="flex items-start gap-2.5 text-sm">
                  <Check size={14} weight="bold" className="text-[#0ABAB5] shrink-0 mt-0.5" />
                  <span className="text-zinc-300">{f}</span>
                </li>
              ))}
            </ul>

            <Link
              to={`/auth/signup?plan=${plan.slug}`}
              className="block text-center font-semibold py-3.5 rounded-full text-sm bg-[#0ABAB5] text-white hover:bg-[#089B97] hover:shadow-[0_6px_24px_rgba(10,186,181,0.45)] transition-all active:scale-[0.97]"
            >
              Começar 14 dias grátis
            </Link>
          </div>

          {/* Consultation card */}
          <div className="fade-in flex flex-col gap-4" style={{ transitionDelay: '0.1s' }}>
            {/* Basic */}
            <div className="flex-1 bg-white border border-zinc-200 rounded-2xl p-6 card-lift flex flex-col">
              <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wide mb-2">Básico</p>
              <p className="text-2xl font-bold text-[#1D1D1F] mb-1">R$ {annual ? '80' : '98'}<span className="text-sm font-normal text-zinc-400">/mês</span></p>
              <p className="text-xs text-zinc-400 mb-4">Para pequenos times e freelancers</p>
              <ul className="space-y-2 mb-5 flex-1">
                {['Até 500 contatos', '1 agente WhatsApp', 'Pipeline básico', '2 usuários'].map(f => (
                  <li key={f} className="flex items-center gap-2 text-xs text-zinc-500">
                    <Check size={11} weight="bold" className="text-[#0ABAB5] shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                to="/auth/signup?plan=basic"
                className="block text-center text-xs font-semibold py-2.5 rounded-full border border-zinc-200 text-zinc-600 hover:bg-zinc-50 hover:border-zinc-300 transition-all"
              >
                Começar grátis
              </Link>
            </div>

            {/* White-label */}
            <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-6 flex flex-col">
              <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-wide mb-2">White-Label & Avançado</p>
              <p className="text-lg font-bold text-white mb-1">Sob consulta</p>
              <p className="text-xs text-zinc-500 mb-4">CRM com sua marca, agentes ilimitados, múltiplos tenants e SLA dedicado.</p>
              <a
                href="https://wa.me/5511947880561"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-1.5 text-xs font-semibold py-2.5 rounded-full bg-[#0ABAB5]/10 text-[#0ABAB5] border border-[#0ABAB5]/20 hover:bg-[#0ABAB5]/20 transition-all"
              >
                <ChatCircleDots size={13} weight="fill" />
                Falar com a equipe
              </a>
            </div>
          </div>
        </div>

        <p className="text-center text-sm text-zinc-400 mt-10 fade-in">
          Precisa de algo diferente? <a href="https://wa.me/5511947880561" className="text-[#0ABAB5] hover:underline">Fale com nossa equipe</a> — criamos planos customizados.
        </p>
      </div>
    </section>
  )
}

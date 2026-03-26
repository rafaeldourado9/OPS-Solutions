import { useState } from 'react'
import { ArrowRight } from '@phosphor-icons/react'

const TABS = ['Pipeline', 'Conversas', 'Relatórios']

const COLUMNS = [
  {
    title: 'Novos Leads',
    color: 'bg-zinc-100 text-zinc-600',
    cards: [
      { name: 'Beatriz Fontes', company: 'Luminar Tech', value: 'R$ 24.800', initials: 'BF', color: '#7C3AED' },
      { name: 'Caio Drummond', company: 'Vortex Infra', value: 'R$ 8.200', initials: 'CD', color: '#2563EB' },
      { name: 'Isabela Cruz', company: 'AxisPrime', value: 'R$ 16.500', initials: 'IC', color: '#DC2626' },
    ],
  },
  {
    title: 'Qualificados',
    color: 'bg-blue-50 text-blue-600',
    cards: [
      { name: 'Rodrigo Matos', company: 'ClearBuild', value: 'R$ 42.000', initials: 'RM', color: '#0891B2' },
      { name: 'Fernanda Leal', company: 'NovaCore', value: 'R$ 19.750', initials: 'FL', color: '#059669' },
    ],
  },
  {
    title: 'Proposta Enviada',
    color: 'bg-amber-50 text-amber-600',
    cards: [
      { name: 'Thiago Bastos', company: 'PulseRetail', value: 'R$ 67.300', initials: 'TB', color: '#D97706' },
      { name: 'Mariana Vaz', company: 'FluxLogix', value: 'R$ 31.000', initials: 'MV', color: '#9333EA' },
    ],
  },
  {
    title: 'Fechados',
    color: 'bg-[#0ABAB5]/10 text-[#089B97]',
    cards: [
      { name: 'Lucas Pinheiro', company: 'Zenith Cloud', value: 'R$ 89.900', initials: 'LP', color: '#0ABAB5', won: true },
    ],
  },
]

type Card = { name: string; company: string; value: string; initials: string; color: string; won?: boolean }

export default function CRMShowcase() {
  const [activeTab, setActiveTab] = useState(0)

  return (
    <section className="bg-[#F5F5F7] py-28 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="max-w-2xl mb-14 fade-in">
          <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-[0.2em] mb-4">OPS CRM</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-[#1D1D1F] leading-tight mb-5">
            O CRM que sua equipe vai realmente usar.
          </h2>
          <p className="text-lg text-zinc-500 leading-relaxed">
            Pipeline visual, automações que economizam 10 horas por semana e IA que prevê quais leads vão converter.
          </p>
          <a href="#" className="inline-flex items-center gap-1.5 text-[#0ABAB5] font-semibold mt-6 hover:gap-3 transition-all text-sm group">
            Conhecer o CRM
            <ArrowRight size={14} weight="bold" className="group-hover:translate-x-0.5 transition-transform" />
          </a>
        </div>

        {/* Mockup */}
        <div
          className="fade-in bg-white rounded-3xl shadow-[0_40px_100px_-20px_rgba(0,0,0,0.14)] overflow-hidden border border-zinc-100/80"
          style={{
            transform: 'perspective(1400px) rotateY(-1.5deg) rotateX(1deg)',
            transition: 'transform 0.7s cubic-bezier(0.16,1,0.3,1)',
          }}
          onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.transform = 'perspective(1400px) rotateY(0) rotateX(0)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.transform = 'perspective(1400px) rotateY(-1.5deg) rotateX(1deg)' }}
        >
          {/* Window bar */}
          <div className="flex items-center gap-2 px-5 py-3.5 bg-zinc-50/90 border-b border-zinc-100">
            <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
            <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
            <span className="w-3 h-3 rounded-full bg-[#28C840]" />
            <span className="ml-4 text-xs font-medium text-zinc-400">OPS CRM — Pipeline de Vendas</span>
            {/* Live indicator */}
            <div className="ml-auto flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="ping-ring absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-50" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
              </span>
              <span className="text-xs text-zinc-400">Ao vivo</span>
            </div>
          </div>

          {/* Sub-tabs (Helena CRM inspired) */}
          <div className="flex items-center gap-1 px-5 py-2.5 border-b border-zinc-100 bg-white">
            {TABS.map((tab, i) => (
              <button
                key={tab}
                onClick={() => setActiveTab(i)}
                className={`text-xs font-semibold px-3.5 py-1.5 rounded-lg transition-all ${
                  activeTab === i
                    ? 'bg-[#0ABAB5]/10 text-[#0ABAB5]'
                    : 'text-zinc-400 hover:text-zinc-600 hover:bg-zinc-50'
                }`}
              >
                {tab}
              </button>
            ))}
            <div className="ml-auto flex items-center gap-2">
              <div className="text-xs text-zinc-400 bg-zinc-50 border border-zinc-100 rounded-lg px-3 py-1.5">
                Mar 2026
              </div>
              <div className="w-7 h-7 rounded-lg bg-[#0ABAB5] flex items-center justify-center">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M6 2v8M2 6h8" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              </div>
            </div>
          </div>

          {/* Kanban */}
          <div className="p-5 overflow-x-auto bg-[#FAFAFA]">
            <div className="grid grid-cols-4 gap-4 min-w-[700px]">
              {COLUMNS.map(col => (
                <div key={col.title} className="group">
                  <div className="flex items-center justify-between mb-3">
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${col.color}`}>{col.title}</span>
                    <span className="text-xs text-zinc-400 font-mono">{col.cards.length}</span>
                  </div>
                  <div className="space-y-2.5">
                    {col.cards.map((card: Card) => (
                      <div
                        key={card.name}
                        className={`rounded-xl p-3.5 border transition-all hover:shadow-md cursor-pointer ${
                          card.won
                            ? 'bg-[#0ABAB5]/5 border-[#0ABAB5]/25'
                            : 'bg-white border-zinc-100 hover:border-zinc-200'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <div
                            className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[9px] font-bold shrink-0"
                            style={{ background: card.color }}
                          >
                            {card.initials}
                          </div>
                          <div className="min-w-0">
                            <p className="text-xs font-semibold text-[#1D1D1F] leading-tight truncate">{card.name}</p>
                            <p className="text-[10px] text-zinc-400 truncate">{card.company}</p>
                          </div>
                        </div>
                        <p className={`text-sm font-bold font-mono ${card.won ? 'text-[#089B97]' : 'text-zinc-700'}`}>
                          {card.value}
                        </p>
                      </div>
                    ))}
                    {/* Add card hint */}
                    <div className="rounded-xl border border-dashed border-zinc-200 p-3 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer hover:border-[#0ABAB5]/40">
                      <span className="text-xs text-zinc-400">+ Novo card</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

import { useEffect, useRef, useState, useCallback } from 'react'
import { Check, ArrowRight } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'

// ─── Feature definitions ────────────────────────────────────────────────────

const FEATURES = [
  {
    tag: 'Dashboard',
    title: 'Visão total do negócio.\nEm tempo real.',
    desc: 'KPIs, receita e pipeline reunidos num único painel. Tome decisões baseadas em dados reais — não em achismos.',
    bullets: ['Métricas ao vivo com delta vs. mês anterior', 'Gráfico de receita por período', 'Feed de atividade da equipe'],
  },
  {
    tag: 'Pipeline de Leads',
    title: 'Nenhum negócio cai\nno esquecimento.',
    desc: 'Kanban visual com arrastar e soltar. Cada lead tem valor, empresa e próxima ação — tudo visível numa relance.',
    bullets: ['Estágios configuráveis por nicho', 'Valor total por coluna atualizado ao vivo', 'Alerta automático de inatividade'],
  },
  {
    tag: 'Conversas & Takeover',
    title: 'Assumir o atendimento\nem um clique.',
    desc: 'Quando o agente de IA precisa de reforço, você entra direto no CRM — sem trocar de app, sem perder contexto.',
    bullets: ['Interface nativa estilo WhatsApp', 'Histórico completo da conversa', 'Devolve ao agente quando encerrar'],
  },
]

// ─── Nav sidebar icons ──────────────────────────────────────────────────────

const NAV_PATHS = [
  'M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z',
  'M4 6h16M4 12h8M4 18h12',
  'M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M12 7a4 4 0 110 8 4 4 0 010-8z',
  'M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z',
  'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
]

function AppSidebar({ activeIdx }: { activeIdx: number }) {
  return (
    <div className="w-[50px] bg-[#F8F9FB] border-r border-zinc-100 flex flex-col items-center py-3.5 gap-2.5 shrink-0">
      <div className="w-7 h-7 bg-[#0ABAB5] rounded-lg flex items-center justify-center mb-1.5">
        <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
          <polygon points="7,0.5 13,4 13,10 7,13.5 1,10 1,4" stroke="white" strokeWidth="1.3" fill="none"/>
          <circle cx="7" cy="7" r="1.5" fill="white"/>
        </svg>
      </div>
      {NAV_PATHS.map((path, i) => (
        <div
          key={i}
          className={`w-7 h-7 rounded-xl flex items-center justify-center cursor-pointer transition-all ${
            i === activeIdx ? 'bg-[#0ABAB5]/15 shadow-sm' : 'hover:bg-zinc-200/70'
          }`}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d={path} stroke={i === activeIdx ? '#0ABAB5' : '#A1A1AA'} strokeWidth="1.7" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      ))}
    </div>
  )
}

// ─── Screen 1: Dashboard ────────────────────────────────────────────────────

const CHART_DATA = [
  { m: 'Out', v: 48 }, { m: 'Nov', v: 55 }, { m: 'Dez', v: 71 },
  { m: 'Jan', v: 63 }, { m: 'Fev', v: 79 }, { m: 'Mar', v: 87 },
]
const CHART_MAX = 87

const KPIS = [
  { label: 'Leads ativos', val: '143', trend: '+12%', up: true },
  { label: 'Receita mês', val: 'R$87k', trend: '+23%', up: true },
  { label: 'Taxa conv.', val: '34,7%', trend: '-2%', up: false },
  { label: 'Propostas', val: '12', trend: '+4', up: true },
]

const ACTIVITY = [
  { init: 'BF', name: 'Beatriz Fontes', action: 'Proposta enviada', val: 'R$24.8k', c: '#7C3AED' },
  { init: 'LP', name: 'Lucas Pinheiro', action: 'Lead fechado ✓', val: 'R$89.9k', c: '#0ABAB5' },
  { init: 'TB', name: 'Thiago Bastos', action: 'Reunião agendada', val: 'R$67.3k', c: '#D97706' },
]

function DashboardScreen() {
  return (
    <div className="flex h-full text-[#1D1D1F]">
      <AppSidebar activeIdx={0} />
      <div className="flex-1 overflow-hidden bg-[#F8F9FB] flex flex-col min-w-0">
        {/* Top bar */}
        <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-zinc-100">
          <div>
            <p className="text-[9px] text-zinc-400 leading-none mb-0.5">OPS CRM</p>
            <p className="text-sm font-bold">Dashboard</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-1.5 bg-zinc-50 border border-zinc-100 rounded-lg px-2.5 py-1.5 text-[10px] text-zinc-400">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/><path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
              Buscar...
            </div>
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#0ABAB5] to-[#089B97] flex items-center justify-center text-white text-[8px] font-bold">RF</div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden p-3 flex flex-col gap-3">
          {/* KPIs */}
          <div className="grid grid-cols-4 gap-2">
            {KPIS.map(k => (
              <div key={k.label} className="bg-white rounded-xl p-3 border border-zinc-100 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
                <p className="text-[9px] text-zinc-400 mb-1 leading-tight">{k.label}</p>
                <p className="text-base font-bold tracking-tight leading-none mb-1">{k.val}</p>
                <p className={`text-[9px] font-semibold ${k.up ? 'text-emerald-500' : 'text-red-400'}`}>{k.trend}</p>
              </div>
            ))}
          </div>

          {/* Chart + Activity */}
          <div className="flex gap-2 flex-1 min-h-0">
            {/* Chart */}
            <div className="flex-1 bg-white rounded-xl border border-zinc-100 p-3 shadow-[0_1px_3px_rgba(0,0,0,0.04)] flex flex-col min-w-0">
              <div className="flex items-center justify-between mb-2.5">
                <p className="text-[10px] font-semibold">Receita — últimos 6 meses</p>
                <span className="text-[9px] text-zinc-400 bg-zinc-50 border border-zinc-100 rounded px-1.5 py-0.5">R$ mil</span>
              </div>
              <div className="flex-1 flex items-end gap-1.5 pb-1">
                {CHART_DATA.map((d, i) => (
                  <div key={d.m} className="flex-1 flex flex-col items-center gap-1 min-w-0">
                    <span className="text-[7px] text-zinc-500 font-mono">{d.v}</span>
                    <div
                      className={`w-full rounded-t-md transition-all ${i === 5 ? 'bg-[#0ABAB5]' : 'bg-zinc-100'}`}
                      style={{ height: `${(d.v / CHART_MAX) * 60}px` }}
                    />
                    <span className="text-[7px] text-zinc-400">{d.m}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Activity */}
            <div className="w-[130px] bg-white rounded-xl border border-zinc-100 p-3 shadow-[0_1px_3px_rgba(0,0,0,0.04)] shrink-0">
              <p className="text-[10px] font-semibold mb-2.5">Atividade recente</p>
              <div className="space-y-2.5">
                {ACTIVITY.map(a => (
                  <div key={a.name} className="flex items-start gap-1.5">
                    <div className="w-5 h-5 rounded-full flex items-center justify-center text-white text-[7px] font-bold shrink-0 mt-0.5" style={{ background: a.c }}>{a.init}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[9px] font-semibold truncate leading-tight">{a.name}</p>
                      <p className="text-[8px] text-zinc-400 truncate">{a.action}</p>
                      <p className="text-[8px] font-mono font-bold text-zinc-500 mt-0.5">{a.val}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Screen 2: Pipeline ─────────────────────────────────────────────────────

const PIPELINE_COLS = [
  {
    title: 'Novos', color: 'bg-zinc-100 text-zinc-600',
    total: 'R$ 49.5k',
    cards: [
      { init: 'BF', name: 'Beatriz Fontes', co: 'Luminar Tech', val: 'R$ 24.800', c: '#7C3AED' },
      { init: 'CD', name: 'Caio Drummond', co: 'Vortex Infra', val: 'R$ 8.200', c: '#2563EB' },
      { init: 'IC', name: 'Isabela Cruz', co: 'AxisPrime', val: 'R$ 16.500', c: '#DC2626' },
    ],
  },
  {
    title: 'Qualificados', color: 'bg-blue-50 text-blue-600',
    total: 'R$ 61.7k',
    cards: [
      { init: 'RM', name: 'Rodrigo Matos', co: 'ClearBuild', val: 'R$ 42.000', c: '#0891B2' },
      { init: 'FL', name: 'Fernanda Leal', co: 'NovaCore', val: 'R$ 19.750', c: '#059669' },
    ],
  },
  {
    title: 'Proposta', color: 'bg-amber-50 text-amber-600',
    total: 'R$ 98.3k',
    cards: [
      { init: 'TB', name: 'Thiago Bastos', co: 'PulseRetail', val: 'R$ 67.300', c: '#D97706' },
      { init: 'MV', name: 'Mariana Vaz', co: 'FluxLogix', val: 'R$ 31.000', c: '#9333EA' },
    ],
  },
  {
    title: 'Fechados', color: 'bg-[#0ABAB5]/10 text-[#089B97]',
    total: 'R$ 89.9k',
    cards: [
      { init: 'LP', name: 'Lucas Pinheiro', co: 'Zenith Cloud', val: 'R$ 89.900', c: '#0ABAB5', won: true },
    ],
  },
]

function PipelineScreen() {
  return (
    <div className="flex h-full text-[#1D1D1F]">
      <AppSidebar activeIdx={1} />
      <div className="flex-1 overflow-hidden bg-[#F8F9FB] flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-zinc-100 shrink-0">
          <div>
            <p className="text-[9px] text-zinc-400 leading-none mb-0.5">Leads</p>
            <p className="text-sm font-bold">Pipeline de Vendas</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[9px] text-zinc-400 bg-zinc-50 border border-zinc-100 rounded-lg px-2 py-1">Mar 2026</span>
            <div className="w-6 h-6 rounded-lg bg-[#0ABAB5] flex items-center justify-center cursor-pointer">
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M5 1v8M1 5h8" stroke="white" strokeWidth="1.5" strokeLinecap="round"/></svg>
            </div>
          </div>
        </div>

        {/* Kanban */}
        <div className="flex-1 overflow-auto p-3">
          <div className="flex gap-2.5 h-full min-w-[500px]">
            {PIPELINE_COLS.map(col => (
              <div key={col.title} className="flex-1 flex flex-col gap-2 min-w-0">
                <div className="flex items-center justify-between">
                  <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${col.color}`}>{col.title}</span>
                  <span className="text-[9px] font-mono text-zinc-400">{col.cards.length}</span>
                </div>
                <p className="text-[9px] font-semibold text-zinc-500 font-mono px-0.5">{col.total}</p>
                <div className="space-y-1.5 flex-1">
                  {col.cards.map((card: any) => (
                    <div
                      key={card.name}
                      className={`rounded-xl p-2.5 border cursor-pointer transition-all hover:shadow-md ${
                        card.won ? 'bg-[#0ABAB5]/6 border-[#0ABAB5]/20' : 'bg-white border-zinc-100 hover:border-zinc-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]'
                      }`}
                    >
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <div className="w-5 h-5 rounded-full flex items-center justify-center text-white text-[7px] font-bold shrink-0" style={{ background: card.c }}>{card.init}</div>
                        <div className="min-w-0 flex-1">
                          <p className="text-[9px] font-bold truncate leading-tight">{card.name}</p>
                          <p className="text-[8px] text-zinc-400 truncate">{card.co}</p>
                        </div>
                      </div>
                      <p className={`text-[10px] font-bold font-mono ${card.won ? 'text-[#089B97]' : 'text-zinc-600'}`}>{card.val}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Screen 3: Conversations ─────────────────────────────────────────────────

const CONV_LIST = [
  { init: 'BF', name: 'Beatriz Fontes', preview: 'Qual o prazo de instalação?', time: '09:41', unread: 2, active: true, c: '#7C3AED' },
  { init: 'RM', name: 'Rodrigo Matos', preview: 'Obrigado pela proposta!', time: '09:23', unread: 0, active: false, c: '#0891B2' },
  { init: 'TB', name: 'Thiago Bastos', preview: 'Pode ser sexta?', time: '08:55', unread: 0, active: false, c: '#D97706' },
  { init: 'FL', name: 'Fernanda Leal', preview: 'Vou verificar com o financeiro', time: 'Ontem', unread: 0, active: false, c: '#059669' },
]

const CONV_MSGS = [
  { from: 'user', text: 'Oi! Gostaria de um orçamento para 50 colaboradores.', time: '09:31' },
  { from: 'agent', text: 'Olá, Beatriz! Para 50 usuários o plano Pro é ideal — R$ 387/mês com todos os recursos. Posso enviar a proposta formal?', time: '09:32' },
  { from: 'user', text: 'Sim! E qual o prazo de instalação?', time: '09:41' },
]

function ConversationsScreen() {
  return (
    <div className="flex h-full text-[#1D1D1F]">
      <AppSidebar activeIdx={3} />

      {/* Conversation list */}
      <div className="w-[148px] bg-white border-r border-zinc-100 flex flex-col shrink-0">
        <div className="px-3 py-3 border-b border-zinc-100">
          <p className="text-[10px] font-bold">Conversas</p>
        </div>
        <div className="flex-1 overflow-auto divide-y divide-zinc-50">
          {CONV_LIST.map(c => (
            <div
              key={c.name}
              className={`px-2.5 py-2 cursor-pointer transition-colors ${
                c.active ? 'bg-[#0ABAB5]/6 border-l-2 border-l-[#0ABAB5]' : 'hover:bg-zinc-50'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <div className="w-5 h-5 rounded-full flex items-center justify-center text-white text-[7px] font-bold shrink-0" style={{ background: c.c }}>{c.init}</div>
                <p className={`text-[9px] font-semibold truncate flex-1 leading-tight ${c.active ? 'text-[#0ABAB5]' : ''}`}>{c.name}</p>
                <span className="text-[7px] text-zinc-400 shrink-0">{c.time}</span>
              </div>
              <div className="flex items-center justify-between pl-6">
                <p className="text-[8px] text-zinc-400 truncate flex-1">{c.preview}</p>
                {c.unread > 0 && (
                  <span className="w-3.5 h-3.5 bg-[#0ABAB5] text-white text-[7px] font-bold rounded-full flex items-center justify-center shrink-0 ml-1">{c.unread}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col bg-[#F8F9FB] min-w-0">
        {/* Header */}
        <div className="flex items-center gap-2.5 px-3 py-2.5 bg-white border-b border-zinc-100 shrink-0">
          <div className="w-6 h-6 rounded-full bg-[#7C3AED] flex items-center justify-center text-white text-[8px] font-bold">BF</div>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-bold truncate">Beatriz Fontes</p>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <p className="text-[8px] text-emerald-500">Online agora</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[8px] text-zinc-400 bg-zinc-100 rounded px-1.5 py-0.5">Agente ativo</span>
            <button className="text-[8px] font-bold bg-[#0ABAB5] text-white px-2 py-1 rounded-md whitespace-nowrap">
              Assumir
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-hidden px-3 py-3 space-y-2 flex flex-col justify-end">
          {CONV_MSGS.map((msg, i) => (
            <div key={i} className={`flex ${msg.from === 'agent' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[78%] rounded-2xl px-2.5 py-1.5 text-[9px] leading-relaxed ${
                  msg.from === 'agent'
                    ? 'bg-[#0ABAB5]/10 text-[#1D1D1F] rounded-br-sm'
                    : 'bg-white border border-zinc-100 text-[#1D1D1F] rounded-bl-sm shadow-sm'
                }`}
              >
                {msg.text}
                <span className="text-[7px] text-zinc-400 ml-1.5 inline-block">{msg.time}</span>
              </div>
            </div>
          ))}
          {/* Typing indicator */}
          <div className="flex justify-end">
            <div className="bg-[#0ABAB5]/10 rounded-2xl rounded-br-sm px-3 py-2 flex items-center gap-1">
              {[0, 1, 2].map(i => (
                <span key={i} className="typing-dot w-1 h-1 bg-[#0ABAB5] rounded-full" />
              ))}
            </div>
          </div>
        </div>

        {/* Input */}
        <div className="px-3 pb-3 shrink-0">
          <div className="bg-white border border-zinc-100 rounded-xl px-3 py-2 flex items-center gap-2 shadow-sm">
            <span className="text-[9px] text-zinc-400 flex-1">Escreva uma mensagem...</span>
            <div className="w-5 h-5 bg-[#0ABAB5] rounded-lg flex items-center justify-center">
              <svg width="9" height="9" viewBox="0 0 9 9" fill="none"><path d="M8 4.5H1M4.5 1l3.5 3.5L4.5 8" stroke="white" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────

const SCREENS = [DashboardScreen, PipelineScreen, ConversationsScreen]

export default function CRMShowcase() {
  const containerRef = useRef<HTMLDivElement>(null)
  const rafRef = useRef<number>(0)
  const [progress, setProgress] = useState(0)
  const [isMobile, setIsMobile] = useState(false)

  const activeIndex = progress < 0.33 ? 0 : progress < 0.66 ? 1 : 2

  const onScroll = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    rafRef.current = requestAnimationFrame(() => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const scrollable = rect.height - window.innerHeight
      const scrolled = -rect.top
      setProgress(Math.max(0, Math.min(1, scrolled / scrollable)))
    })
  }, [])

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 1024)
    checkMobile()
    window.addEventListener('resize', checkMobile, { passive: true })
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      window.removeEventListener('resize', checkMobile)
      window.removeEventListener('scroll', onScroll)
      cancelAnimationFrame(rafRef.current)
    }
  }, [onScroll])

  // ── Mobile: stacked sections ──────────────────────────────────────────────
  if (isMobile) {
    return (
      <section className="bg-[#F5F5F7] py-24 px-6">
        <div className="max-w-2xl mx-auto space-y-24">
          {FEATURES.map((f, i) => {
            const Screen = SCREENS[i]
            return (
              <div key={f.tag} className="fade-in">
                <p className="text-xs font-bold text-[#0ABAB5] uppercase tracking-[0.18em] mb-4">{f.tag}</p>
                <h2 className="text-3xl font-bold tracking-tight text-[#1D1D1F] leading-tight mb-4 whitespace-pre-line">{f.title}</h2>
                <p className="text-base text-zinc-500 leading-relaxed mb-6">{f.desc}</p>
                <ul className="space-y-2.5 mb-10">
                  {f.bullets.map(b => (
                    <li key={b} className="flex items-start gap-2.5 text-sm text-zinc-600">
                      <Check size={14} weight="bold" className="text-[#0ABAB5] shrink-0 mt-0.5" />
                      {b}
                    </li>
                  ))}
                </ul>
                {/* Mockup */}
                <div className="rounded-2xl overflow-hidden shadow-[0_20px_60px_rgba(0,0,0,0.12)] border border-zinc-200/60">
                  <div className="flex items-center gap-1.5 px-4 py-2.5 bg-zinc-50 border-b border-zinc-100">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#FF5F57]" />
                    <span className="w-2.5 h-2.5 rounded-full bg-[#FEBC2E]" />
                    <span className="w-2.5 h-2.5 rounded-full bg-[#28C840]" />
                    <span className="ml-3 text-[10px] font-medium text-zinc-400">OPS CRM — {f.tag}</span>
                  </div>
                  <div className="h-[340px]">
                    <Screen />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </section>
    )
  }

  // ── Desktop: scroll-pinned Apple-style ────────────────────────────────────
  return (
    <div ref={containerRef} className="relative" style={{ height: '320vh' }}>
      <div className="sticky top-0 h-screen overflow-hidden bg-[#F5F5F7] flex items-center">

        {/* Background accent — subtle gradient that shifts with active feature */}
        <div
          className="absolute inset-0 pointer-events-none transition-opacity duration-700"
          style={{
            background: 'radial-gradient(ellipse 60% 50% at 75% 50%, rgba(10,186,181,0.07) 0%, transparent 60%)',
            opacity: 1,
          }}
        />

        <div className="max-w-7xl mx-auto w-full px-8 lg:px-12 grid grid-cols-[1fr_1.3fr] gap-12 xl:gap-20 items-center relative z-10">

          {/* ── Left: Feature text ──────────────────────────────────────────── */}
          <div className="relative min-h-[380px] flex flex-col justify-center">
            {FEATURES.map((f, i) => {
              const isActive = i === activeIndex
              const isPast = i < activeIndex
              return (
                <div
                  key={f.tag}
                  className="absolute inset-0 flex flex-col justify-center"
                  style={{
                    opacity: isActive ? 1 : 0,
                    transform: isActive
                      ? 'translateY(0)'
                      : isPast
                      ? 'translateY(-28px)'
                      : 'translateY(28px)',
                    transition: 'opacity 0.65s cubic-bezier(0.16,1,0.3,1), transform 0.65s cubic-bezier(0.16,1,0.3,1)',
                    pointerEvents: isActive ? 'auto' : 'none',
                  }}
                >
                  <p className="text-xs font-bold text-[#0ABAB5] uppercase tracking-[0.2em] mb-5">{f.tag}</p>
                  <h2 className="text-4xl xl:text-5xl font-bold tracking-tight text-[#1D1D1F] leading-[1.08] mb-5 whitespace-pre-line">
                    {f.title}
                  </h2>
                  <p className="text-lg text-zinc-500 leading-relaxed mb-8 max-w-md">{f.desc}</p>
                  <ul className="space-y-3 mb-10">
                    {f.bullets.map((b, bi) => (
                      <li
                        key={b}
                        className="flex items-start gap-3 text-sm text-zinc-600"
                        style={{
                          opacity: isActive ? 1 : 0,
                          transform: isActive ? 'translateX(0)' : 'translateX(-12px)',
                          transition: `opacity 0.5s cubic-bezier(0.16,1,0.3,1) ${bi * 0.07 + 0.15}s, transform 0.5s cubic-bezier(0.16,1,0.3,1) ${bi * 0.07 + 0.15}s`,
                        }}
                      >
                        <Check size={14} weight="bold" className="text-[#0ABAB5] shrink-0 mt-0.5" />
                        {b}
                      </li>
                    ))}
                  </ul>
                  <Link
                    to="/auth/signup"
                    className="inline-flex items-center gap-2 text-sm font-semibold text-[#0ABAB5] hover:gap-3 transition-all group"
                  >
                    Começar grátis
                    <ArrowRight size={13} weight="bold" className="group-hover:translate-x-0.5 transition-transform" />
                  </Link>
                </div>
              )
            })}

            {/* Progress dots */}
            <div className="absolute -bottom-8 left-0 flex items-center gap-2.5">
              {FEATURES.map((_, i) => (
                <div
                  key={i}
                  className="rounded-full transition-all duration-500"
                  style={{
                    width: i === activeIndex ? 20 : 6,
                    height: 6,
                    background: i === activeIndex ? '#0ABAB5' : '#D4D4D8',
                  }}
                />
              ))}
              <span className="text-[10px] text-zinc-400 ml-1 font-mono">{activeIndex + 1} / {FEATURES.length}</span>
            </div>
          </div>

          {/* ── Right: CRM mockup ────────────────────────────────────────────── */}
          <div className="relative">
            {/* Ambient glow */}
            <div
              className="absolute -inset-8 rounded-3xl pointer-events-none transition-opacity duration-700"
              style={{
                background: 'radial-gradient(ellipse 70% 60% at 50% 55%, rgba(10,186,181,0.12) 0%, transparent 70%)',
                filter: 'blur(24px)',
              }}
            />

            {/* Browser window */}
            <div
              className="relative bg-white rounded-2xl overflow-hidden border border-zinc-200/70 shadow-[0_32px_80px_rgba(0,0,0,0.13),0_8px_20px_rgba(0,0,0,0.06)]"
              style={{ transform: 'perspective(1200px) rotateY(-2deg) rotateX(1.5deg)' }}
            >
              {/* Chrome */}
              <div className="flex items-center gap-2 px-4 py-2.5 bg-zinc-50 border-b border-zinc-100">
                <span className="w-2.5 h-2.5 rounded-full bg-[#FF5F57]" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#FEBC2E]" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#28C840]" />
                {/* URL bar */}
                <div className="flex-1 mx-3 bg-white border border-zinc-100 rounded-md px-3 py-1 flex items-center gap-2">
                  <svg width="9" height="10" viewBox="0 0 9 10" fill="none"><rect x="1" y="4" width="7" height="5.5" rx="1" stroke="#A1A1AA" strokeWidth="1"/><path d="M2.5 4V2.5a2 2 0 014 0V4" stroke="#A1A1AA" strokeWidth="1" strokeLinecap="round"/></svg>
                  <span className="text-[9px] text-zinc-400">app.ops.solutions/{['dashboard', 'leads', 'conversas'][activeIndex]}</span>
                </div>
                {/* Live pill */}
                <div className="flex items-center gap-1.5 shrink-0">
                  <span className="relative flex h-1.5 w-1.5">
                    <span className="ping-ring absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
                    <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  </span>
                  <span className="text-[9px] text-zinc-400">Ao vivo</span>
                </div>
              </div>

              {/* Screen content — all rendered, CSS controls visibility */}
              <div className="relative" style={{ height: 400 }}>
                {SCREENS.map((Screen, i) => (
                  <div
                    key={i}
                    className="absolute inset-0"
                    style={{
                      opacity: i === activeIndex ? 1 : 0,
                      transform: i === activeIndex
                        ? 'translateY(0) scale(1)'
                        : i < activeIndex
                        ? 'translateY(-16px) scale(0.99)'
                        : 'translateY(16px) scale(0.99)',
                      transition: 'opacity 0.55s cubic-bezier(0.16,1,0.3,1), transform 0.55s cubic-bezier(0.16,1,0.3,1)',
                      pointerEvents: i === activeIndex ? 'auto' : 'none',
                    }}
                  >
                    <Screen />
                  </div>
                ))}
              </div>
            </div>

            {/* Floating notifications — change with active screen */}
            {activeIndex === 0 && (
              <div
                className="absolute -top-4 -right-4 glass rounded-xl px-3.5 py-2.5 shadow-[0_8px_32px_rgba(0,0,0,0.1)] flex items-center gap-2.5 crm-float-in"
                key="notif-0"
              >
                <div className="w-7 h-7 bg-emerald-50 rounded-lg flex items-center justify-center">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke="#10B981" strokeWidth="2" fill="none"/></svg>
                </div>
                <div>
                  <p className="text-[10px] font-bold text-[#1D1D1F]">Receita bate recorde</p>
                  <p className="text-[9px] text-zinc-400">R$ 87k em março — +23%</p>
                </div>
              </div>
            )}
            {activeIndex === 1 && (
              <div
                className="absolute -top-4 -right-4 glass rounded-xl px-3.5 py-2.5 shadow-[0_8px_32px_rgba(0,0,0,0.1)] flex items-center gap-2.5 crm-float-in"
                key="notif-1"
              >
                <div className="w-7 h-7 bg-[#0ABAB5]/10 rounded-lg flex items-center justify-center">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="#0ABAB5" strokeWidth="2" fill="none"/></svg>
                </div>
                <div>
                  <p className="text-[10px] font-bold text-[#1D1D1F]">Lead fechado!</p>
                  <p className="text-[9px] text-zinc-400">Lucas Pinheiro — R$ 89.900</p>
                </div>
                <span className="w-1.5 h-1.5 bg-[#0ABAB5] rounded-full shrink-0" style={{ boxShadow: '0 0 6px rgba(10,186,181,0.7)' }} />
              </div>
            )}
            {activeIndex === 2 && (
              <div
                className="absolute -top-4 -right-4 glass rounded-xl px-3.5 py-2.5 shadow-[0_8px_32px_rgba(0,0,0,0.1)] flex items-center gap-2.5 crm-float-in"
                key="notif-2"
              >
                <div className="w-7 h-7 bg-violet-50 rounded-lg flex items-center justify-center text-[10px]">💬</div>
                <div>
                  <p className="text-[10px] font-bold text-[#1D1D1F]">Nova mensagem</p>
                  <p className="text-[9px] text-zinc-400">Beatriz Fontes · agora</p>
                </div>
                <span className="w-1.5 h-1.5 bg-violet-400 rounded-full shrink-0 animate-pulse" />
              </div>
            )}

            {/* Bottom floating metric */}
            <div className="float-reverse absolute -bottom-4 -left-4 glass-dark rounded-xl px-4 py-2.5 flex items-center gap-3 shadow-[0_8px_32px_rgba(0,0,0,0.25)]">
              <div>
                <p className="text-[9px] text-zinc-400">Pipeline total</p>
                <p className="text-sm font-bold text-white tracking-tight">R$ 299.450</p>
              </div>
              <div className="text-[10px] font-bold text-emerald-400 bg-emerald-400/15 px-2 py-0.5 rounded-full">+31%</div>
            </div>
          </div>
        </div>

        {/* Scroll cue (shows only at top) */}
        <div
          className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5 transition-opacity duration-500"
          style={{ opacity: progress < 0.04 ? 1 : 0 }}
        >
          <p className="text-[10px] text-zinc-400 font-medium tracking-wide">ROLE PARA EXPLORAR</p>
          <div className="w-5 h-8 border border-zinc-300 rounded-full flex items-start justify-center pt-1.5">
            <div className="w-1 h-2 bg-zinc-400 rounded-full animate-scroll-indicator" />
          </div>
        </div>
      </div>
    </div>
  )
}

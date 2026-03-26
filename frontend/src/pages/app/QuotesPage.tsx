import { useState } from 'react'
import { Plus, DotsThreeVertical, FileText, CurrencyDollar, ClockCounterClockwise, CheckCircle } from '@phosphor-icons/react'

type QuoteStatus = 'Aprovado' | 'Enviado' | 'Rascunho' | 'Rejeitado'
type FilterTab = 'Todos' | QuoteStatus

interface Quote {
  id: string
  cliente: string
  descricao: string
  data: string
  valor: number
  status: QuoteStatus
}

const QUOTES: Quote[] = [
  { id: '1', cliente: 'João Silva',    descricao: 'Instalação Solar 5kW',        data: '12/03/2026', valor: 18500, status: 'Aprovado' },
  { id: '2', cliente: 'Maria Costa',   descricao: 'Manutenção Preventiva',        data: '18/03/2026', valor: 4200,  status: 'Enviado'  },
  { id: '3', cliente: 'Pedro Almeida', descricao: 'Projeto Elétrico Comercial',   data: '20/03/2026', valor: 31000, status: 'Rascunho' },
  { id: '4', cliente: 'Ana Ferreira',  descricao: 'Revisão Sistema',              data: '22/03/2026', valor: 2800,  status: 'Rejeitado'},
  { id: '5', cliente: 'Carlos Souza',  descricao: 'Consultoria Energética',       data: '24/03/2026', valor: 7500,  status: 'Enviado'  },
]

const STATUS_STYLES: Record<QuoteStatus, string> = {
  Aprovado:  'bg-emerald-50 text-emerald-700 border border-emerald-100',
  Enviado:   'bg-blue-50 text-blue-700 border border-blue-100',
  Rascunho:  'bg-zinc-100 text-zinc-600 border border-zinc-200',
  Rejeitado: 'bg-red-50 text-red-700 border border-red-100',
}

function fmtVal(n: number) {
  if (n >= 1000) return 'R$ ' + (n / 1000).toFixed(1).replace('.', ',') + 'k'
  return 'R$ ' + n.toLocaleString('pt-BR')
}

const TABS: FilterTab[] = ['Todos', 'Rascunho', 'Enviado', 'Aprovado', 'Rejeitado']

export default function QuotesPage() {
  const [tab, setTab] = useState<FilterTab>('Todos')

  const filtered = tab === 'Todos' ? QUOTES : QUOTES.filter(q => q.status === tab)

  const total        = QUOTES.length
  const aguardando   = QUOTES.filter(q => q.status === 'Enviado').length
  const potencial    = QUOTES.filter(q => q.status !== 'Rejeitado').reduce((s, q) => s + q.valor, 0)

  return (
    <div className="p-4 md:p-6 space-y-5 pb-6">

      {/* Header */}
      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100 flex items-center justify-between">
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight">Orçamentos</h1>
        <button className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#09a8a3] text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95">
          <Plus size={15} weight="bold" />
          <span className="hidden sm:inline">Novo Orçamento</span>
          <span className="sm:hidden">Novo</span>
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-[#0ABAB5]/10 flex items-center justify-center mb-3">
            <FileText size={16} weight="duotone" className="text-[#0ABAB5]" />
          </div>
          <p className="text-xl font-bold text-[#1D1D1F] font-mono truncate">{total}</p>
          <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">Total de Orçamentos</p>
        </div>
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-blue-50 flex items-center justify-center mb-3">
            <ClockCounterClockwise size={16} weight="duotone" className="text-blue-500" />
          </div>
          <p className="text-xl font-bold text-[#1D1D1F] font-mono truncate">{aguardando}</p>
          <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">Aguardando Aprovação</p>
        </div>
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-emerald-50 flex items-center justify-center mb-3">
            <CurrencyDollar size={16} weight="duotone" className="text-emerald-600" />
          </div>
          <p className="text-xl font-bold text-[#1D1D1F] font-mono truncate">{fmtVal(potencial)}</p>
          <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">Receita Potencial</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-1.5 overflow-x-auto pb-0.5 scrollbar-none">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`shrink-0 text-[12px] font-semibold px-3.5 py-1.5 rounded-xl border transition-all ${
              tab === t
                ? 'bg-[#0ABAB5] text-white border-[#0ABAB5]'
                : 'bg-white text-zinc-500 border-zinc-200 hover:border-zinc-300'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 overflow-hidden">

        {/* Desktop header */}
        <div className="hidden md:grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3 border-b border-zinc-100 bg-zinc-50/60">
          {['Cliente', 'Descrição', 'Data', 'Valor', 'Status', ''].map(h => (
            <p key={h} className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">{h}</p>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className="flex flex-col items-center py-16 text-zinc-300">
            <FileText size={40} weight="duotone" />
            <p className="text-sm mt-2 text-zinc-400">Nenhum orçamento encontrado</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-100">
            {filtered.map(q => (
              <div key={q.id}>
                {/* Desktop row */}
                <div className="hidden md:grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3.5 items-center hover:bg-zinc-50/60 transition-colors group cursor-pointer">
                  <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{q.cliente}</p>
                  <p className="text-[13px] text-zinc-500 truncate">{q.descricao}</p>
                  <p className="text-[13px] text-zinc-500">{q.data}</p>
                  <p className="text-[13px] font-bold text-[#0ABAB5] font-mono">{fmtVal(q.valor)}</p>
                  <span className={`inline-flex text-[11px] font-semibold px-2 py-0.5 rounded-full w-fit ${STATUS_STYLES[q.status]}`}>
                    {q.status}
                  </span>
                  <button className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-all">
                    <DotsThreeVertical size={16} weight="bold" />
                  </button>
                </div>

                {/* Mobile card */}
                <div className="md:hidden p-4 active:bg-zinc-50 transition-colors cursor-pointer">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="min-w-0">
                      <p className="text-[14px] font-semibold text-[#1D1D1F] truncate">{q.cliente}</p>
                      <p className="text-[12px] text-zinc-400 truncate mt-0.5">{q.descricao}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${STATUS_STYLES[q.status]}`}>
                        {q.status}
                      </span>
                      <button className="p-1 rounded-lg hover:bg-zinc-100 text-zinc-400">
                        <DotsThreeVertical size={15} weight="bold" />
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-zinc-100">
                    <p className="text-[12px] text-zinc-400">{q.data}</p>
                    <p className="text-[14px] font-bold text-[#0ABAB5] font-mono">{fmtVal(q.valor)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Summary footer */}
      {filtered.length > 0 && (
        <div className="flex items-center justify-between px-1">
          <p className="text-[12px] text-zinc-400">{filtered.length} orçamento{filtered.length !== 1 ? 's' : ''}</p>
          <div className="flex items-center gap-1.5 text-[12px] text-emerald-600 font-semibold">
            <CheckCircle size={13} weight="fill" />
            {fmtVal(filtered.reduce((s, q) => s + q.valor, 0))} total
          </div>
        </div>
      )}
    </div>
  )
}

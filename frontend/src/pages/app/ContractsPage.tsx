import { useState } from 'react'
import { Plus, DotsThreeVertical, Handshake, WarningCircle, FileText, CurrencyDollar, Clock } from '@phosphor-icons/react'

type ContractStatus = 'Ativo' | 'Expirado' | 'Cancelado' | 'Rascunho'
type FilterTab = 'Todos' | ContractStatus

interface Contract {
  id: string
  cliente: string
  objeto: string
  inicio: string
  validade: string
  status: ContractStatus
  expiringSoon?: boolean
}

const CONTRACTS: Contract[] = [
  { id: '1', cliente: 'João Silva',   objeto: 'Manutenção Mensal Solar',   inicio: '01/01/2025', validade: '31/12/2025', status: 'Ativo'     },
  { id: '2', cliente: 'Maria Costa',  objeto: 'Suporte Técnico Anual',     inicio: '15/03/2024', validade: '15/03/2025', status: 'Expirado'  },
  { id: '3', cliente: 'Pedro Almeida',objeto: 'Projeto Elétrico',          inicio: '01/06/2025', validade: '31/05/2026', status: 'Ativo'     },
  { id: '4', cliente: 'Empresa XYZ',  objeto: 'Consultoria Energética',    inicio: '—',          validade: '—',          status: 'Rascunho'  },
  { id: '5', cliente: 'Ana Ferreira', objeto: 'Instalação Fotovoltaica',   inicio: '10/02/2025', validade: '10/04/2025', status: 'Ativo', expiringSoon: true },
  { id: '6', cliente: 'Carlos Lima',  objeto: 'Gestão de Energia',         inicio: '01/09/2024', validade: '01/09/2025', status: 'Cancelado' },
]

const STATUS_STYLES: Record<ContractStatus, string> = {
  Ativo:     'bg-emerald-50 text-emerald-700 border border-emerald-100',
  Expirado:  'bg-orange-50 text-orange-700 border border-orange-100',
  Cancelado: 'bg-red-50 text-red-700 border border-red-100',
  Rascunho:  'bg-zinc-100 text-zinc-600 border border-zinc-200',
}

const TABS: FilterTab[] = ['Todos', 'Ativo', 'Expirado', 'Cancelado', 'Rascunho']

export default function ContractsPage() {
  const [tab, setTab] = useState<FilterTab>('Todos')

  const filtered = tab === 'Todos' ? CONTRACTS : CONTRACTS.filter(c => c.status === tab)

  const ativos    = CONTRACTS.filter(c => c.status === 'Ativo').length
  const vencer    = CONTRACTS.filter(c => c.expiringSoon).length
  const totalVal  = 127000

  return (
    <div className="p-4 md:p-6 space-y-5 pb-6">

      {/* Sticky header */}
      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100 flex items-center justify-between">
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight">Contratos</h1>
        <button className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#09a8a3] text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95">
          <Plus size={15} weight="bold" />
          <span className="hidden sm:inline">Novo Contrato</span>
          <span className="sm:hidden">Novo</span>
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-emerald-50 flex items-center justify-center mb-3">
            <Handshake size={16} weight="duotone" className="text-emerald-600" />
          </div>
          <p className="text-xl font-bold text-[#1D1D1F] font-mono truncate">{ativos}</p>
          <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">Contratos Ativos</p>
        </div>
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-amber-50 flex items-center justify-center mb-3">
            <Clock size={16} weight="duotone" className="text-amber-600" />
          </div>
          <p className="text-xl font-bold text-amber-600 font-mono truncate">{vencer}</p>
          <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">A Vencer em 30 dias</p>
        </div>
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-[#0ABAB5]/10 flex items-center justify-center mb-3">
            <CurrencyDollar size={16} weight="duotone" className="text-[#0ABAB5]" />
          </div>
          <p className="text-xl font-bold text-[#1D1D1F] font-mono truncate">R$ {(totalVal / 1000).toFixed(0)}k</p>
          <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">Valor Total</p>
        </div>
      </div>

      {/* Filter tabs */}
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

      {/* Contract list */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 overflow-hidden">

        {/* Desktop header */}
        <div className="hidden md:grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3 border-b border-zinc-100 bg-zinc-50/60">
          {['Cliente', 'Objeto', 'Início', 'Validade', 'Status', ''].map(h => (
            <p key={h} className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">{h}</p>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className="flex flex-col items-center py-16 text-zinc-300">
            <FileText size={40} weight="duotone" />
            <p className="text-sm mt-2 text-zinc-400">Nenhum contrato encontrado</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-100">
            {filtered.map(c => (
              <div key={c.id}>

                {/* Desktop row */}
                <div className="hidden md:grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3.5 items-center hover:bg-zinc-50/60 transition-colors group cursor-pointer">
                  <div className="flex items-center gap-2 min-w-0">
                    <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{c.cliente}</p>
                    {c.expiringSoon && (
                      <span className="shrink-0 flex items-center gap-1 text-[11px] font-semibold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full border border-amber-100">
                        <WarningCircle size={10} weight="fill" />
                        Vence
                      </span>
                    )}
                  </div>
                  <p className="text-[13px] text-zinc-500 truncate">{c.objeto}</p>
                  <p className="text-[13px] text-zinc-500">{c.inicio}</p>
                  <p className={`text-[13px] font-medium ${c.expiringSoon ? 'text-amber-600 font-semibold' : 'text-zinc-500'}`}>
                    {c.validade}
                  </p>
                  <span className={`inline-flex text-[11px] font-semibold px-2 py-0.5 rounded-full w-fit ${STATUS_STYLES[c.status]}`}>
                    {c.status}
                  </span>
                  <button className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-all">
                    <DotsThreeVertical size={16} weight="bold" />
                  </button>
                </div>

                {/* Mobile card */}
                <div className="md:hidden p-4 active:bg-zinc-50 transition-colors cursor-pointer">
                  <div className="flex items-start gap-3">
                    <div className="w-9 h-9 rounded-xl bg-[#0ABAB5]/10 flex items-center justify-center shrink-0 mt-0.5">
                      <Handshake size={17} weight="duotone" className="text-[#0ABAB5]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-0.5">
                        <p className="text-[14px] font-semibold text-[#1D1D1F] truncate">{c.cliente}</p>
                        <div className="flex items-center gap-1.5 shrink-0">
                          {c.expiringSoon && (
                            <WarningCircle size={14} weight="fill" className="text-amber-500" />
                          )}
                          <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${STATUS_STYLES[c.status]}`}>
                            {c.status}
                          </span>
                        </div>
                      </div>
                      <p className="text-[12px] text-zinc-400 mb-2.5 truncate">{c.objeto}</p>
                      <div className="flex items-center gap-4 pt-2 border-t border-zinc-100">
                        <div>
                          <p className="text-[10px] text-zinc-400">Início</p>
                          <p className="text-[12px] font-medium text-zinc-600">{c.inicio}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-zinc-400">Validade</p>
                          <p className={`text-[12px] font-medium ${c.expiringSoon ? 'text-amber-600 font-semibold' : 'text-zinc-600'}`}>
                            {c.validade}
                          </p>
                        </div>
                        <button className="ml-auto p-1 rounded-lg hover:bg-zinc-100 text-zinc-400">
                          <DotsThreeVertical size={15} weight="bold" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <p className="text-[12px] text-zinc-400 px-1">{filtered.length} contrato{filtered.length !== 1 ? 's' : ''}</p>
    </div>
  )
}

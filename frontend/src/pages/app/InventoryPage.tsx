import { useState } from 'react'
import { Plus, DotsThreeVertical, Package, WarningCircle, CurrencyDollar } from '@phosphor-icons/react'

type StockStatus = 'Normal' | 'Baixo' | 'Crítico'
type FilterTab = 'Todos' | StockStatus

interface Product {
  id: string
  name: string
  categoria: string
  stock: number
  minStock: number
  status: StockStatus
}

const PRODUCTS: Product[] = [
  { id: '1', name: 'Painel Solar 400W',    categoria: 'Painéis',         stock: 45, minStock: 10, status: 'Normal'  },
  { id: '2', name: 'Inversor 5kW',         categoria: 'Inversores',      stock: 8,  minStock: 10, status: 'Baixo'   },
  { id: '3', name: 'Cabo Solar 6mm',       categoria: 'Cabos',           stock: 0,  minStock: 20, status: 'Crítico' },
  { id: '4', name: 'Estrutura Metálica',   categoria: 'Estruturas',      stock: 23, minStock: 5,  status: 'Normal'  },
  { id: '5', name: 'Microinversor 800W',   categoria: 'Microinversores', stock: 3,  minStock: 5,  status: 'Baixo'   },
  { id: '6', name: 'String Box 4E/4S',     categoria: 'Proteção',        stock: 12, minStock: 4,  status: 'Normal'  },
  { id: '7', name: 'Disjuntor 32A',        categoria: 'Proteção',        stock: 2,  minStock: 15, status: 'Crítico' },
]

const STATUS_STYLES: Record<StockStatus, { pill: string; bar: string; text: string }> = {
  Normal:   { pill: 'bg-emerald-50 text-emerald-700 border border-emerald-100',  bar: 'bg-emerald-500', text: 'text-emerald-600' },
  Baixo:    { pill: 'bg-amber-50 text-amber-700 border border-amber-100',        bar: 'bg-amber-500',   text: 'text-amber-600'   },
  Crítico:  { pill: 'bg-red-50 text-red-700 border border-red-100',              bar: 'bg-red-500',     text: 'text-red-600'     },
}

const TABS: FilterTab[] = ['Todos', 'Normal', 'Baixo', 'Crítico']

function StockBar({ stock, minStock, status }: { stock: number; minStock: number; status: StockStatus }) {
  const pct = minStock === 0 ? 100 : Math.min(100, Math.round((stock / (minStock * 2)) * 100))
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-zinc-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${STATUS_STYLES[status].bar}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-[12px] font-bold font-mono ${STATUS_STYLES[status].text}`}>{stock}</span>
    </div>
  )
}

export default function InventoryPage() {
  const [tab, setTab] = useState<FilterTab>('Todos')

  const filtered = tab === 'Todos' ? PRODUCTS : PRODUCTS.filter(p => p.status === tab)

  const total      = PRODUCTS.length
  const baixo      = PRODUCTS.filter(p => p.status === 'Baixo' || p.status === 'Crítico').length
  const hasAlerts  = baixo > 0
  const valorEstoque = 45000

  return (
    <div className="p-4 md:p-6 space-y-5 pb-6">

      {/* Sticky header */}
      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100 flex items-center justify-between">
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight">Estoque</h1>
        <button className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#09a8a3] text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95">
          <Plus size={15} weight="bold" />
          <span className="hidden sm:inline">Novo Produto</span>
          <span className="sm:hidden">Novo</span>
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-[#0ABAB5]/10 flex items-center justify-center mb-3">
            <Package size={16} weight="duotone" className="text-[#0ABAB5]" />
          </div>
          <p className="text-xl font-bold text-[#1D1D1F] font-mono truncate">{total}</p>
          <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">Total de Produtos</p>
        </div>
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-amber-50 flex items-center justify-center mb-3">
            <WarningCircle size={16} weight="duotone" className="text-amber-600" />
          </div>
          <p className="text-xl font-bold text-amber-600 font-mono truncate">{baixo}</p>
          <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">Estoque Baixo</p>
        </div>
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-emerald-50 flex items-center justify-center mb-3">
            <CurrencyDollar size={16} weight="duotone" className="text-emerald-600" />
          </div>
          <p className="text-xl font-bold text-[#1D1D1F] font-mono truncate">R$ {(valorEstoque / 1000).toFixed(0)}k</p>
          <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">Valor em Estoque</p>
        </div>
      </div>

      {/* Alert banner */}
      {hasAlerts && (
        <div className="flex items-center gap-3 p-3.5 bg-amber-50 rounded-2xl border border-amber-200">
          <WarningCircle size={18} weight="fill" className="text-amber-600 shrink-0" />
          <p className="text-[13px] font-semibold text-amber-800 flex-1">
            {baixo} produto{baixo !== 1 ? 's' : ''} com estoque abaixo do mínimo
          </p>
          <button className="text-[12px] font-semibold text-amber-700 hover:text-amber-900 transition-colors shrink-0">
            Ver todos
          </button>
        </div>
      )}

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

      {/* Product list */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 overflow-hidden">

        {/* Desktop header */}
        <div className="hidden md:grid grid-cols-[2fr_1fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3 border-b border-zinc-100 bg-zinc-50/60">
          {['Produto', 'Categoria', 'Estoque Atual', 'Estoque Mínimo', 'Status', ''].map(h => (
            <p key={h} className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">{h}</p>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className="flex flex-col items-center py-16 text-zinc-300">
            <Package size={40} weight="duotone" />
            <p className="text-sm mt-2 text-zinc-400">Nenhum produto encontrado</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-100">
            {filtered.map(p => {
              const st = STATUS_STYLES[p.status]
              return (
                <div key={p.id}>

                  {/* Desktop row */}
                  <div className="hidden md:grid grid-cols-[2fr_1fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3.5 items-center hover:bg-zinc-50/60 transition-colors group cursor-pointer">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-zinc-50 flex items-center justify-center shrink-0">
                        <Package size={15} weight="duotone" className="text-zinc-400" />
                      </div>
                      <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{p.name}</p>
                    </div>
                    <span className="text-[12px] text-zinc-500 bg-zinc-50 px-2 py-0.5 rounded-lg w-fit font-medium">
                      {p.categoria}
                    </span>
                    <div className="min-w-0">
                      <StockBar stock={p.stock} minStock={p.minStock} status={p.status} />
                    </div>
                    <p className="text-[13px] font-mono text-zinc-500">{p.minStock}</p>
                    <span className={`inline-flex text-[11px] font-semibold px-2 py-0.5 rounded-full w-fit ${st.pill}`}>
                      {p.status}
                    </span>
                    <button className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-all">
                      <DotsThreeVertical size={16} weight="bold" />
                    </button>
                  </div>

                  {/* Mobile card */}
                  <div className="md:hidden p-4 active:bg-zinc-50 transition-colors cursor-pointer">
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-xl bg-zinc-50 flex items-center justify-center shrink-0">
                          <Package size={17} weight="duotone" className="text-zinc-400" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-[14px] font-semibold text-[#1D1D1F] truncate">{p.name}</p>
                          <p className="text-[11px] text-zinc-400">{p.categoria}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${st.pill}`}>
                          {p.status}
                        </span>
                        <button className="p-1 rounded-lg hover:bg-zinc-100 text-zinc-400">
                          <DotsThreeVertical size={15} weight="bold" />
                        </button>
                      </div>
                    </div>
                    <div className="pt-2 border-t border-zinc-100">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[11px] text-zinc-400">Estoque atual</span>
                        <span className="text-[11px] text-zinc-400">Mínimo: {p.minStock}</span>
                      </div>
                      <StockBar stock={p.stock} minStock={p.minStock} status={p.status} />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <p className="text-[12px] text-zinc-400 px-1">{filtered.length} produto{filtered.length !== 1 ? 's' : ''}</p>
    </div>
  )
}

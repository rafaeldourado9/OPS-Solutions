import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, DotsThreeVertical, Package, WarningCircle, CurrencyDollar,
  X, Check, SpinnerGap, PencilSimple, MagnifyingGlass, Trash,
  ArrowUp, ArrowDown, ClockCounterClockwise, FilePdf, ArrowsClockwise,
} from '@phosphor-icons/react'
import { productsApi, type Product, type CreateProductPayload, type StockMovement, type AddMovementPayload } from '../../api/products'

// ── Helpers ────────────────────────────────────────────────────────────────────

type StockStatus = 'Normal' | 'Baixo' | 'Crítico'
type FilterTab = 'Todos' | StockStatus

const TABS: FilterTab[] = ['Todos', 'Normal', 'Baixo', 'Crítico']

const STATUS_STYLES: Record<StockStatus, { pill: string; bar: string; text: string }> = {
  Normal:  { pill: 'bg-emerald-50 text-emerald-700 border border-emerald-100', bar: 'bg-emerald-500', text: 'text-emerald-600' },
  Baixo:   { pill: 'bg-amber-50 text-amber-700 border border-amber-100',       bar: 'bg-amber-500',   text: 'text-amber-600'   },
  Crítico: { pill: 'bg-red-50 text-red-700 border border-red-100',             bar: 'bg-red-500',     text: 'text-red-600'     },
}

function computeStatus(stock: number, minStock: number): StockStatus {
  if (stock <= 0) return 'Crítico'
  if (stock < minStock) return 'Baixo'
  return 'Normal'
}

function formatPrice(value: number | null | undefined): string {
  if (value == null) return '-'
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function StockBar({ stock, minStock, status }: { stock: number; minStock: number; status: StockStatus }) {
  const pct = minStock === 0 ? 100 : Math.min(100, Math.round((stock / (minStock * 2)) * 100))
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-zinc-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${STATUS_STYLES[status].bar}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-[12px] font-bold font-mono ${STATUS_STYLES[status].text}`}>{stock}</span>
    </div>
  )
}

// ── Product Modal ─────────────────────────────────────────────────────────────

interface ModalProps {
  initial?: Product
  onClose: () => void
  onSave: (data: CreateProductPayload) => void
  saving: boolean
}

function ProductModal({ initial, onClose, onSave, saving }: ModalProps) {
  const [name, setName]           = useState(initial?.name ?? '')
  const [sku, setSku]             = useState(initial?.sku ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [unitPrice, setUnitPrice] = useState(initial?.unit_price?.toString() ?? '')
  const [costPrice, setCostPrice] = useState(initial?.cost_price?.toString() ?? '')
  const [stock, setStock]         = useState(initial?.stock?.toString() ?? '0')
  const [minStock, setMinStock]   = useState(initial?.min_stock?.toString() ?? '10')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !sku.trim()) return
    const parsedPrice = unitPrice.trim() ? parseFloat(unitPrice.replace(',', '.')) : null
    const parsedCost = costPrice.trim() ? parseFloat(costPrice.replace(',', '.')) : null
    onSave({
      name: name.trim(),
      sku: sku.trim(),
      description: description.trim() || undefined,
      unit_price: parsedPrice !== null && !isNaN(parsedPrice) ? parsedPrice : null,
      cost_price: parsedCost !== null && !isNaN(parsedCost) ? parsedCost : null,
      stock: parseInt(stock) || 0,
      min_stock: parseInt(minStock) || 0,
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100">
          <h2 className="text-[15px] font-bold text-[#1D1D1F]">
            {initial ? 'Editar Produto' : 'Novo Produto'}
          </h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
            <X size={16} weight="bold" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Nome do Produto *</label>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Ex: Produto A"
              className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" required autoFocus />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">SKU *</label>
              <input value={sku} onChange={e => setSku(e.target.value)} placeholder="Ex: PROD-001"
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" required />
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Categoria</label>
              <input value={description} onChange={e => setDescription(e.target.value)} placeholder="Ex: Eletrônicos, Serviços"
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Preço de Venda (R$) <span className="text-zinc-300 font-normal">opcional</span></label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[13px] text-zinc-400 font-semibold pointer-events-none">R$</span>
                <input value={unitPrice} onChange={e => setUnitPrice(e.target.value)} placeholder="Deixe vazio se não aplicável" inputMode="decimal"
                  className="w-full text-[14px] border border-zinc-200 rounded-xl pl-9 pr-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
              </div>
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Preço de Custo (R$) <span className="text-zinc-300 font-normal">opcional</span></label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[13px] text-zinc-400 font-semibold pointer-events-none">R$</span>
                <input value={costPrice} onChange={e => setCostPrice(e.target.value)} placeholder="Deixe vazio se não aplicável" inputMode="decimal"
                  className="w-full text-[14px] border border-zinc-200 rounded-xl pl-9 pr-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Estoque Atual</label>
              <input value={stock} onChange={e => setStock(e.target.value)} placeholder="0" type="number" min="0"
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Estoque Mínimo</label>
              <input value={minStock} onChange={e => setMinStock(e.target.value)} placeholder="10" type="number" min="0"
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
            </div>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={saving || !name.trim() || !sku.trim()}
              className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] disabled:opacity-50 py-2.5 rounded-xl transition-colors">
              {saving ? <SpinnerGap size={14} className="animate-spin" /> : <Check size={14} weight="bold" />}
              {initial ? 'Salvar' : 'Criar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Stock Movement Modal ──────────────────────────────────────────────────────

interface MovementModalProps {
  product: Product
  onClose: () => void
}

function MovementModal({ product, onClose }: MovementModalProps) {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'movement' | 'history'>('movement')
  const [type, setType] = useState<'in' | 'out' | 'adjustment'>('in')
  const [quantity, setQuantity] = useState('')
  const [notes, setNotes] = useState('')

  const { data: movements = [], isLoading: loadingMovements } = useQuery<StockMovement[]>({
    queryKey: ['movements', product.id],
    queryFn: () => productsApi.getMovements(product.id),
  })

  const addMutation = useMutation({
    mutationFn: (data: AddMovementPayload) => productsApi.addMovement(product.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['movements', product.id] })
      setQuantity('')
      setNotes('')
      setActiveTab('history')
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const qty = parseFloat(quantity)
    if (!qty || qty <= 0) return
    addMutation.mutate({ type, quantity: qty, notes: notes.trim() || undefined })
  }

  const status = computeStatus(product.stock, product.min_stock)
  const st = STATUS_STYLES[status]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-xl max-h-[90vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="px-5 pt-5 pb-4 border-b border-zinc-100">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[15px] font-bold text-[#1D1D1F]">Movimentação de Estoque</h2>
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
              <X size={16} weight="bold" />
            </button>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-zinc-50 flex items-center justify-center shrink-0">
              <Package size={18} weight="duotone" className="text-zinc-400" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[14px] font-semibold text-[#1D1D1F] truncate">{product.name}</p>
              <div className="flex items-center gap-2">
                <span className="text-[12px] text-zinc-400">{product.sku}</span>
                {product.unit_price != null && (
                  <span className="text-[12px] text-zinc-400">| {formatPrice(product.unit_price)}</span>
                )}
              </div>
            </div>
            <div className="text-right shrink-0">
              <p className="text-lg font-bold font-mono text-[#1D1D1F]">{product.stock}</p>
              <span className={`inline-flex text-[10px] font-semibold px-2 py-0.5 rounded-full ${st.pill}`}>{status}</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-zinc-100">
          <button onClick={() => setActiveTab('movement')}
            className={`flex-1 text-[13px] font-semibold py-3 transition-colors ${activeTab === 'movement' ? 'text-[#0ABAB5] border-b-2 border-[#0ABAB5]' : 'text-zinc-400 hover:text-zinc-600'}`}>
            Nova Movimentação
          </button>
          <button onClick={() => setActiveTab('history')}
            className={`flex-1 text-[13px] font-semibold py-3 transition-colors ${activeTab === 'history' ? 'text-[#0ABAB5] border-b-2 border-[#0ABAB5]' : 'text-zinc-400 hover:text-zinc-600'}`}>
            Histórico ({movements.length})
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'movement' ? (
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              {/* Movement type selector */}
              <div>
                <label className="block text-[12px] font-semibold text-zinc-500 mb-2">Tipo de Movimentação</label>
                <div className="grid grid-cols-3 gap-2">
                  <button type="button" onClick={() => setType('in')}
                    className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border-2 transition-all ${
                      type === 'in' ? 'border-emerald-500 bg-emerald-50' : 'border-zinc-200 hover:border-zinc-300'
                    }`}>
                    <ArrowDown size={20} weight="bold" className={type === 'in' ? 'text-emerald-600' : 'text-zinc-400'} />
                    <span className={`text-[12px] font-semibold ${type === 'in' ? 'text-emerald-700' : 'text-zinc-500'}`}>Entrada</span>
                  </button>
                  <button type="button" onClick={() => setType('out')}
                    className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border-2 transition-all ${
                      type === 'out' ? 'border-red-500 bg-red-50' : 'border-zinc-200 hover:border-zinc-300'
                    }`}>
                    <ArrowUp size={20} weight="bold" className={type === 'out' ? 'text-red-600' : 'text-zinc-400'} />
                    <span className={`text-[12px] font-semibold ${type === 'out' ? 'text-red-700' : 'text-zinc-500'}`}>Saída</span>
                  </button>
                  <button type="button" onClick={() => setType('adjustment')}
                    className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border-2 transition-all ${
                      type === 'adjustment' ? 'border-blue-500 bg-blue-50' : 'border-zinc-200 hover:border-zinc-300'
                    }`}>
                    <ArrowsClockwise size={20} weight="bold" className={type === 'adjustment' ? 'text-blue-600' : 'text-zinc-400'} />
                    <span className={`text-[12px] font-semibold ${type === 'adjustment' ? 'text-blue-700' : 'text-zinc-500'}`}>Ajuste</span>
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">
                  {type === 'adjustment' ? 'Novo Estoque (valor absoluto)' : 'Quantidade'}
                </label>
                <input value={quantity} onChange={e => setQuantity(e.target.value)} placeholder="0" type="number" min="1" step="1"
                  className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" required autoFocus />
                {type === 'out' && parseFloat(quantity) > product.stock && (
                  <p className="text-[11px] text-red-500 mt-1">Quantidade excede o estoque atual ({product.stock})</p>
                )}
              </div>

              <div>
                <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Motivo / Observação</label>
                <input value={notes} onChange={e => setNotes(e.target.value)}
                  placeholder={type === 'in' ? 'Ex: Compra fornecedor, Devolução...' : type === 'out' ? 'Ex: Venda, Perda, Uso interno...' : 'Ex: Inventário físico, Correção...'}
                  className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
              </div>

              {addMutation.isError && (
                <p className="text-[12px] text-red-500 bg-red-50 p-2 rounded-lg">
                  Erro: {(addMutation.error as any)?.response?.data?.detail ?? 'Falha ao registrar movimentação'}
                </p>
              )}

              <button type="submit" disabled={addMutation.isPending || !quantity || parseFloat(quantity) <= 0}
                className="w-full flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] disabled:opacity-50 py-2.5 rounded-xl transition-colors">
                {addMutation.isPending ? <SpinnerGap size={14} className="animate-spin" /> : <Check size={14} weight="bold" />}
                Registrar {type === 'in' ? 'Entrada' : type === 'out' ? 'Saída' : 'Ajuste'}
              </button>
            </form>
          ) : (
            <div className="p-5">
              {loadingMovements ? (
                <div className="flex items-center justify-center py-10">
                  <SpinnerGap size={20} className="animate-spin text-[#0ABAB5]" />
                </div>
              ) : movements.length === 0 ? (
                <div className="flex flex-col items-center py-10 text-zinc-300">
                  <ClockCounterClockwise size={32} weight="duotone" />
                  <p className="text-[13px] mt-2 text-zinc-400">Nenhuma movimentação registrada</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {movements.map(m => {
                    const isIn = m.type === 'in'
                    const isOut = m.type === 'out'
                    return (
                      <div key={m.id} className="flex items-center gap-3 p-3 rounded-xl bg-zinc-50/60 border border-zinc-100">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                          isIn ? 'bg-emerald-100' : isOut ? 'bg-red-100' : 'bg-blue-100'
                        }`}>
                          {isIn ? <ArrowDown size={14} weight="bold" className="text-emerald-600" /> :
                           isOut ? <ArrowUp size={14} weight="bold" className="text-red-600" /> :
                           <ArrowsClockwise size={14} weight="bold" className="text-blue-600" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className={`text-[13px] font-bold font-mono ${
                              isIn ? 'text-emerald-600' : isOut ? 'text-red-600' : 'text-blue-600'
                            }`}>
                              {isIn ? '+' : isOut ? '-' : '='}{m.quantity}
                            </span>
                            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                              isIn ? 'bg-emerald-50 text-emerald-600' : isOut ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'
                            }`}>
                              {isIn ? 'Entrada' : isOut ? 'Saída' : 'Ajuste'}
                            </span>
                          </div>
                          {m.notes && <p className="text-[11px] text-zinc-500 truncate mt-0.5">{m.notes}</p>}
                        </div>
                        <span className="text-[11px] text-zinc-400 shrink-0">{formatDate(m.created_at)}</span>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Action Menu ────────────────────────────────────────────────────────────────

function ActionMenu({ onEdit, onMovement, onDelete, onClose }: { onEdit: () => void; onMovement: () => void; onDelete: () => void; onClose: () => void }) {
  return (
    <>
      <div className="fixed inset-0 z-40" onClick={e => { e.stopPropagation(); onClose() }} />
      <div className="absolute right-0 top-full mt-1 w-44 bg-white rounded-xl border border-zinc-100 shadow-lg py-1 z-50"
        onClick={e => e.stopPropagation()}>
        <button onClick={() => { onClose(); onEdit() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-zinc-600 hover:bg-zinc-50 transition-colors">
          <PencilSimple size={14} /> Editar
        </button>
        <button onClick={() => { onClose(); onMovement() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-zinc-600 hover:bg-zinc-50 transition-colors">
          <ArrowsClockwise size={14} /> Movimentar Estoque
        </button>
        <button onClick={() => { onClose(); onDelete() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-red-500 hover:bg-red-50 transition-colors">
          <Trash size={14} weight="bold" /> Apagar
        </button>
      </div>
    </>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function InventoryPage() {
  const queryClient = useQueryClient()
  const [tab, setTab]                     = useState<FilterTab>('Todos')
  const [modal, setModal]                 = useState<'create' | Product | null>(null)
  const [movementProduct, setMovementProduct] = useState<Product | null>(null)
  const [menuOpen, setMenuOpen]           = useState<string | null>(null)
  const [search, setSearch]               = useState('')
  const [exporting, setExporting]         = useState(false)

  const { data: products = [], isLoading } = useQuery<Product[]>({
    queryKey: ['products'],
    queryFn: () => productsApi.list({ active_only: true }),
  })

  const createMutation = useMutation({
    mutationFn: (data: CreateProductPayload) => productsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      setModal(null)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateProductPayload> }) =>
      productsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      setModal(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => productsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })

  function handleDelete(product: Product) {
    if (window.confirm(`Tem certeza que deseja apagar "${product.name}"?`)) {
      deleteMutation.mutate(product.id)
    }
  }

  // Enrich products with computed status
  const enriched = products.map(p => ({
    ...p,
    stockStatus: computeStatus(p.stock, p.min_stock),
  }))

  const searchFiltered = search
    ? enriched.filter(p => p.name.toLowerCase().includes(search.toLowerCase()) ||
                           (p.description ?? '').toLowerCase().includes(search.toLowerCase()) ||
                           p.sku.toLowerCase().includes(search.toLowerCase()))
    : enriched

  const filtered = tab === 'Todos' ? searchFiltered : searchFiltered.filter(p => p.stockStatus === tab)

  const total        = enriched.length
  const baixo        = enriched.filter(p => p.stockStatus === 'Baixo' || p.stockStatus === 'Crítico').length
  const valorEstoque = enriched.reduce((s, p) => s + p.stock * (p.unit_price ?? 0), 0)

  function handleSave(data: CreateProductPayload) {
    if (modal === 'create') {
      createMutation.mutate(data)
    } else if (modal && typeof modal === 'object') {
      updateMutation.mutate({ id: modal.id, data })
    }
  }

  async function handleExportPdf() {
    setExporting(true)
    try {
      const response = await productsApi.exportReport()
      const blob = new Blob([response], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `relatorio-estoque-${new Date().toISOString().slice(0, 10)}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch {
      alert('Erro ao gerar relatório PDF')
    } finally {
      setExporting(false)
    }
  }

  const saving = createMutation.isPending || updateMutation.isPending

  return (
    <div className="p-4 md:p-6 space-y-5 pb-6">

      {/* Modals */}
      {modal !== null && (
        <ProductModal
          initial={modal === 'create' ? undefined : modal}
          onClose={() => setModal(null)}
          onSave={handleSave}
          saving={saving}
        />
      )}
      {movementProduct && (
        <MovementModal product={movementProduct} onClose={() => setMovementProduct(null)} />
      )}

      {/* Sticky header */}
      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100 flex items-center justify-between gap-2">
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight">Estoque</h1>
        <div className="flex items-center gap-2">
          <button onClick={handleExportPdf} disabled={exporting || products.length === 0}
            className="flex items-center gap-2 border border-zinc-200 text-zinc-600 hover:bg-zinc-50 text-[13px] font-semibold px-3 py-2 rounded-xl transition-all active:scale-95 disabled:opacity-50">
            {exporting ? <SpinnerGap size={15} className="animate-spin" /> : <FilePdf size={15} weight="duotone" />}
            <span className="hidden sm:inline">Relatório PDF</span>
          </button>
          <button onClick={() => setModal('create')} className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#09a8a3] text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95">
            <Plus size={15} weight="bold" />
            <span className="hidden sm:inline">Novo Produto</span>
            <span className="sm:hidden">Novo</span>
          </button>
        </div>
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
          <p className="text-xl font-bold text-[#1D1D1F] font-mono truncate">
            {valorEstoque >= 1000 ? `R$ ${(valorEstoque / 1000).toFixed(0)}k` : `R$ ${valorEstoque.toLocaleString('pt-BR')}`}
          </p>
          <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">Valor em Estoque</p>
        </div>
      </div>

      {/* Alert banner */}
      {baixo > 0 && (
        <div className="flex items-center gap-3 p-3.5 bg-amber-50 rounded-2xl border border-amber-200">
          <WarningCircle size={18} weight="fill" className="text-amber-600 shrink-0" />
          <p className="text-[13px] font-semibold text-amber-800 flex-1">
            {baixo} produto{baixo !== 1 ? 's' : ''} com estoque abaixo do mínimo
          </p>
          <button onClick={() => setTab('Baixo')} className="text-[12px] font-semibold text-amber-700 hover:text-amber-900 transition-colors shrink-0">
            Ver todos
          </button>
        </div>
      )}

      {/* Search */}
      <div className="flex items-center gap-2 bg-white border border-zinc-200 rounded-xl px-3 py-2 focus-within:border-[#0ABAB5]/50 transition-all">
        <MagnifyingGlass size={14} className="text-zinc-400 shrink-0" />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por nome, SKU ou categoria..."
          className="text-[13px] bg-transparent focus:outline-none w-full placeholder:text-zinc-400" />
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1.5 overflow-x-auto pb-0.5 scrollbar-none">
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`shrink-0 text-[12px] font-semibold px-3.5 py-1.5 rounded-xl border transition-all ${
              tab === t ? 'bg-[#0ABAB5] text-white border-[#0ABAB5]' : 'bg-white text-zinc-500 border-zinc-200 hover:border-zinc-300'
            }`}>
            {t}
          </button>
        ))}
      </div>

      {/* Product list */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 overflow-visible">
        <div className="hidden md:grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3 border-b border-zinc-100 bg-zinc-50/60">
          {['Produto', 'Categoria', 'Preço', 'Estoque Atual', 'Mínimo', 'Status', ''].map(h => (
            <p key={h} className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">{h}</p>
          ))}
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <SpinnerGap size={24} className="animate-spin text-[#0ABAB5]" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center py-16 text-zinc-300">
            <Package size={40} weight="duotone" />
            <p className="text-sm mt-2 text-zinc-400">Nenhum produto encontrado</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-100">
            {filtered.map(p => {
              const st = STATUS_STYLES[p.stockStatus]
              return (
                <div key={p.id}>
                  {/* Desktop row */}
                  <div className="hidden md:grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3.5 items-center hover:bg-zinc-50/60 transition-colors group cursor-pointer"
                    onClick={() => setModal(p)}>
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-zinc-50 flex items-center justify-center shrink-0">
                        <Package size={15} weight="duotone" className="text-zinc-400" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{p.name}</p>
                        <p className="text-[11px] text-zinc-400 truncate">{p.sku}</p>
                      </div>
                    </div>
                    <span className="text-[12px] text-zinc-500 bg-zinc-50 px-2 py-0.5 rounded-lg w-fit font-medium truncate">
                      {p.description || '-'}
                    </span>
                    <span className="text-[13px] font-mono text-zinc-600">{formatPrice(p.unit_price)}</span>
                    <div className="min-w-0">
                      <StockBar stock={p.stock} minStock={p.min_stock} status={p.stockStatus} />
                    </div>
                    <p className="text-[13px] font-mono text-zinc-500">{p.min_stock}</p>
                    <span className={`inline-flex text-[11px] font-semibold px-2 py-0.5 rounded-full w-fit ${st.pill}`}>
                      {p.stockStatus}
                    </span>
                    <div className="relative" onClick={e => e.stopPropagation()}>
                      <button onClick={() => setMenuOpen(menuOpen === p.id ? null : p.id)}
                        className="p-1.5 rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-600 transition-all">
                        <DotsThreeVertical size={18} weight="bold" />
                      </button>
                      {menuOpen === p.id && (
                        <ActionMenu onEdit={() => setModal(p)} onMovement={() => setMovementProduct(p)} onDelete={() => handleDelete(p)} onClose={() => setMenuOpen(null)} />
                      )}
                    </div>
                  </div>

                  {/* Mobile card */}
                  <div className="md:hidden p-4 active:bg-zinc-50 transition-colors cursor-pointer" onClick={() => setMovementProduct(p)}>
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-xl bg-zinc-50 flex items-center justify-center shrink-0">
                          <Package size={17} weight="duotone" className="text-zinc-400" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-[14px] font-semibold text-[#1D1D1F] truncate">{p.name}</p>
                          <p className="text-[11px] text-zinc-400">{p.sku} {p.unit_price != null ? `| ${formatPrice(p.unit_price)}` : ''}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0" onClick={e => e.stopPropagation()}>
                        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${st.pill}`}>
                          {p.stockStatus}
                        </span>
                        <button onClick={() => setMenuOpen(menuOpen === p.id ? null : p.id)} className="p-1 rounded-lg hover:bg-zinc-100 text-zinc-400">
                          <DotsThreeVertical size={15} weight="bold" />
                        </button>
                        {menuOpen === p.id && (
                          <ActionMenu onEdit={() => setModal(p)} onMovement={() => setMovementProduct(p)} onDelete={() => handleDelete(p)} onClose={() => setMenuOpen(null)} />
                        )}
                      </div>
                    </div>
                    <div className="pt-2 border-t border-zinc-100">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[11px] text-zinc-400">Estoque atual</span>
                        <span className="text-[11px] text-zinc-400">Mínimo: {p.min_stock}</span>
                      </div>
                      <StockBar stock={p.stock} minStock={p.min_stock} status={p.stockStatus} />
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

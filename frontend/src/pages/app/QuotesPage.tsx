import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, DotsThreeVertical, FileText, CurrencyDollar, ClockCounterClockwise,
  CheckCircle, X, Check, SpinnerGap, PencilSimple, Trash, MagnifyingGlass,
  FilePdf, ArrowRight, ArrowLeft, TrendUp, Percent,
  DownloadSimple, Warning,
} from '@phosphor-icons/react'
import { quotesApi, type QuoteStatus, type Quote, type CreateQuotePayload } from '../../api/quotes'
import { customersApi, type Customer, type CustomerListResponse } from '../../api/customers'
import { productsApi, type Product } from '../../api/products'
import { premisesApi, type Premise } from '../../api/premises'

// ── Helpers ────────────────────────────────────────────────────────────────────

const STATUS_LABEL: Record<QuoteStatus, string> = {
  draft:    'Rascunho',
  sent:     'Enviado',
  approved: 'Aprovado',
  rejected: 'Rejeitado',
  expired:  'Expirado',
}

const STATUS_STYLES: Record<QuoteStatus, string> = {
  approved: 'bg-emerald-50 text-emerald-700 border border-emerald-100',
  sent:     'bg-blue-50 text-blue-700 border border-blue-100',
  draft:    'bg-zinc-100 text-zinc-600 border border-zinc-200',
  rejected: 'bg-red-50 text-red-700 border border-red-100',
  expired:  'bg-orange-50 text-orange-700 border border-orange-100',
}

const STATUSES: QuoteStatus[] = ['draft', 'sent', 'approved', 'rejected', 'expired']
type FilterTab = 'Todos' | QuoteStatus
const TABS: FilterTab[] = ['Todos', 'draft', 'sent', 'approved', 'rejected']
const TAB_LABELS: Record<FilterTab, string> = {
  Todos: 'Todos', draft: 'Rascunho', sent: 'Enviado', approved: 'Aprovado',
  rejected: 'Rejeitado', expired: 'Expirado',
}

function fmtVal(n: number) {
  if (n >= 1000) return 'R$ ' + (n / 1000).toFixed(1).replace('.', ',') + 'k'
  return 'R$ ' + n.toLocaleString('pt-BR')
}

function fmtMoney(n: number) {
  return 'R$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function calcPremiseAmount(p: Premise, base: number): number {
  if (p.type === 'percentage') return base * (p.value / 100)
  if (p.type === 'multiplier') return (p.cost ?? 0) * p.value
  return p.value // fixed
}

// ── Wizard Modal ───────────────────────────────────────────────────────────────

type WizardStep = 'items' | 'premises' | 'preview'

interface QuoteItemDraft {
  product_id?: string
  description: string
  quantity: number
  unit_price: number
}

interface WizardModalProps {
  onClose: () => void
  onSave: (data: CreateQuotePayload) => void
  saving: boolean
}

function WizardModal({ onClose, onSave, saving }: WizardModalProps) {
  const [step, setStep] = useState<WizardStep>('items')
  const [title, setTitle]           = useState('')
  const [customerId, setCustomerId] = useState('')
  const [items, setItems]           = useState<QuoteItemDraft[]>([{ description: '', quantity: 1, unit_price: 0 }])
  const [selectedPremiseIds, setSelectedPremiseIds] = useState<Set<string>>(new Set())
  const [salePrice, setSalePrice]   = useState<number>(0)
  const [salePriceInput, setSalePriceInput] = useState<string>('')

  const { data: customersData } = useQuery<CustomerListResponse>({
    queryKey: ['customers-select'],
    queryFn: () => customersApi.list({ limit: 200 }),
  })
  const customers: Customer[] = customersData?.items ?? []

  const { data: products = [] } = useQuery<Product[]>({
    queryKey: ['products-select'],
    queryFn: () => productsApi.list({ active_only: true }),
  })

  const { data: premises = [] } = useQuery<Premise[]>({
    queryKey: ['premises-active'],
    queryFn: () => premisesApi.list(),
    select: (data) => data.filter(p => p.is_active),
  })

  // Pre-select all active premises on load
  useEffect(() => {
    if (premises.length > 0 && selectedPremiseIds.size === 0) {
      setSelectedPremiseIds(new Set(premises.map(p => p.id)))
    }
  }, [premises])

  // ── Calculations (contribution-margin method) ─────────────────────────────────
  // Premises are % of the SELLING PRICE, not of cost.
  // Formula: selling_price = (items_cost + fixed + multiplier) / (1 - sum_pct)
  const validItems = items.filter(i => i.description.trim())
  const itemsTotal = validItems.reduce((s, i) => s + i.quantity * i.unit_price, 0)

  const activePremises = premises.filter(p => selectedPremiseIds.has(p.id))
  const totalPct    = activePremises.filter(p => p.type === 'percentage').reduce((s, p) => s + p.value / 100, 0)
  const sumFixed    = activePremises.filter(p => p.type === 'fixed').reduce((s, p) => s + p.value, 0)
  const sumMult     = activePremises.filter(p => p.type === 'multiplier').reduce((s, p) => s + (p.cost ?? 0) * p.value, 0)
  const baseForCalc = itemsTotal + sumFixed + sumMult
  const naturalSell = totalPct < 1 ? baseForCalc / (1 - totalPct) : baseForCalc
  const suggestedPrice = Math.ceil(naturalSell)

  const effectiveSalePrice = salePrice > 0 ? salePrice : suggestedPrice

  // Premise amounts calculated on the effective sale price
  const premiseBreakdown = activePremises.map(p => ({
    ...p,
    amount: p.type === 'percentage'
      ? effectiveSalePrice * p.value / 100
      : p.type === 'multiplier'
      ? (p.cost ?? 0) * p.value
      : p.value,
  }))
  const premisesTotal = premiseBreakdown.reduce((s, p) => s + p.amount, 0)

  // Profitability stats
  const profit       = effectiveSalePrice - itemsTotal
  const marginPct    = effectiveSalePrice > 0 ? (profit / effectiveSalePrice) * 100 : 0
  const percentPremises = premiseBreakdown
    .filter(p => p.type === 'percentage')
    .reduce((s, p) => s + p.value, 0)

  // ── Navigation ────────────────────────────────────────────────────────────────

  function goToPremises() {
    // suggestedPrice is computed from current items — initialize sale price
    setSalePrice(0) // will be read as suggestedPrice via effectiveSalePrice
    setSalePriceInput('')
    setStep('premises')
  }

  function goToPreview() {
    setStep('preview')
  }

  function handleSalePriceChange(val: string) {
    setSalePriceInput(val)
    const n = parseFloat(val.replace(',', '.'))
    // 0 means "use suggestedPrice"; set actual value only when user typed something valid
    setSalePrice(!isNaN(n) && n > 0 ? n : 0)
  }

  function handleFinish() {
    // sale_price_override: only pass when user explicitly typed a custom value
    const customPrice = salePrice > 0 ? salePrice : undefined

    onSave({
      title: title.trim(),
      customer_id: customerId,
      items: validItems.map(i => ({
        description: i.description.trim(),
        quantity: i.quantity || 1,
        unit_price: i.unit_price || 0,
        discount_percent: 0,
      })),
      premise_ids: [...selectedPremiseIds],
      sale_price: customPrice,
    })
  }

  // ── Item helpers ──────────────────────────────────────────────────────────────

  function handleProductSelect(index: number, productId: string) {
    const product = products.find(p => p.id === productId)
    setItems(prev => prev.map((item, i) => {
      if (i !== index) return item
      if (!product) return { ...item, product_id: undefined, description: '', unit_price: 0 }
      return { ...item, product_id: product.id, description: product.name, unit_price: product.unit_price ?? 0 }
    }))
  }

  function updateItem(index: number, field: keyof QuoteItemDraft, value: string | number) {
    setItems(prev => prev.map((item, i) => i === index ? { ...item, [field]: value } : item))
  }

  function addItem() { setItems(prev => [...prev, { description: '', quantity: 1, unit_price: 0 }]) }
  function removeItem(index: number) { if (items.length > 1) setItems(prev => prev.filter((_, i) => i !== index)) }

  function togglePremise(id: string) {
    setSelectedPremiseIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      // Reset to auto-calculate (user can re-type if they want custom)
      setSalePrice(0)
      setSalePriceInput('')
      return next
    })
  }

  const canGoNext = title.trim() && customerId && validItems.length > 0 && validItems.some(i => i.unit_price > 0)

  const stepTitles: Record<WizardStep, string> = {
    items:    'Itens do Orçamento',
    premises: 'Premissas de Custo',
    preview:  'Revisão e Análise',
  }

  const stepNumbers: Record<WizardStep, number> = { items: 1, premises: 2, preview: 3 }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white w-full sm:rounded-2xl sm:max-w-2xl sm:max-h-[92vh] rounded-t-2xl max-h-[calc(100dvh-4.5rem)] sm:max-h-[92vh] overflow-hidden flex flex-col shadow-xl">

        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100 shrink-0">
          <div>
            <h2 className="text-[15px] font-bold text-[#1D1D1F]">{stepTitles[step]}</h2>
            <div className="flex items-center gap-1.5 mt-1">
              {(['items', 'premises', 'preview'] as WizardStep[]).map((s, idx) => (
                <div key={s} className="flex items-center gap-1.5">
                  <div className={`w-5 h-5 rounded-full text-[10px] font-bold flex items-center justify-center transition-colors ${
                    step === s ? 'bg-[#0ABAB5] text-white' :
                    stepNumbers[step] > idx + 1 ? 'bg-emerald-500 text-white' :
                    'bg-zinc-100 text-zinc-400'
                  }`}>{stepNumbers[step] > idx + 1 ? <Check size={8} weight="bold" /> : idx + 1}</div>
                  {idx < 2 && <div className={`w-8 h-0.5 rounded-full ${stepNumbers[step] > idx + 1 ? 'bg-emerald-500' : 'bg-zinc-100'}`} />}
                </div>
              ))}
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
            <X size={16} weight="bold" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto flex-1 p-5">

          {/* ── Step 1: Items ────────────────────────────────────────────────── */}
          {step === 'items' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Cliente *</label>
                  <select value={customerId} onChange={e => setCustomerId(e.target.value)}
                    className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all bg-white" required>
                    <option value="">Selecionar cliente...</option>
                    {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Título *</label>
                  <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Ex: Proposta Comercial"
                    className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" required autoFocus />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-[12px] font-semibold text-zinc-500">Itens</p>
                  <button type="button" onClick={addItem}
                    className="text-[12px] font-semibold text-[#0ABAB5] hover:text-[#09a8a3] flex items-center gap-1 transition-colors">
                    <Plus size={12} weight="bold" /> Adicionar item
                  </button>
                </div>

                {items.map((item, idx) => (
                  <div key={idx} className="bg-zinc-50 rounded-xl border border-zinc-100 overflow-hidden">
                    {/* Description row */}
                    <div className="flex items-center gap-2 px-3 py-2.5 border-b border-zinc-100">
                      <span className="text-[11px] font-bold text-zinc-400 w-4 shrink-0">#{idx + 1}</span>
                      <input value={item.description} onChange={e => updateItem(idx, 'description', e.target.value)}
                        placeholder="Descrição do item ou serviço *"
                        className="flex-1 text-[13px] bg-transparent outline-none placeholder:text-zinc-400 min-w-0" />
                      {items.length > 1 && (
                        <button type="button" onClick={() => removeItem(idx)}
                          className="p-1 rounded-lg hover:bg-red-50 text-zinc-300 hover:text-red-400 transition-colors shrink-0">
                          <X size={13} weight="bold" />
                        </button>
                      )}
                    </div>
                    {/* Qty × Price = Subtotal */}
                    <div className="px-3 py-2.5 flex items-center gap-2">
                      <div className="flex items-center gap-1.5 shrink-0">
                        <label className="text-[10px] font-semibold text-zinc-400 uppercase">Qtd</label>
                        <input value={item.quantity}
                          onChange={e => updateItem(idx, 'quantity', parseInt(e.target.value) || 1)}
                          type="number" min="1"
                          className="w-14 text-[13px] text-center border border-zinc-200 rounded-lg px-1 py-1.5 outline-none focus:border-[#0ABAB5] bg-white" />
                      </div>
                      <span className="text-zinc-300">×</span>
                      <div className="relative flex-1 min-w-0">
                        <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[11px] text-zinc-400 font-semibold pointer-events-none">R$</span>
                        <input
                          value={item.unit_price || ''}
                          onChange={e => updateItem(idx, 'unit_price', parseFloat(e.target.value.replace(',', '.')) || 0)}
                          placeholder="0,00" inputMode="decimal"
                          className="w-full text-[13px] border border-zinc-200 rounded-lg pl-7 pr-2 py-1.5 outline-none focus:border-[#0ABAB5] bg-white" />
                      </div>
                      {item.quantity > 0 && item.unit_price > 0 && (
                        <span className="text-[12px] font-bold text-[#0ABAB5] font-mono shrink-0 whitespace-nowrap">
                          = {fmtMoney(item.quantity * item.unit_price)}
                        </span>
                      )}
                    </div>
                    {/* Product link - compact */}
                    {products.length > 0 && (
                      <div className="px-3 pb-2.5">
                        <select value={item.product_id ?? ''} onChange={e => handleProductSelect(idx, e.target.value)}
                          className="w-full text-[12px] border border-zinc-200 rounded-lg px-2 py-1.5 outline-none focus:border-[#0ABAB5] bg-white text-zinc-500">
                          <option value="">Vincular produto do estoque (opcional)</option>
                          {products.map(p => (
                            <option key={p.id} value={p.id}>
                              {p.name} — R$ {p.unit_price?.toFixed(2) ?? '?'} (est: {p.stock})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                ))}

                {itemsTotal > 0 && (
                  <div className="flex items-center justify-between px-4 py-3 bg-zinc-50 rounded-xl border border-zinc-200">
                    <span className="text-[13px] font-semibold text-zinc-600">Custo total dos itens</span>
                    <span className="text-[15px] font-bold text-zinc-800 font-mono">{fmtMoney(itemsTotal)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Step 2: Premissas ─────────────────────────────────────────────── */}
          {step === 'premises' && (
            <div className="space-y-5">
              {premises.length === 0 ? (
                <div className="text-center py-8 text-zinc-400">
                  <Percent size={32} weight="duotone" className="mx-auto mb-2 opacity-50" />
                  <p className="text-[13px] font-medium">Nenhuma premissa configurada</p>
                  <p className="text-[12px] mt-1">Configure premissas de custo na página Premissas</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-[12px] font-semibold text-zinc-500 mb-3">
                    Selecione as premissas aplicáveis a este orçamento:
                  </p>
                  {premises.map(p => {
                    const amount = calcPremiseAmount(p, itemsTotal)
                    const isSelected = selectedPremiseIds.has(p.id)
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => togglePremise(p.id)}
                        className={`w-full flex items-center justify-between p-3.5 rounded-xl border transition-all text-left ${
                          isSelected
                            ? 'bg-[#0ABAB5]/5 border-[#0ABAB5]/30 ring-1 ring-[#0ABAB5]/20'
                            : 'bg-white border-zinc-200 hover:border-zinc-300'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-colors ${
                            isSelected ? 'border-[#0ABAB5] bg-[#0ABAB5]' : 'border-zinc-300'
                          }`}>
                            {isSelected && <Check size={11} weight="bold" className="text-white" />}
                          </div>
                          <div>
                            <p className="text-[13px] font-semibold text-zinc-800">{p.name}</p>
                            <p className="text-[11px] text-zinc-400 mt-0.5">
                              {p.type === 'percentage' && `${p.value}% sobre custo`}
                              {p.type === 'fixed' && `Valor fixo`}
                              {p.type === 'multiplier' && `Fator ${p.value}×`}
                              {p.description ? ` · ${p.description}` : ''}
                            </p>
                          </div>
                        </div>
                        <div className="text-right shrink-0 ml-3">
                          <p className={`text-[13px] font-bold font-mono ${isSelected ? 'text-[#0ABAB5]' : 'text-zinc-400'}`}>
                            +{fmtMoney(amount)}
                          </p>
                          <p className="text-[10px] text-zinc-400">
                            {p.type === 'percentage' ? `${p.value}%` : 'fixo'}
                          </p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              )}

              {/* Calculation Breakdown */}
              <div className="bg-zinc-50 rounded-xl border border-zinc-200 overflow-hidden">
                <div className="px-4 py-3 border-b border-zinc-200">
                  <p className="text-[12px] font-semibold text-zinc-500 uppercase tracking-wide">Cálculo do Preço de Venda</p>
                </div>
                <div className="p-4 space-y-2">
                  {/* Show breakdown as components of the selling price */}
                  {premiseBreakdown.map(p => (
                    <div key={p.id} className="flex justify-between">
                      <span className="text-[13px] text-zinc-500">
                        {p.name}
                        {p.type === 'percentage' && (
                          <span className="text-zinc-400 text-[11px] ml-1">({p.value}% do valor de venda)</span>
                        )}
                      </span>
                      <span className="text-[13px] font-semibold font-mono text-[#0ABAB5]">{fmtMoney(p.amount)}</span>
                    </div>
                  ))}
                  <div className="flex justify-between pt-1 border-t border-zinc-200">
                    <span className="text-[12px] text-zinc-400">
                      Custo dos itens ({(100 - percentPremises).toFixed(1)}% do valor de venda)
                    </span>
                    <span className="text-[12px] font-semibold font-mono text-zinc-600">
                      {fmtMoney(effectiveSalePrice - premisesTotal)}
                    </span>
                  </div>
                  <div className="flex justify-between bg-[#0ABAB5]/5 -mx-4 -mb-4 px-4 py-3 rounded-b-xl border-t border-[#0ABAB5]/20">
                    <span className="text-[13px] font-bold text-[#0ABAB5]">
                      {salePrice > 0 ? 'Valor de Venda' : 'Preço sugerido (arredondado)'}
                    </span>
                    <span className="text-[16px] font-bold font-mono text-[#0ABAB5]">{fmtMoney(effectiveSalePrice)}</span>
                  </div>
                </div>
              </div>

              {/* Manual price override */}
              <div>
                <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">
                  Valor de Venda Final <span className="text-zinc-400 font-normal">(opcional — ajuste manual)</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[13px] text-zinc-500 font-semibold pointer-events-none">R$</span>
                  <input
                    value={salePriceInput}
                    onChange={e => handleSalePriceChange(e.target.value)}
                    placeholder={suggestedPrice.toString()}
                    inputMode="decimal"
                    className="w-full text-[14px] font-semibold border border-zinc-200 rounded-xl pl-10 pr-3 py-2.5 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
                </div>
                {salePrice > 0 && (
                  <p className="text-[11px] text-zinc-400 mt-1">
                    Valor personalizado. As premissas serão calculadas sobre R$ {salePrice.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* ── Step 3: Preview ───────────────────────────────────────────────── */}
          {step === 'preview' && (
            <div className="space-y-5">
              {/* Quote summary */}
              <div className="bg-zinc-50 rounded-xl border border-zinc-200 p-4 space-y-3">
                <div className="flex justify-between items-start gap-3">
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">Orçamento</p>
                    <p className="text-[15px] font-bold text-zinc-800 mt-0.5 truncate">{title}</p>
                    <p className="text-[12px] text-zinc-500 truncate">{customers.find(c => c.id === customerId)?.name}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide mb-1">Valor de Venda</p>
                    <div className="relative">
                      <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[12px] text-[#0ABAB5] font-bold pointer-events-none">R$</span>
                      <input
                        value={salePriceInput || effectiveSalePrice.toFixed(2).replace('.', ',')}
                        onChange={e => handleSalePriceChange(e.target.value)}
                        inputMode="decimal"
                        className="w-36 text-[16px] font-bold text-[#0ABAB5] font-mono text-right bg-[#0ABAB5]/5 border border-[#0ABAB5]/30 rounded-xl pl-8 pr-2 py-1.5 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all"
                      />
                    </div>
                    <p className="text-[10px] text-zinc-400 mt-1">toque para ajustar</p>
                  </div>
                </div>

                {/* Items list */}
                <div className="space-y-1.5 pt-2 border-t border-zinc-200">
                  <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide mb-2">Itens</p>
                  {validItems.map((item, idx) => (
                    <div key={idx} className="flex justify-between text-[13px]">
                      <span className="text-zinc-600">{item.quantity}× {item.description}</span>
                      <span className="font-semibold font-mono text-zinc-700">{fmtMoney(item.quantity * item.unit_price)}</span>
                    </div>
                  ))}
                  <div className="flex justify-between pt-1 border-t border-zinc-200 mt-1">
                    <span className="text-[12px] font-semibold text-zinc-500">Subtotal itens</span>
                    <span className="text-[12px] font-semibold font-mono text-zinc-600">{fmtMoney(itemsTotal)}</span>
                  </div>
                </div>

                {/* Premises */}
                {premiseBreakdown.length > 0 && (
                  <div className="space-y-1 pt-2 border-t border-zinc-200">
                    <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide mb-2">Premissas Aplicadas</p>
                    {premiseBreakdown.map(p => (
                      <div key={p.id} className="flex justify-between text-[13px]">
                        <span className="text-zinc-500">
                          {p.name}
                          {p.type === 'percentage' && <span className="text-zinc-400 text-[11px] ml-1">({p.value}%)</span>}
                        </span>
                        <span className="font-semibold font-mono text-[#0ABAB5]">{fmtMoney(p.amount)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Profitability Playback */}
              <div className="bg-gradient-to-br from-[#0ABAB5]/5 to-emerald-50 rounded-xl border border-[#0ABAB5]/20 p-4 space-y-4">
                <div className="flex items-center gap-2">
                  <TrendUp size={16} weight="duotone" className="text-[#0ABAB5]" />
                  <p className="text-[13px] font-bold text-zinc-700">Análise de Rentabilidade</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white/70 rounded-xl p-3 border border-white">
                    <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">Margem de Lucro</p>
                    <p className="text-[22px] font-bold text-emerald-600 font-mono mt-0.5">{marginPct.toFixed(1)}%</p>
                    <p className="text-[11px] text-zinc-400 mt-0.5">
                      {fmtMoney(profit)} de lucro bruto
                    </p>
                  </div>
                  <div className="bg-white/70 rounded-xl p-3 border border-white">
                    <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">Custo Real</p>
                    <p className="text-[22px] font-bold text-zinc-700 font-mono mt-0.5">
                      {((itemsTotal / effectiveSalePrice) * 100).toFixed(1)}%
                    </p>
                    <p className="text-[11px] text-zinc-400 mt-0.5">
                      {fmtMoney(itemsTotal)} de custo
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  {[3, 5, 10].map(n => (
                    <div key={n} className="flex items-center justify-between py-2 px-3 bg-white/60 rounded-lg border border-white">
                      <span className="text-[12px] text-zinc-600">
                        Fechando <strong>{n} vendas</strong> assim/mês
                      </span>
                      <span className="text-[13px] font-bold text-emerald-600 font-mono">
                        {fmtMoney(profit * n)}/mês
                      </span>
                    </div>
                  ))}
                </div>

                <div className="bg-white/60 rounded-lg border border-white px-3 py-2.5">
                  <p className="text-[12px] text-zinc-600">
                    <span className="font-semibold text-zinc-700">Viabilidade:</span>{' '}
                    {marginPct >= 30
                      ? 'Excelente margem. Proposta muito competitiva e saudável para o negócio.'
                      : marginPct >= 20
                      ? 'Boa margem. Equilibrio saudável entre competitividade e rentabilidade.'
                      : marginPct >= 10
                      ? 'Margem razoável. Considere revisar custos ou aumentar o preço de venda.'
                      : 'Margem baixa. Recomendamos revisar as premissas de custo antes de enviar.'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer navigation */}
        <div className="flex items-center gap-2 px-5 py-4 border-t border-zinc-100 shrink-0">
          {step === 'items' && (
            <>
              <button type="button" onClick={onClose}
                className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
                Cancelar
              </button>
              <button type="button" onClick={goToPremises} disabled={!canGoNext}
                className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] disabled:opacity-40 py-2.5 rounded-xl transition-colors">
                Premissas <ArrowRight size={14} weight="bold" />
              </button>
            </>
          )}
          {step === 'premises' && (
            <>
              <button type="button" onClick={() => setStep('items')}
                className="flex items-center gap-2 px-4 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
                <ArrowLeft size={14} weight="bold" /> Voltar
              </button>
              <button type="button" onClick={goToPreview}
                className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] py-2.5 rounded-xl transition-colors">
                Revisar <ArrowRight size={14} weight="bold" />
              </button>
            </>
          )}
          {step === 'preview' && (
            <>
              <button type="button" onClick={() => setStep('premises')}
                className="flex items-center gap-2 px-4 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
                <ArrowLeft size={14} weight="bold" /> Voltar
              </button>
              <button type="button" onClick={handleFinish} disabled={saving}
                className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] disabled:opacity-50 py-2.5 rounded-xl transition-colors">
                {saving ? <SpinnerGap size={14} className="animate-spin" /> : <Check size={14} weight="bold" />}
                Gerar Orçamento
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ── PDF Modal ──────────────────────────────────────────────────────────────────

interface PdfModalProps {
  quote: Quote
  onClose: () => void
}

function PdfModal({ quote, onClose }: PdfModalProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  async function download() {
    setLoading(true)
    setError('')
    try {
      const data = await quotesApi.downloadPdf(quote.id)
      const blob = new Blob([data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `proposta-${quote.customer_name ?? quote.id}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erro ao gerar PDF.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100">
          <div>
            <h2 className="text-[15px] font-bold text-[#1D1D1F]">Baixar Proposta PDF</h2>
            <p className="text-[12px] text-zinc-400 mt-0.5">{quote.customer_name ?? '—'} · {quote.title}</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
            <X size={16} weight="bold" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div className="flex items-start gap-3 p-4 bg-[#F0FEFE] rounded-xl border border-[#0ABAB5]/20">
            <FilePdf size={22} weight="duotone" className="text-[#0ABAB5] shrink-0 mt-0.5" />
            <div>
              <p className="text-[13px] font-semibold text-[#1D1D1F]">{quote.title}</p>
              <p className="text-[12px] text-zinc-500 mt-0.5">
                Proposta gerada automaticamente com os dados do orçamento.
              </p>
            </div>
          </div>

          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 rounded-xl border border-red-100">
              <Warning size={14} className="text-red-500 shrink-0 mt-0.5" />
              <p className="text-[12px] text-red-600">{error}</p>
            </div>
          )}

          <div className="flex items-center gap-2 pt-1">
            <button onClick={onClose}
              className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
              Cancelar
            </button>
            <button onClick={download} disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] disabled:opacity-50 py-2.5 rounded-xl transition-colors">
              {loading ? <SpinnerGap size={14} className="animate-spin" /> : <DownloadSimple size={14} weight="bold" />}
              Baixar Proposta PDF
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Edit Status Modal ──────────────────────────────────────────────────────────

interface EditModalProps {
  quote: Quote
  onClose: () => void
  onSave: (status: QuoteStatus) => void
  saving: boolean
}

function EditModal({ quote, onClose, onSave, saving }: EditModalProps) {
  const [status, setStatus] = useState<QuoteStatus>(quote.status)
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100">
          <h2 className="text-[15px] font-bold text-[#1D1D1F]">Editar Status</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
            <X size={16} weight="bold" />
          </button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <p className="text-[12px] font-semibold text-zinc-500 mb-0.5">Cliente</p>
            <p className="text-[14px] text-zinc-800 font-medium">{quote.customer_name ?? '—'}</p>
          </div>
          <div>
            <p className="text-[12px] font-semibold text-zinc-500 mb-0.5">Descrição</p>
            <p className="text-[14px] text-zinc-800">{quote.title}</p>
          </div>

          {/* Premises breakdown if available */}
          {quote.applied_premises && quote.applied_premises.length > 0 && (
            <div className="bg-zinc-50 rounded-xl border border-zinc-100 p-3 space-y-1.5">
              <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide mb-2">Composição do Valor</p>
              <div className="flex justify-between text-[12px]">
                <span className="text-zinc-500">Custo dos itens</span>
                <span className="font-mono font-semibold text-zinc-700">{fmtMoney(quote.subtotal)}</span>
              </div>
              {quote.applied_premises.map((ap, i) => (
                <div key={i} className="flex justify-between text-[12px]">
                  <span className="text-zinc-400">
                    + {ap.name}
                    {ap.type === 'percent' && <span className="text-zinc-300 text-[10px] ml-1">({ap.value}%)</span>}
                  </span>
                  <span className="font-mono font-semibold text-[#0ABAB5]">+{fmtMoney(ap.amount)}</span>
                </div>
              ))}
              <div className="flex justify-between pt-2 border-t border-zinc-200 text-[13px]">
                <span className="font-semibold text-zinc-700">Total de Venda</span>
                <span className="font-bold font-mono text-[#0ABAB5]">{fmtVal(quote.total)}</span>
              </div>
            </div>
          )}

          {(!quote.applied_premises || quote.applied_premises.length === 0) && (
            <div>
              <p className="text-[12px] font-semibold text-zinc-500 mb-0.5">Valor Total</p>
              <p className="text-[16px] font-bold text-[#0ABAB5] font-mono">{fmtVal(quote.total)}</p>
            </div>
          )}

          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Status</label>
            <select value={status} onChange={e => setStatus(e.target.value as QuoteStatus)}
              className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all bg-white">
              {STATUSES.map(s => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <button onClick={onClose}
              className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
              Cancelar
            </button>
            <button onClick={() => onSave(status)} disabled={saving || status === quote.status}
              className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] disabled:opacity-50 py-2.5 rounded-xl transition-colors">
              {saving ? <SpinnerGap size={14} className="animate-spin" /> : <Check size={14} weight="bold" />}
              Salvar
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Delete Confirm ─────────────────────────────────────────────────────────────

function DeleteConfirm({ nome, onConfirm, onCancel }: { nome: string; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onCancel}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-5" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center shrink-0">
            <Trash size={18} weight="duotone" className="text-red-500" />
          </div>
          <div>
            <p className="text-[14px] font-bold text-[#1D1D1F]">Excluir orçamento</p>
            <p className="text-[12px] text-zinc-400">Esta ação não pode ser desfeita</p>
          </div>
        </div>
        <p className="text-[13px] text-zinc-600 mb-5">
          Tem certeza que deseja excluir o orçamento de <strong>{nome}</strong>?
        </p>
        <div className="flex items-center gap-2">
          <button onClick={onCancel}
            className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
            Cancelar
          </button>
          <button onClick={onConfirm}
            className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-red-500 hover:bg-red-600 py-2.5 rounded-xl transition-colors">
            <Trash size={14} weight="bold" /> Excluir
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Action Menu ────────────────────────────────────────────────────────────────

function ActionMenu({
  onEdit, onDelete, onPdf, onClose,
}: { onEdit: () => void; onDelete: () => void; onPdf: () => void; onClose: () => void }) {
  return (
    <>
      <div className="fixed inset-0 z-40" onClick={onClose} />
      <div className="absolute right-0 top-full mt-1 w-44 bg-white rounded-xl border border-zinc-100 shadow-lg py-1 z-50">
        <button onClick={() => { onEdit(); onClose() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-zinc-600 hover:bg-zinc-50 transition-colors">
          <PencilSimple size={14} /> Editar Status
        </button>
        <button onClick={() => { onPdf(); onClose() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-[#0ABAB5] hover:bg-[#0ABAB5]/5 transition-colors">
          <FilePdf size={14} weight="bold" /> Gerar PDF / Enviar
        </button>
        <div className="border-t border-zinc-100 my-1" />
        <button onClick={() => { onDelete(); onClose() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-red-500 hover:bg-red-50 transition-colors">
          <Trash size={14} /> Excluir
        </button>
      </div>
    </>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function QuotesPage() {
  const queryClient = useQueryClient()
  const [tab, setTab]               = useState<FilterTab>('Todos')
  const [modal, setModal]           = useState<'create' | Quote | null>(null)
  const [pdfTarget, setPdfTarget]   = useState<Quote | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Quote | null>(null)
  const [menuOpen, setMenuOpen]     = useState<string | null>(null)
  const [search, setSearch]         = useState('')

  const { data: quotes = [], isLoading } = useQuery<Quote[]>({
    queryKey: ['quotes'],
    queryFn: () => quotesApi.list({ limit: 200 }),
  })

  const createMutation = useMutation({
    mutationFn: (data: CreateQuotePayload) => quotesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      setModal(null)
    },
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: QuoteStatus }) =>
      quotesApi.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      setModal(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => quotesApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      setDeleteTarget(null)
    },
  })

  const searchFiltered = search
    ? quotes.filter(q =>
        (q.customer_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
        q.title.toLowerCase().includes(search.toLowerCase()))
    : quotes
  const filtered = tab === 'Todos' ? searchFiltered : searchFiltered.filter(q => q.status === tab)

  const total      = quotes.length
  const aguardando = quotes.filter(q => q.status === 'sent').length
  const potencial  = quotes.filter(q => q.status !== 'rejected').reduce((s, q) => s + q.total, 0)

  return (
    <div className="p-4 md:p-6 space-y-5 pb-6">

      {/* Modals */}
      {modal === 'create' && (
        <WizardModal
          onClose={() => setModal(null)}
          onSave={data => createMutation.mutate(data)}
          saving={createMutation.isPending}
        />
      )}
      {modal !== null && modal !== 'create' && (
        <EditModal
          quote={modal}
          onClose={() => setModal(null)}
          onSave={status => updateStatusMutation.mutate({ id: (modal as Quote).id, status })}
          saving={updateStatusMutation.isPending}
        />
      )}
      {pdfTarget && (
        <PdfModal quote={pdfTarget} onClose={() => setPdfTarget(null)} />
      )}
      {deleteTarget && (
        <DeleteConfirm
          nome={deleteTarget.customer_name ?? deleteTarget.title}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
          onCancel={() => setDeleteTarget(null)}
        />
      )}

      {/* Header */}
      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100 flex items-center justify-between">
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight">Orçamentos</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={async () => {
              try {
                const data = await quotesApi.exportReport()
                const blob = new Blob([data], { type: 'application/pdf' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url; a.download = 'relatorio-orcamentos.pdf'; a.click()
                URL.revokeObjectURL(url)
              } catch (e) { console.error('PDF export failed', e) }
            }}
            className="flex items-center gap-2 border border-zinc-200 hover:bg-zinc-50 text-zinc-600 text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95"
          >
            <FilePdf size={15} weight="bold" />
            <span className="hidden sm:inline">Relatório PDF</span>
          </button>
          <button onClick={() => setModal('create')}
            className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#09a8a3] text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95">
            <Plus size={15} weight="bold" />
            <span className="hidden sm:inline">Novo Orçamento</span>
            <span className="sm:hidden">Novo</span>
          </button>
        </div>
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

      {/* Search */}
      <div className="flex items-center gap-2 bg-white border border-zinc-200 rounded-xl px-3 py-2 focus-within:border-[#0ABAB5]/50 transition-all">
        <MagnifyingGlass size={14} className="text-zinc-400 shrink-0" />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar orçamentos..."
          className="text-[13px] bg-transparent focus:outline-none w-full placeholder:text-zinc-400" />
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-1.5 overflow-x-auto pb-0.5 scrollbar-none">
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`shrink-0 text-[12px] font-semibold px-3.5 py-1.5 rounded-xl border transition-all ${
              tab === t ? 'bg-[#0ABAB5] text-white border-[#0ABAB5]' : 'bg-white text-zinc-500 border-zinc-200 hover:border-zinc-300'
            }`}>
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 overflow-visible">
        <div className="hidden md:grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3 border-b border-zinc-100 bg-zinc-50/60">
          {['Cliente', 'Descrição', 'Data', 'Valor', 'Status', ''].map(h => (
            <p key={h} className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">{h}</p>
          ))}
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <SpinnerGap size={24} className="animate-spin text-[#0ABAB5]" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center py-16 text-zinc-300">
            <FileText size={40} weight="duotone" />
            <p className="text-sm mt-2 text-zinc-400">Nenhum orçamento encontrado</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-100">
            {filtered.map(q => (
              <div key={q.id}>
                {/* Desktop row */}
                <div className="hidden md:grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3.5 items-center hover:bg-zinc-50/60 transition-colors group cursor-pointer"
                  onClick={() => setModal(q)}>
                  <div>
                    <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{q.customer_name ?? '—'}</p>
                    {q.applied_premises && q.applied_premises.length > 0 && (
                      <p className="text-[10px] text-zinc-400 mt-0.5">{q.applied_premises.length} premissa{q.applied_premises.length !== 1 ? 's' : ''}</p>
                    )}
                  </div>
                  <p className="text-[13px] text-zinc-500 truncate">{q.title}</p>
                  <p className="text-[13px] text-zinc-500">{fmtDate(q.created_at)}</p>
                  <p className="text-[13px] font-bold text-[#0ABAB5] font-mono">{fmtVal(q.total)}</p>
                  <span className={`inline-flex text-[11px] font-semibold px-2 py-0.5 rounded-full w-fit ${STATUS_STYLES[q.status]}`}>
                    {STATUS_LABEL[q.status]}
                  </span>
                  <div className="relative" onClick={e => e.stopPropagation()}>
                    <button onClick={() => setMenuOpen(menuOpen === q.id ? null : q.id)}
                      className="p-1.5 rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-600 transition-all">
                      <DotsThreeVertical size={16} weight="bold" />
                    </button>
                    {menuOpen === q.id && (
                      <ActionMenu
                        onEdit={() => setModal(q)}
                        onDelete={() => setDeleteTarget(q)}
                        onPdf={() => setPdfTarget(q)}
                        onClose={() => setMenuOpen(null)}
                      />
                    )}
                  </div>
                </div>

                {/* Mobile card */}
                <div className="md:hidden p-4 active:bg-zinc-50 transition-colors cursor-pointer" onClick={() => setModal(q)}>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="min-w-0">
                      <p className="text-[14px] font-semibold text-[#1D1D1F] truncate">{q.customer_name ?? '—'}</p>
                      <p className="text-[12px] text-zinc-400 truncate mt-0.5">{q.title}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${STATUS_STYLES[q.status]}`}>
                        {STATUS_LABEL[q.status]}
                      </span>
                      <div onClick={e => e.stopPropagation()}>
                        <button onClick={() => setMenuOpen(menuOpen === q.id ? null : q.id)} className="p-1 rounded-lg hover:bg-zinc-100 text-zinc-400">
                          <DotsThreeVertical size={15} weight="bold" />
                        </button>
                        {menuOpen === q.id && (
                          <ActionMenu
                            onEdit={() => setModal(q)}
                            onDelete={() => setDeleteTarget(q)}
                            onPdf={() => setPdfTarget(q)}
                            onClose={() => setMenuOpen(null)}
                          />
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-zinc-100">
                    <div className="flex items-center gap-2">
                      <p className="text-[12px] text-zinc-400">{fmtDate(q.created_at)}</p>
                      {q.applied_premises && q.applied_premises.length > 0 && (
                        <span className="text-[10px] text-zinc-400 bg-zinc-100 px-1.5 py-0.5 rounded-full">
                          {q.applied_premises.length} premissa{q.applied_premises.length !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                    <p className="text-[14px] font-bold text-[#0ABAB5] font-mono">{fmtVal(q.total)}</p>
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
            {fmtVal(filtered.reduce((s, q) => s + q.total, 0))} total
          </div>
        </div>
      )}
    </div>
  )
}

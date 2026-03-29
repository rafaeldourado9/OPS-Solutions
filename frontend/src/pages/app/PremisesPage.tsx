import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, PencilSimple, Trash, Percent, CurrencyDollar,
  SpinnerGap, WarningCircle, X, Check, ArrowsClockwise,
} from '@phosphor-icons/react'
import { premisesApi, type Premise, type PremiseType, type CreatePremisePayload } from '../../api/premises'

function fmtCurrency(v: number) {
  return `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
}

function fmtValue(type: PremiseType, value: number, _cost?: number): string {
  if (type === 'percentage') return `${value.toFixed(1).replace('.', ',')}%`
  if (type === 'multiplier') return `${value.toFixed(2).replace('.', ',')}×`
  return fmtCurrency(value)
}

// ─── Modal ────────────────────────────────────────────────────────────────────
interface ModalProps {
  initial?: Premise
  onClose: () => void
  onSave: (data: CreatePremisePayload) => void
  saving: boolean
}

function PremiseModal({ initial, onClose, onSave, saving }: ModalProps) {
  const [name, setName] = useState(initial?.name ?? '')
  const [type, setType] = useState<PremiseType>(initial?.type ?? 'percentage')
  const [value, setValue] = useState(initial?.value.toString() ?? '')
  const [cost, setCost] = useState(initial?.cost?.toString() ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')

  const numVal = parseFloat(value.replace(',', '.'))
  const numCost = parseFloat(cost.replace(',', '.'))
  const previewAmount = type === 'multiplier' && !isNaN(numCost) && !isNaN(numVal) && numCost > 0
    ? numCost * numVal
    : null

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || isNaN(numVal) || numVal <= 0) return
    if (type === 'multiplier' && (isNaN(numCost) || numCost <= 0)) return
    onSave({
      name: name.trim(),
      type,
      value: numVal,
      cost: type === 'multiplier' ? numCost : 0,
      description: description.trim(),
    })
  }

  const typeButtons: { key: PremiseType; label: string; icon: React.ReactNode }[] = [
    { key: 'percentage', label: 'Percentual', icon: <Percent size={13} weight="bold" /> },
    { key: 'fixed',      label: 'Valor Fixo', icon: <CurrencyDollar size={13} weight="bold" /> },
    { key: 'multiplier', label: 'Multiplicador', icon: <ArrowsClockwise size={13} weight="bold" /> },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100">
          <h2 className="text-[15px] font-bold text-[#1D1D1F]">
            {initial ? 'Editar Premissa' : 'Nova Premissa'}
          </h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
            <X size={16} weight="bold" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Name */}
          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Nome *</label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Ex: Painel Solar 550W, ICMS, Mão de Obra"
              className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all"
              required
              autoFocus
            />
          </div>

          {/* Type toggle */}
          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Tipo *</label>
            <div className="flex rounded-xl border border-zinc-200 overflow-hidden">
              {typeButtons.map(({ key, label, icon }, i) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setType(key)}
                  className={`flex-1 flex items-center justify-center gap-1.5 text-[12px] font-semibold py-2 transition-colors ${
                    i > 0 ? 'border-l border-zinc-200' : ''
                  } ${
                    type === key ? 'bg-[#0ABAB5] text-white' : 'bg-white text-zinc-500 hover:bg-zinc-50'
                  }`}
                >
                  {icon}{label}
                </button>
              ))}
            </div>
            <p className="text-[11px] text-zinc-400 mt-1.5 leading-relaxed">
              {type === 'percentage' && 'Aplica um percentual sobre o total dos itens do orçamento.'}
              {type === 'fixed' && 'Adiciona um valor fixo ao total, independente dos itens.'}
              {type === 'multiplier' && 'Multiplica o custo de um material/serviço para obter o preço de venda.'}
            </p>
          </div>

          {/* Multiplier: two fields */}
          {type === 'multiplier' ? (
            <div className="space-y-3">
              <div>
                <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">
                  Preço de custo (R$) *
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[13px] text-zinc-400 font-semibold pointer-events-none">R$</span>
                  <input
                    value={cost}
                    onChange={e => setCost(e.target.value)}
                    placeholder="0,00"
                    className="w-full text-[14px] border border-zinc-200 rounded-xl pl-10 pr-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all"
                    required
                    inputMode="decimal"
                  />
                </div>
              </div>
              <div>
                <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">
                  Fator multiplicador *
                </label>
                <div className="relative">
                  <input
                    value={value}
                    onChange={e => setValue(e.target.value)}
                    placeholder="Ex: 2.5"
                    className="w-full text-[14px] border border-zinc-200 rounded-xl pl-3 pr-9 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all"
                    required
                    inputMode="decimal"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[13px] text-zinc-400 font-semibold pointer-events-none">×</span>
                </div>
              </div>

              {/* Live preview */}
              {previewAmount !== null && (
                <div className="flex items-center justify-between bg-[#0ABAB5]/8 border border-[#0ABAB5]/20 rounded-xl px-4 py-2.5">
                  <span className="text-[12px] text-zinc-500">
                    {fmtCurrency(numCost)} × {numVal.toFixed(2)}× =
                  </span>
                  <span className="text-[15px] font-bold text-[#0ABAB5] font-mono">
                    {fmtCurrency(previewAmount)}
                  </span>
                </div>
              )}
            </div>
          ) : (
            /* Percentage / Fixed: single field */
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">
                {type === 'percentage' ? 'Percentual (%) *' : 'Valor (R$) *'}
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[13px] text-zinc-400 font-semibold pointer-events-none">
                  {type === 'percentage' ? '%' : 'R$'}
                </span>
                <input
                  value={value}
                  onChange={e => setValue(e.target.value)}
                  placeholder={type === 'percentage' ? '0,0' : '0,00'}
                  className="w-full text-[14px] border border-zinc-200 rounded-xl pl-9 pr-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all"
                  required
                  inputMode="decimal"
                />
              </div>
            </div>
          )}

          {/* Description */}
          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Descrição</label>
            <input
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Opcional"
              className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2 rounded-xl hover:bg-zinc-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving || !name.trim() || !value}
              className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] disabled:opacity-50 py-2 rounded-xl transition-colors"
            >
              {saving ? <SpinnerGap size={14} className="animate-spin" /> : <Check size={14} weight="bold" />}
              {initial ? 'Salvar' : 'Criar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Card ─────────────────────────────────────────────────────────────────────
function PremiseCard({
  premise, onEdit, onDelete, deleting,
}: {
  premise: Premise
  onEdit: (p: Premise) => void
  onDelete?: (id: string) => void
  deleting?: boolean
}) {
  const isMultiplier = premise.type === 'multiplier'
  const iconBg = premise.type === 'percentage' ? 'bg-[#0ABAB5]/10' : isMultiplier ? 'bg-amber-50' : 'bg-violet-50'
  const icon = premise.type === 'percentage'
    ? <Percent size={18} weight="duotone" className="text-[#0ABAB5]" />
    : isMultiplier
      ? <ArrowsClockwise size={18} weight="duotone" className="text-amber-500" />
      : <CurrencyDollar size={18} weight="duotone" className="text-violet-500" />

  const valueColor = premise.type === 'percentage' ? 'text-[#0ABAB5]' : isMultiplier ? 'text-amber-600' : 'text-violet-600'
  const typeLabel = premise.type === 'percentage' ? 'Percentual' : isMultiplier ? 'Multiplicador' : 'Valor fixo'

  return (
    <div className="bg-white rounded-2xl p-4 border border-zinc-100 shadow-sm flex items-start gap-4">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${iconBg}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          <p className="text-[14px] font-bold text-[#1D1D1F] truncate">{premise.name}</p>
          <div className="flex items-center gap-1 shrink-0">
            <button onClick={() => onEdit(premise)} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
              <PencilSimple size={14} weight="bold" />
            </button>
            {onDelete && (
              <button
                onClick={() => onDelete(premise.id)}
                disabled={deleting}
                className="p-1.5 rounded-lg hover:bg-red-50 text-zinc-400 hover:text-red-500 disabled:opacity-50 transition-colors"
              >
                {deleting ? <SpinnerGap size={14} className="animate-spin" /> : <Trash size={14} weight="bold" />}
              </button>
            )}
          </div>
        </div>

        {premise.description && (
          <p className="text-[12px] text-zinc-400 leading-snug mb-2">{premise.description}</p>
        )}

        <div className="flex items-center gap-2 flex-wrap mt-1.5">
          <span className={`text-[14px] font-bold font-mono ${valueColor}`}>
            {fmtValue(premise.type, premise.value, premise.cost)}
          </span>

          {isMultiplier && premise.cost > 0 && (
            <>
              <span className="text-[12px] text-zinc-300">·</span>
              <span className="text-[12px] text-zinc-500 font-mono">
                custo {fmtCurrency(premise.cost)}
              </span>
              <span className="text-[12px] text-zinc-300">·</span>
              <span className="text-[12px] font-semibold text-amber-600 font-mono">
                = {fmtCurrency(premise.cost * premise.value)}
              </span>
            </>
          )}

          <span className="text-[11px] px-2 py-0.5 rounded-full font-semibold bg-zinc-100 text-zinc-500">
            {typeLabel}
          </span>
          {!premise.is_active && (
            <span className="text-[11px] px-2 py-0.5 rounded-full font-semibold bg-zinc-100 text-zinc-400">Inativa</span>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function PremisesPage() {
  const qc = useQueryClient()
  const [modal, setModal] = useState<'create' | Premise | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const { data: premises = [], isLoading, isError } = useQuery({
    queryKey: ['premises'],
    queryFn: premisesApi.list,
  })

  const createMutation = useMutation({
    mutationFn: (data: CreatePremisePayload) => premisesApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['premises'] }); setModal(null) },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: CreatePremisePayload }) => premisesApi.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['premises'] }); setModal(null) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => premisesApi.remove(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['premises'] }); setDeletingId(null) },
  })

  function handleSave(data: CreatePremisePayload) {
    if (modal === 'create') createMutation.mutate(data)
    else if (modal && typeof modal === 'object') updateMutation.mutate({ id: modal.id, data })
  }

  const totalPercent = premises
    .filter((p: Premise) => p.type === 'percentage' && p.is_active)
    .reduce((s: number, p: Premise) => s + p.value, 0)

  const totalMultiplier = premises
    .filter((p: Premise) => p.type === 'multiplier' && p.is_active)
    .reduce((s: number, p: Premise) => s + p.cost * p.value, 0)

  const isSaving = createMutation.isPending || updateMutation.isPending

  return (
    <div className="p-4 md:p-6 space-y-6 pb-6">

      {modal !== null && (
        <PremiseModal
          initial={modal === 'create' ? undefined : modal}
          onClose={() => setModal(null)}
          onSave={handleSave}
          saving={isSaving}
        />
      )}

      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100 flex items-center justify-between">
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight">Premissas</h1>
        <button
          onClick={() => setModal('create')}
          className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#09a8a3] text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95"
        >
          <Plus size={15} weight="bold" />
          <span className="hidden sm:inline">Nova Premissa</span>
          <span className="sm:hidden">Nova</span>
        </button>
      </div>

      <p className="text-[13px] text-zinc-500 leading-relaxed">
        Configure os percentuais, valores fixos e multiplicadores de custo aplicados nos orçamentos.
      </p>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="flex items-center gap-3 p-4 bg-[#0ABAB5]/8 rounded-2xl border border-[#0ABAB5]/20">
          <div className="w-9 h-9 rounded-xl bg-[#0ABAB5]/15 flex items-center justify-center shrink-0">
            <Percent size={16} weight="duotone" className="text-[#0ABAB5]" />
          </div>
          <div>
            <p className="text-[15px] font-bold text-[#0ABAB5] font-mono">
              {totalPercent.toFixed(1).replace('.', ',')}%
            </p>
            <p className="text-[11px] text-zinc-500">Encargos percentuais</p>
          </div>
        </div>
        <div className="flex items-center gap-3 p-4 bg-amber-50 rounded-2xl border border-amber-100">
          <div className="w-9 h-9 rounded-xl bg-amber-100 flex items-center justify-center shrink-0">
            <ArrowsClockwise size={16} weight="duotone" className="text-amber-500" />
          </div>
          <div>
            <p className="text-[15px] font-bold text-amber-600 font-mono">
              {fmtCurrency(totalMultiplier)}
            </p>
            <p className="text-[11px] text-zinc-500">Total multiplicadores</p>
          </div>
        </div>
      </div>

      {/* List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <SpinnerGap size={28} className="text-[#0ABAB5] animate-spin" />
        </div>
      ) : isError ? (
        <div className="flex flex-col items-center py-12 text-zinc-400 gap-2">
          <WarningCircle size={32} weight="duotone" className="text-red-400" />
          <p className="text-[13px]">Erro ao carregar premissas</p>
        </div>
      ) : premises.length === 0 ? (
        <div className="flex flex-col items-center py-16 bg-white rounded-2xl border border-dashed border-zinc-200 text-zinc-300 gap-2">
          <Percent size={36} weight="duotone" />
          <p className="text-[14px] text-zinc-400 font-medium">Nenhuma premissa cadastrada</p>
          <p className="text-[12px] text-zinc-400">Clique em "Nova Premissa" para começar</p>
        </div>
      ) : (
        <section className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <p className="text-[12px] font-bold text-zinc-400 uppercase tracking-widest">Premissas</p>
            <p className="text-[12px] text-zinc-400">{premises.length} cadastrada{premises.length !== 1 ? 's' : ''}</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {premises.map((p: Premise) => (
              <PremiseCard
                key={p.id}
                premise={p}
                onEdit={p => setModal(p)}
                onDelete={id => { setDeletingId(id); deleteMutation.mutate(id) }}
                deleting={deletingId === p.id && deleteMutation.isPending}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

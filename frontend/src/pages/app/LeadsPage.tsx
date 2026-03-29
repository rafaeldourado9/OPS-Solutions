import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, DotsThreeVertical, CurrencyDollar, MagnifyingGlass,
  SpinnerGap, WarningCircle, X, Check, PencilSimple, Trash,
  ArrowRight, Funnel, CaretLeft, CaretRight, XCircle,
} from '@phosphor-icons/react'
import { leadsApi, type Lead, type LeadStage, type CreateLeadPayload, type LeadListResponse } from '../../api/leads'
import { customersApi, type Customer, type CustomerListResponse } from '../../api/customers'

// ─── Constants ─────────────────────────────────────────────────────────────────

const STAGES: { id: LeadStage; label: string; color: string; dot: string }[] = [
  { id: 'new',         label: 'Novos',        color: 'bg-zinc-100 text-zinc-600',    dot: 'bg-zinc-400' },
  { id: 'contacted',   label: 'Contatados',   color: 'bg-blue-50 text-blue-600',     dot: 'bg-blue-400' },
  { id: 'qualified',   label: 'Qualificados', color: 'bg-violet-50 text-violet-600', dot: 'bg-violet-400' },
  { id: 'proposal',    label: 'Proposta',     color: 'bg-amber-50 text-amber-600',   dot: 'bg-amber-400' },
  { id: 'negotiation', label: 'Negociação',   color: 'bg-orange-50 text-orange-600', dot: 'bg-orange-400' },
  { id: 'won',         label: 'Ganhos',       color: 'bg-emerald-50 text-emerald-600', dot: 'bg-emerald-400' },
  { id: 'lost',        label: 'Perdidos',     color: 'bg-red-50 text-red-500',       dot: 'bg-red-400' },
]

const STAGE_MAP = Object.fromEntries(STAGES.map(s => [s.id, s]))

const VALID_TRANSITIONS: Record<LeadStage, LeadStage[]> = {
  new:         ['contacted', 'lost'],
  contacted:   ['qualified', 'lost'],
  qualified:   ['proposal', 'lost'],
  proposal:    ['negotiation', 'lost'],
  negotiation: ['won', 'lost'],
  won:         [],
  lost:        ['new'],
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

const COLORS = ['bg-[#0ABAB5]', 'bg-violet-500', 'bg-orange-500', 'bg-rose-500', 'bg-blue-500', 'bg-emerald-600']

function Av({ name, size = 7 }: { name: string; size?: number }) {
  const initials = name.split(' ').filter(Boolean).map(w => w[0]).slice(0, 2).join('').toUpperCase()
  const c = COLORS[initials.charCodeAt(0) % COLORS.length]
  return (
    <div className={`w-${size} h-${size} text-[${size < 8 ? 10 : 11}px] ${c} rounded-full flex items-center justify-center text-white font-bold shrink-0`}
      style={{ width: size * 4, height: size * 4, fontSize: size < 8 ? 10 : 11 }}>
      {initials}
    </div>
  )
}

function fmt(n: number) { return n >= 1000 ? 'R$ ' + (n / 1000).toFixed(n >= 10000 ? 0 : 1) + 'k' : 'R$ ' + n.toFixed(0) }

function daysSince(iso: string) {
  return Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 86400000))
}

// ─── Lead Modal ────────────────────────────────────────────────────────────────

interface ModalProps {
  initial?: Lead
  onClose: () => void
  onSave: (data: CreateLeadPayload) => void
  saving: boolean
}

function LeadModal({ initial, onClose, onSave, saving }: ModalProps) {
  const [title, setTitle] = useState(initial?.title ?? '')
  const [value, setValue] = useState(initial?.value?.toString() ?? '')
  const [customerId, setCustomerId] = useState(initial?.customer_id ?? '')
  const [notes, setNotes] = useState(initial?.notes ?? '')
  const [source, setSource] = useState(initial?.source ?? 'manual')
  const [customerSearch, setCustomerSearch] = useState('')

  const { data: customers } = useQuery<CustomerListResponse>({
    queryKey: ['customers-select', customerSearch],
    queryFn: () => customersApi.list({ search: customerSearch || undefined, limit: 10 }),
    staleTime: 30_000,
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    const numVal = parseFloat(value.replace(',', '.')) || 0
    onSave({
      title: title.trim(),
      value: numVal,
      customer_id: customerId || undefined,
      notes: notes.trim(),
      source,
    })
  }

  const selectedCustomer = customers?.items?.find((c: Customer) => c.id === customerId)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100">
          <h2 className="text-[15px] font-bold text-[#1D1D1F]">
            {initial ? 'Editar Lead' : 'Novo Lead'}
          </h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
            <X size={16} weight="bold" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Título *</label>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Ex: Proposta comercial - Empresa X"
              className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" required autoFocus />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Valor (R$)</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[13px] text-zinc-400 font-semibold pointer-events-none">R$</span>
                <input value={value} onChange={e => setValue(e.target.value)} placeholder="0,00" inputMode="decimal"
                  className="w-full text-[14px] border border-zinc-200 rounded-xl pl-9 pr-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
              </div>
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Origem</label>
              <select value={source} onChange={e => setSource(e.target.value)}
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all bg-white">
                <option value="manual">Manual</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="website">Website</option>
                <option value="referral">Indicação</option>
              </select>
            </div>
          </div>

          {/* Customer picker */}
          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Cliente</label>
            {customerId && selectedCustomer ? (
              <div className="flex items-center justify-between bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2">
                <span className="text-[14px] text-[#1D1D1F]">{selectedCustomer.name}</span>
                <button type="button" onClick={() => setCustomerId('')} className="p-0.5 hover:bg-zinc-200 rounded-lg transition-colors">
                  <X size={14} className="text-zinc-400" />
                </button>
              </div>
            ) : (
              <div className="relative">
                <input value={customerSearch} onChange={e => setCustomerSearch(e.target.value)} placeholder="Buscar cliente..."
                  className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
                {customerSearch && customers?.items && customers.items.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl border border-zinc-200 shadow-lg max-h-40 overflow-y-auto z-10">
                    {customers.items.map((c: Customer) => (
                      <button key={c.id} type="button" onClick={() => { setCustomerId(c.id); setCustomerSearch('') }}
                        className="w-full text-left px-3 py-2 text-[13px] hover:bg-zinc-50 transition-colors flex items-center gap-2">
                        <span className="font-medium text-[#1D1D1F]">{c.name}</span>
                        {c.company_name && <span className="text-zinc-400 text-[11px]">{c.company_name}</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Observações</label>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Notas sobre o lead..." rows={2}
              className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all resize-none" />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={saving || !title.trim()}
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

// ─── Move Stage Modal ──────────────────────────────────────────────────────────

function MoveStageModal({ lead, onClose, onMove, moving }: { lead: Lead; onClose: () => void; onMove: (stage: LeadStage, reason?: string) => void; moving: boolean }) {
  const [lostReason, setLostReason] = useState('')
  const [selected, setSelected] = useState<LeadStage | null>(null)
  const targets = VALID_TRANSITIONS[lead.stage] ?? []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100">
          <h2 className="text-[15px] font-bold text-[#1D1D1F]">Mover Lead</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
            <X size={16} weight="bold" />
          </button>
        </div>
        <div className="p-5 space-y-3">
          <p className="text-[13px] text-zinc-500">
            <strong>{lead.title}</strong> está em <span className={`inline-flex text-[11px] font-semibold px-2 py-0.5 rounded-full ${STAGE_MAP[lead.stage]?.color}`}>{STAGE_MAP[lead.stage]?.label}</span>
          </p>
          <p className="text-[12px] font-semibold text-zinc-400 uppercase tracking-wide">Mover para:</p>
          <div className="flex flex-wrap gap-2">
            {targets.map(s => {
              const st = STAGE_MAP[s]
              return (
                <button key={s} onClick={() => setSelected(s)}
                  className={`flex items-center gap-1.5 text-[12px] font-semibold px-3 py-2 rounded-xl border transition-all ${
                    selected === s ? 'bg-[#0ABAB5] text-white border-[#0ABAB5]' : `${st.color} border-current/20 hover:opacity-80`
                  }`}>
                  <ArrowRight size={12} weight="bold" />
                  {st.label}
                </button>
              )
            })}
          </div>

          {selected === 'lost' && (
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Motivo da perda</label>
              <input value={lostReason} onChange={e => setLostReason(e.target.value)} placeholder="Por que o lead foi perdido?"
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" autoFocus />
            </div>
          )}

          {targets.length === 0 && (
            <p className="text-[13px] text-zinc-400 py-2">Este lead não pode ser movido.</p>
          )}

          <div className="flex items-center gap-2 pt-1">
            <button onClick={onClose}
              className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
              Cancelar
            </button>
            <button onClick={() => selected && onMove(selected, selected === 'lost' ? lostReason : undefined)} disabled={!selected || moving}
              className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] disabled:opacity-50 py-2.5 rounded-xl transition-colors">
              {moving ? <SpinnerGap size={14} className="animate-spin" /> : <ArrowRight size={14} weight="bold" />}
              Mover
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Delete Confirm ────────────────────────────────────────────────────────────

function DeleteConfirm({ title, onConfirm, onCancel, deleting }: { title: string; onConfirm: () => void; onCancel: () => void; deleting: boolean }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onCancel}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-5" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center shrink-0">
            <Trash size={18} weight="duotone" className="text-red-500" />
          </div>
          <div>
            <p className="text-[14px] font-bold text-[#1D1D1F]">Excluir lead</p>
            <p className="text-[12px] text-zinc-400">Esta ação não pode ser desfeita</p>
          </div>
        </div>
        <p className="text-[13px] text-zinc-600 mb-5">
          Tem certeza que deseja excluir <strong>{title}</strong>?
        </p>
        <div className="flex items-center gap-2">
          <button onClick={onCancel}
            className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
            Cancelar
          </button>
          <button onClick={onConfirm} disabled={deleting}
            className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-red-500 hover:bg-red-600 disabled:opacity-50 py-2.5 rounded-xl transition-colors">
            {deleting ? <SpinnerGap size={14} className="animate-spin" /> : <Trash size={14} weight="bold" />}
            Excluir
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Action Menu ───────────────────────────────────────────────────────────────

function ActionMenu({ onEdit, onMove, onDelete, onClose }: { onEdit: () => void; onMove: () => void; onDelete: () => void; onClose: () => void }) {
  return (
    <>
      <div className="fixed inset-0 z-40" onClick={onClose} />
      <div className="absolute right-0 top-full mt-1 w-44 bg-white rounded-xl border border-zinc-100 shadow-lg py-1 z-50">
        <button onClick={() => { onEdit(); onClose() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-zinc-600 hover:bg-zinc-50 transition-colors">
          <PencilSimple size={14} /> Editar
        </button>
        <button onClick={() => { onMove(); onClose() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-zinc-600 hover:bg-zinc-50 transition-colors">
          <ArrowRight size={14} /> Mover etapa
        </button>
        <button onClick={() => { onDelete(); onClose() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-red-500 hover:bg-red-50 transition-colors">
          <Trash size={14} /> Excluir
        </button>
      </div>
    </>
  )
}

// ─── Kanban Card ───────────────────────────────────────────────────────────────

function KanbanCard({ lead, onMenu }: { lead: Lead; onMenu: (action: 'edit' | 'move' | 'delete') => void }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const days = daysSince(lead.created_at)

  return (
    <div className="bg-white rounded-2xl border border-zinc-100 p-3.5 cursor-pointer hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 group">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <Av name={lead.title} size={7} />
          <div className="min-w-0">
            <p className="text-[12px] font-semibold text-[#1D1D1F] truncate">{lead.title}</p>
            {lead.source && <p className="text-[10px] text-zinc-400 truncate">{lead.source}</p>}
          </div>
        </div>
        <div className="relative shrink-0">
          <button onClick={e => { e.stopPropagation(); setMenuOpen(!menuOpen) }}
            className="opacity-0 group-hover:opacity-100 p-0.5 text-zinc-400 hover:text-zinc-600 transition-all">
            <DotsThreeVertical size={14} weight="bold" />
          </button>
          {menuOpen && (
            <ActionMenu
              onEdit={() => onMenu('edit')}
              onMove={() => onMenu('move')}
              onDelete={() => onMenu('delete')}
              onClose={() => setMenuOpen(false)}
            />
          )}
        </div>
      </div>
      {lead.notes && <p className="text-[11px] text-zinc-400 truncate mb-2">{lead.notes}</p>}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-[#0ABAB5]">
          <CurrencyDollar size={13} weight="bold" />
          <span className="text-[12px] font-bold font-mono">{fmt(lead.value)}</span>
        </div>
        <span className="text-[10px] text-zinc-400">{days}d</span>
      </div>
      {lead.lost_reason && (
        <div className="flex items-center gap-1 mt-2 text-[10px] text-red-400">
          <XCircle size={11} /> {lead.lost_reason}
        </div>
      )}
    </div>
  )
}

// ─── Page ──────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 50

export default function LeadsPage() {
  const qc = useQueryClient()
  const [view, setView] = useState<'kanban' | 'list'>('kanban')
  const [search, setSearch] = useState('')
  const [stageFilter, setStageFilter] = useState<LeadStage | ''>('')
  const [page, setPage] = useState(0)
  const [modal, setModal] = useState<'create' | Lead | null>(null)
  const [moveTarget, setMoveTarget] = useState<Lead | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Lead | null>(null)
  const [menuOpen, setMenuOpen] = useState<string | null>(null)

  const { data, isLoading, isError } = useQuery<LeadListResponse>({
    queryKey: ['leads', search, stageFilter, page],
    queryFn: () => leadsApi.list({
      search: search || undefined,
      stage: stageFilter || undefined,
      offset: page * PAGE_SIZE,
      limit: PAGE_SIZE,
    }),
  })

  const leads: Lead[] = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const stats = useMemo(() => {
    const pipeline = leads.filter((l: Lead) => !['won', 'lost'].includes(l.stage)).reduce((a: number, l: Lead) => a + l.value, 0)
    const wonVal = leads.filter((l: Lead) => l.stage === 'won').reduce((a: number, l: Lead) => a + l.value, 0)
    const wonCount = leads.filter((l: Lead) => l.stage === 'won').length
    return { pipeline, wonVal, wonCount }
  }, [leads])

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: CreateLeadPayload) => leadsApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['leads'] }); setModal(null) },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateLeadPayload> }) => leadsApi.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['leads'] }); setModal(null) },
  })

  const moveMutation = useMutation({
    mutationFn: ({ id, stage, reason }: { id: string; stage: LeadStage; reason?: string }) => leadsApi.moveStage(id, stage, reason),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['leads'] }); setMoveTarget(null) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => leadsApi.remove(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['leads'] }); setDeleteTarget(null) },
  })

  function handleSave(data: CreateLeadPayload) {
    if (modal === 'create') createMutation.mutate(data)
    else if (modal && typeof modal === 'object') updateMutation.mutate({ id: modal.id, data })
  }

  function handleCardAction(lead: Lead, action: 'edit' | 'move' | 'delete') {
    if (action === 'edit') setModal(lead)
    else if (action === 'move') setMoveTarget(lead)
    else setDeleteTarget(lead)
  }

  const isSaving = createMutation.isPending || updateMutation.isPending

  // Kanban stages (exclude lost unless filtering by it)
  const kanbanStages = stageFilter ? STAGES.filter(s => s.id === stageFilter) : STAGES.filter(s => s.id !== 'lost')

  return (
    <div className="flex flex-col h-full">

      {/* Modals */}
      {modal !== null && (
        <LeadModal initial={modal === 'create' ? undefined : modal} onClose={() => setModal(null)} onSave={handleSave} saving={isSaving} />
      )}
      {moveTarget && (
        <MoveStageModal lead={moveTarget} onClose={() => setMoveTarget(null)}
          onMove={(stage, reason) => moveMutation.mutate({ id: moveTarget.id, stage, reason })} moving={moveMutation.isPending} />
      )}
      {deleteTarget && (
        <DeleteConfirm title={deleteTarget.title} onConfirm={() => deleteMutation.mutate(deleteTarget.id)} onCancel={() => setDeleteTarget(null)} deleting={deleteMutation.isPending} />
      )}

      {/* Header */}
      <div className="p-4 md:p-6 lg:p-8 pb-0 space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-[#1D1D1F] tracking-tight">Pipeline de Leads</h1>
            <p className="text-zinc-500 text-sm mt-0.5">
              {isLoading ? '...' : `${total} lead${total !== 1 ? 's' : ''} · ${fmt(stats.pipeline)} em aberto`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-1 bg-white border border-zinc-200 rounded-xl p-1">
              <button onClick={() => setView('kanban')} className={`text-[12px] font-semibold px-3 py-1.5 rounded-lg transition-all ${view === 'kanban' ? 'bg-[#0ABAB5] text-white' : 'text-zinc-500'}`}>Kanban</button>
              <button onClick={() => setView('list')} className={`text-[12px] font-semibold px-3 py-1.5 rounded-lg transition-all ${view === 'list' ? 'bg-[#0ABAB5] text-white' : 'text-zinc-500'}`}>Lista</button>
            </div>
            <button onClick={() => setModal('create')}
              className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#089B97] text-white text-[13px] font-semibold px-4 py-2.5 rounded-xl transition-all active:scale-95">
              <Plus size={16} weight="bold" />
              <span className="hidden sm:inline">Novo lead</span>
            </button>
          </div>
        </div>

        {/* Mini stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Total leads', value: isLoading ? '-' : total },
            { label: 'Ganhos', value: isLoading ? '-' : stats.wonCount },
            { label: 'Pipeline', value: isLoading ? '-' : fmt(stats.pipeline) },
            { label: 'Receita ganha', value: isLoading ? '-' : fmt(stats.wonVal) },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-2xl border border-zinc-100 p-3.5">
              <p className="text-lg font-bold text-[#1D1D1F] font-mono">{s.value}</p>
              <p className="text-[11px] text-zinc-400 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Search + Stage Filter */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex items-center gap-2 bg-white border border-zinc-200 rounded-xl px-3 py-2.5 flex-1 focus-within:border-[#0ABAB5]/50 focus-within:shadow-[0_0_0_3px_rgba(10,186,181,0.08)] transition-all">
            <MagnifyingGlass size={15} className="text-zinc-400 shrink-0" />
            <input value={search} onChange={e => { setSearch(e.target.value); setPage(0) }}
              placeholder="Buscar leads..." className="text-[13px] bg-transparent focus:outline-none w-full placeholder:text-zinc-400" />
          </div>
          <div className="flex items-center gap-2">
            <Funnel size={14} className="text-zinc-400 shrink-0" />
            <select value={stageFilter} onChange={e => { setStageFilter(e.target.value as LeadStage | ''); setPage(0) }}
              className="text-[12px] font-semibold bg-white border border-zinc-200 rounded-xl px-3 py-2.5 outline-none focus:border-[#0ABAB5] transition-all">
              <option value="">Todas etapas</option>
              {STAGES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20 flex-1">
          <SpinnerGap size={28} className="text-[#0ABAB5] animate-spin" />
        </div>
      ) : isError ? (
        <div className="flex flex-col items-center py-16 text-zinc-400 gap-2 flex-1">
          <WarningCircle size={36} weight="duotone" className="text-red-400" />
          <p className="text-[13px]">Erro ao carregar leads</p>
          <button onClick={() => qc.invalidateQueries({ queryKey: ['leads'] })}
            className="text-[12px] text-[#0ABAB5] font-semibold hover:underline mt-1">Tentar novamente</button>
        </div>
      ) : leads.length === 0 && !search && !stageFilter ? (
        <div className="flex flex-col items-center py-20 text-zinc-300 gap-2 flex-1">
          <Funnel size={40} weight="duotone" />
          <p className="text-sm text-zinc-400">Nenhum lead cadastrado</p>
          <button onClick={() => setModal('create')} className="text-[12px] text-[#0ABAB5] font-semibold hover:underline mt-1">
            Criar primeiro lead
          </button>
        </div>
      ) : (
        <>
          {/* Kanban View */}
          {view === 'kanban' && (
            <div className="flex gap-4 p-4 md:p-6 lg:p-8 overflow-x-auto pb-8 flex-1">
              {kanbanStages.map(stage => {
                const cards = leads.filter(l => l.stage === stage.id)
                return (
                  <div key={stage.id} className="flex flex-col shrink-0 w-[260px] md:w-[240px] lg:flex-1 lg:min-w-[180px]">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${stage.dot}`} />
                        <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full ${stage.color}`}>{stage.label}</span>
                      </div>
                      <span className="text-[11px] font-semibold text-zinc-400 bg-zinc-100 w-5 h-5 rounded-full flex items-center justify-center">{cards.length}</span>
                    </div>

                    <div className="flex flex-col gap-2.5 flex-1">
                      {cards.map(lead => (
                        <KanbanCard key={lead.id} lead={lead} onMenu={action => handleCardAction(lead, action)} />
                      ))}
                      <button onClick={() => setModal('create')}
                        className="w-full py-2.5 rounded-xl border border-dashed border-zinc-200 text-[12px] text-zinc-400 hover:border-[#0ABAB5]/40 hover:text-[#0ABAB5] transition-all flex items-center justify-center gap-1.5">
                        <Plus size={13} />Adicionar
                      </button>
                    </div>
                  </div>
                )
              })}

              {/* Lost leads indicator (when not filtering) */}
              {!stageFilter && leads.some(l => l.stage === 'lost') && (
                <div className="flex flex-col shrink-0 w-[260px] md:w-[240px] lg:flex-1 lg:min-w-[180px] opacity-60">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-red-400" />
                      <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-red-50 text-red-500">Perdidos</span>
                    </div>
                    <span className="text-[11px] font-semibold text-zinc-400 bg-zinc-100 w-5 h-5 rounded-full flex items-center justify-center">
                      {leads.filter(l => l.stage === 'lost').length}
                    </span>
                  </div>
                  <div className="flex flex-col gap-2.5 flex-1">
                    {leads.filter(l => l.stage === 'lost').map(lead => (
                      <KanbanCard key={lead.id} lead={lead} onMenu={action => handleCardAction(lead, action)} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* List View */}
          {view === 'list' && (
            <div className="p-4 md:p-6 lg:p-8 pt-4">
              <div className="bg-white rounded-2xl border border-zinc-100 overflow-hidden">
                <div className="hidden md:grid grid-cols-[2fr_1fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3 border-b border-zinc-100 bg-zinc-50/60">
                  {['Lead', 'Etapa', 'Valor', 'Origem', 'Dias', ''].map(h => (
                    <p key={h} className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">{h}</p>
                  ))}
                </div>
                <div className="divide-y divide-zinc-50">
                  {leads.map(lead => {
                    const stage = STAGE_MAP[lead.stage]
                    const days = daysSince(lead.created_at)
                    return (
                      <div key={lead.id}>
                        {/* Desktop */}
                        <div className="hidden md:grid grid-cols-[2fr_1fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3.5 items-center hover:bg-zinc-50/60 transition-colors group">
                          <div className="flex items-center gap-3 min-w-0">
                            <Av name={lead.title} size={7} />
                            <div className="min-w-0">
                              <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{lead.title}</p>
                              {lead.notes && <p className="text-[11px] text-zinc-400 truncate">{lead.notes}</p>}
                            </div>
                          </div>
                          <span className={`inline-flex w-fit text-[11px] font-semibold px-2.5 py-1 rounded-full ${stage?.color}`}>{stage?.label}</span>
                          <p className="text-[13px] font-bold text-[#0ABAB5] font-mono">{fmt(lead.value)}</p>
                          <p className="text-[12px] text-zinc-400 capitalize">{lead.source || '-'}</p>
                          <p className="text-[13px] text-zinc-400 font-mono">{days}d</p>
                          <div className="relative">
                            <button onClick={() => setMenuOpen(menuOpen === lead.id ? null : lead.id)}
                              className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-all">
                              <DotsThreeVertical size={16} weight="bold" />
                            </button>
                            {menuOpen === lead.id && (
                              <ActionMenu
                                onEdit={() => setModal(lead)}
                                onMove={() => setMoveTarget(lead)}
                                onDelete={() => setDeleteTarget(lead)}
                                onClose={() => setMenuOpen(null)}
                              />
                            )}
                          </div>
                        </div>
                        {/* Mobile */}
                        <div className="md:hidden p-4 active:bg-zinc-50 transition-colors">
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <div className="flex items-center gap-2 min-w-0">
                              <Av name={lead.title} size={8} />
                              <div className="min-w-0">
                                <p className="text-[14px] font-semibold text-[#1D1D1F] truncate">{lead.title}</p>
                                {lead.notes && <p className="text-[11px] text-zinc-400 truncate">{lead.notes}</p>}
                              </div>
                            </div>
                            <button onClick={() => setMenuOpen(menuOpen === lead.id ? null : lead.id)}
                              className="p-1 rounded-lg hover:bg-zinc-100 text-zinc-400 shrink-0">
                              <DotsThreeVertical size={16} weight="bold" />
                            </button>
                            {menuOpen === lead.id && (
                              <ActionMenu onEdit={() => setModal(lead)} onMove={() => setMoveTarget(lead)} onDelete={() => setDeleteTarget(lead)} onClose={() => setMenuOpen(null)} />
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-2 ml-10">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${stage?.color}`}>{stage?.label}</span>
                            <span className="text-[13px] font-bold text-[#0ABAB5] font-mono">{fmt(lead.value)}</span>
                            <span className="text-[11px] text-zinc-400">{days}d</span>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between px-5 py-3 border-t border-zinc-100 bg-zinc-50/40">
                    <p className="text-[12px] text-zinc-400">
                      {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} de {total}
                    </p>
                    <div className="flex items-center gap-1">
                      <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                        className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 disabled:opacity-30 transition-colors">
                        <CaretLeft size={14} weight="bold" />
                      </button>
                      <span className="text-[12px] font-semibold text-zinc-500 px-2">{page + 1} / {totalPages}</span>
                      <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
                        className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 disabled:opacity-30 transition-colors">
                        <CaretRight size={14} weight="bold" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

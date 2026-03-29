import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, DotsThreeVertical, Handshake, WarningCircle, FileText,
  CurrencyDollar, Clock, X, Check, SpinnerGap, PencilSimple, Trash, MagnifyingGlass,
} from '@phosphor-icons/react'
import { contractsApi, type ContractStatus, type Contract } from '../../api/contracts'
import { quotesApi, type Quote } from '../../api/quotes'

// ── Status helpers ─────────────────────────────────────────────────────────────

const STATUS_LABEL: Record<ContractStatus, string> = {
  draft:     'Rascunho',
  active:    'Ativo',
  completed: 'Concluído',
  cancelled: 'Cancelado',
}

const STATUS_STYLES: Record<ContractStatus, string> = {
  active:    'bg-emerald-50 text-emerald-700 border border-emerald-100',
  completed: 'bg-blue-50 text-blue-700 border border-blue-100',
  cancelled: 'bg-red-50 text-red-700 border border-red-100',
  draft:     'bg-zinc-100 text-zinc-600 border border-zinc-200',
}

const STATUSES: ContractStatus[] = ['draft', 'active', 'completed', 'cancelled']

type FilterTab = 'Todos' | ContractStatus | 'expired'

const TABS: FilterTab[] = ['Todos', 'active', 'completed', 'cancelled', 'draft', 'expired']
const TAB_LABELS: Record<FilterTab, string> = {
  Todos: 'Todos', active: 'Ativo', completed: 'Concluído', cancelled: 'Cancelado', draft: 'Rascunho', expired: 'A Vencer',
}

function fmtDate(iso?: string) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function isExpiringSoon(contract: Contract) {
  if (!contract.expires_at || contract.status !== 'active') return false
  const diff = new Date(contract.expires_at).getTime() - Date.now()
  return diff > 0 && diff < 30 * 86400000
}

// ── Create Modal ───────────────────────────────────────────────────────────────

interface CreateModalProps {
  onClose: () => void
  onSave: (data: { quote_id: string; title: string; expires_at?: string }) => void
  saving: boolean
}

function CreateModal({ onClose, onSave, saving }: CreateModalProps) {
  const [quoteId, setQuoteId]   = useState('')
  const [title, setTitle]       = useState('')
  const [expiresAt, setExpiresAt] = useState('')

  const { data: quotes = [] } = useQuery<Quote[]>({
    queryKey: ['quotes-select'],
    queryFn: () => quotesApi.list({ status: 'approved', limit: 200 }),
  })

  function handleQuoteChange(id: string) {
    setQuoteId(id)
    const q = quotes.find(q => q.id === id)
    if (q && !title) setTitle(q.title)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!quoteId || !title.trim()) return
    onSave({ quote_id: quoteId, title: title.trim(), expires_at: expiresAt || undefined })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100">
          <h2 className="text-[15px] font-bold text-[#1D1D1F]">Novo Contrato</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
            <X size={16} weight="bold" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Orçamento Aprovado *</label>
            <select value={quoteId} onChange={e => handleQuoteChange(e.target.value)}
              className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all bg-white" required>
              <option value="">Selecionar orçamento...</option>
              {quotes.map(q => (
                <option key={q.id} value={q.id}>
                  {q.title}{q.customer_name ? ` — ${q.customer_name}` : ''}
                </option>
              ))}
            </select>
            {quotes.length === 0 && (
              <p className="text-[11px] text-zinc-400 mt-1">Nenhum orçamento aprovado encontrado.</p>
            )}
          </div>
          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Título / Objeto *</label>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Ex: Contrato de Prestação de Serviço"
              className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" required autoFocus />
          </div>
          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Validade</label>
            <input value={expiresAt} onChange={e => setExpiresAt(e.target.value)} type="date"
              className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
          </div>
          <div className="flex items-center gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={saving || !quoteId || !title.trim()}
              className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] disabled:opacity-50 py-2.5 rounded-xl transition-colors">
              {saving ? <SpinnerGap size={14} className="animate-spin" /> : <Check size={14} weight="bold" />}
              Criar
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Edit Status Modal ──────────────────────────────────────────────────────────

interface EditModalProps {
  contract: Contract
  onClose: () => void
  onSave: (status: ContractStatus) => void
  saving: boolean
}

function EditModal({ contract, onClose, onSave, saving }: EditModalProps) {
  const [status, setStatus] = useState<ContractStatus>(contract.status)
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100">
          <h2 className="text-[15px] font-bold text-[#1D1D1F]">Editar Contrato</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
            <X size={16} weight="bold" />
          </button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <p className="text-[12px] font-semibold text-zinc-500 mb-0.5">Cliente</p>
            <p className="text-[14px] text-zinc-800 font-medium">{contract.customer_name ?? '—'}</p>
          </div>
          <div>
            <p className="text-[12px] font-semibold text-zinc-500 mb-0.5">Objeto</p>
            <p className="text-[14px] text-zinc-800">{contract.title}</p>
          </div>
          <div>
            <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Status</label>
            <select value={status} onChange={e => setStatus(e.target.value as ContractStatus)}
              className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all bg-white">
              {STATUSES.map(s => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <button onClick={onClose}
              className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
              Cancelar
            </button>
            <button onClick={() => onSave(status)} disabled={saving || status === contract.status}
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

// ── Cancel Confirm ─────────────────────────────────────────────────────────────

function CancelConfirm({ nome, onConfirm, onCancel }: { nome: string; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onCancel}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-5" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center shrink-0">
            <Trash size={18} weight="duotone" className="text-red-500" />
          </div>
          <div>
            <p className="text-[14px] font-bold text-[#1D1D1F]">Cancelar contrato</p>
            <p className="text-[12px] text-zinc-400">O status será alterado para Cancelado</p>
          </div>
        </div>
        <p className="text-[13px] text-zinc-600 mb-5">
          Tem certeza que deseja cancelar o contrato de <strong>{nome}</strong>?
        </p>
        <div className="flex items-center gap-2">
          <button onClick={onCancel}
            className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
            Voltar
          </button>
          <button onClick={onConfirm}
            className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-red-500 hover:bg-red-600 py-2.5 rounded-xl transition-colors">
            <Trash size={14} weight="bold" />
            Cancelar Contrato
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Action Menu ────────────────────────────────────────────────────────────────

function ActionMenu({ onEdit, onCancel, onClose }: { onEdit: () => void; onCancel: () => void; onClose: () => void }) {
  return (
    <>
      <div className="fixed inset-0 z-40" onClick={onClose} />
      <div className="absolute right-0 top-full mt-1 w-44 bg-white rounded-xl border border-zinc-100 shadow-lg py-1 z-50">
        <button onClick={() => { onEdit(); onClose() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-zinc-600 hover:bg-zinc-50 transition-colors">
          <PencilSimple size={14} /> Editar Status
        </button>
        <button onClick={() => { onCancel(); onClose() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-red-500 hover:bg-red-50 transition-colors">
          <Trash size={14} /> Cancelar Contrato
        </button>
      </div>
    </>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function ContractsPage() {
  const queryClient = useQueryClient()
  const [tab, setTab]           = useState<FilterTab>('Todos')
  const [modal, setModal]       = useState<'create' | Contract | null>(null)
  const [cancelTarget, setCancelTarget] = useState<Contract | null>(null)
  const [menuOpen, setMenuOpen] = useState<string | null>(null)
  const [search, setSearch]     = useState('')

  const { data: contracts = [], isLoading } = useQuery<Contract[]>({
    queryKey: ['contracts'],
    queryFn: () => contractsApi.list({ limit: 200 }),
  })

  const createMutation = useMutation({
    mutationFn: (data: { quote_id: string; title: string; expires_at?: string }) =>
      contractsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
      setModal(null)
    },
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: ContractStatus }) =>
      contractsApi.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
      setModal(null)
      setCancelTarget(null)
    },
  })

  const searchFiltered = search
    ? contracts.filter(c =>
        (c.customer_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
        c.title.toLowerCase().includes(search.toLowerCase()))
    : contracts

  const filtered = tab === 'Todos'
    ? searchFiltered
    : tab === 'expired'
      ? searchFiltered.filter(isExpiringSoon)
      : searchFiltered.filter(c => c.status === tab)

  const ativos   = contracts.filter(c => c.status === 'active').length
  const vencer   = contracts.filter(isExpiringSoon).length
  const totalVal = contracts.filter(c => c.status === 'active' || c.status === 'completed')
                             .reduce((s, c) => s + (c.value ?? 0), 0)

  return (
    <div className="p-4 md:p-6 space-y-5 pb-6">

      {/* Modals */}
      {modal === 'create' && (
        <CreateModal
          onClose={() => setModal(null)}
          onSave={data => createMutation.mutate(data)}
          saving={createMutation.isPending}
        />
      )}
      {modal !== null && modal !== 'create' && (
        <EditModal
          contract={modal}
          onClose={() => setModal(null)}
          onSave={status => updateStatusMutation.mutate({ id: modal.id, status })}
          saving={updateStatusMutation.isPending}
        />
      )}
      {cancelTarget && (
        <CancelConfirm
          nome={cancelTarget.customer_name ?? cancelTarget.title}
          onConfirm={() => updateStatusMutation.mutate({ id: cancelTarget.id, status: 'cancelled' })}
          onCancel={() => setCancelTarget(null)}
        />
      )}

      {/* Sticky header */}
      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100 flex items-center justify-between">
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight">Contratos</h1>
        <button onClick={() => setModal('create')} className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#09a8a3] text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95">
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
          <p className="text-xl font-bold text-[#1D1D1F] font-mono truncate">
            {totalVal >= 1000 ? `R$ ${(totalVal / 1000).toFixed(0)}k` : `R$ ${totalVal.toLocaleString('pt-BR')}`}
          </p>
          <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">Valor Total</p>
        </div>
      </div>

      {/* Search */}
      <div className="flex items-center gap-2 bg-white border border-zinc-200 rounded-xl px-3 py-2 focus-within:border-[#0ABAB5]/50 transition-all">
        <MagnifyingGlass size={14} className="text-zinc-400 shrink-0" />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar contratos..."
          className="text-[13px] bg-transparent focus:outline-none w-full placeholder:text-zinc-400" />
      </div>

      {/* Filter tabs */}
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

      {/* Contract list */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 overflow-visible">
        <div className="hidden md:grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3 border-b border-zinc-100 bg-zinc-50/60">
          {['Cliente', 'Objeto', 'Criação', 'Validade', 'Status', ''].map(h => (
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
            <p className="text-sm mt-2 text-zinc-400">Nenhum contrato encontrado</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-100">
            {filtered.map(c => {
              const expiring = isExpiringSoon(c)
              return (
                <div key={c.id}>
                  {/* Desktop row */}
                  <div className="hidden md:grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3.5 items-center hover:bg-zinc-50/60 transition-colors group cursor-pointer"
                    onClick={() => setModal(c)}>
                    <div className="flex items-center gap-2 min-w-0">
                      <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{c.customer_name ?? '—'}</p>
                      {expiring && (
                        <span className="shrink-0 flex items-center gap-1 text-[11px] font-semibold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full border border-amber-100">
                          <WarningCircle size={10} weight="fill" />
                          Vence
                        </span>
                      )}
                    </div>
                    <p className="text-[13px] text-zinc-500 truncate">{c.title}</p>
                    <p className="text-[13px] text-zinc-500">{fmtDate(c.created_at)}</p>
                    <p className={`text-[13px] font-medium ${expiring ? 'text-amber-600 font-semibold' : 'text-zinc-500'}`}>
                      {fmtDate(c.expires_at)}
                    </p>
                    <span className={`inline-flex text-[11px] font-semibold px-2 py-0.5 rounded-full w-fit ${STATUS_STYLES[c.status]}`}>
                      {STATUS_LABEL[c.status]}
                    </span>
                    <div className="relative" onClick={e => e.stopPropagation()}>
                      <button onClick={() => setMenuOpen(menuOpen === c.id ? null : c.id)}
                        className="p-1.5 rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-600 transition-all">
                        <DotsThreeVertical size={16} weight="bold" />
                      </button>
                      {menuOpen === c.id && (
                        <ActionMenu onEdit={() => setModal(c)} onCancel={() => setCancelTarget(c)} onClose={() => setMenuOpen(null)} />
                      )}
                    </div>
                  </div>

                  {/* Mobile card */}
                  <div className="md:hidden p-4 active:bg-zinc-50 transition-colors cursor-pointer" onClick={() => setModal(c)}>
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 rounded-xl bg-[#0ABAB5]/10 flex items-center justify-center shrink-0 mt-0.5">
                        <Handshake size={17} weight="duotone" className="text-[#0ABAB5]" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-0.5">
                          <p className="text-[14px] font-semibold text-[#1D1D1F] truncate">{c.customer_name ?? '—'}</p>
                          <div className="flex items-center gap-1.5 shrink-0">
                            {expiring && <WarningCircle size={14} weight="fill" className="text-amber-500" />}
                            <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${STATUS_STYLES[c.status]}`}>
                              {STATUS_LABEL[c.status]}
                            </span>
                          </div>
                        </div>
                        <p className="text-[12px] text-zinc-400 mb-2.5 truncate">{c.title}</p>
                        <div className="flex items-center gap-4 pt-2 border-t border-zinc-100">
                          <div>
                            <p className="text-[10px] text-zinc-400">Criação</p>
                            <p className="text-[12px] font-medium text-zinc-600">{fmtDate(c.created_at)}</p>
                          </div>
                          <div>
                            <p className="text-[10px] text-zinc-400">Validade</p>
                            <p className={`text-[12px] font-medium ${expiring ? 'text-amber-600 font-semibold' : 'text-zinc-600'}`}>
                              {fmtDate(c.expires_at)}
                            </p>
                          </div>
                          <div onClick={e => e.stopPropagation()} className="ml-auto">
                            <button onClick={() => setMenuOpen(menuOpen === c.id ? null : c.id)} className="p-1 rounded-lg hover:bg-zinc-100 text-zinc-400">
                              <DotsThreeVertical size={15} weight="bold" />
                            </button>
                            {menuOpen === c.id && (
                              <ActionMenu onEdit={() => setModal(c)} onCancel={() => setCancelTarget(c)} onClose={() => setMenuOpen(null)} />
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <p className="text-[12px] text-zinc-400 px-1">{filtered.length} contrato{filtered.length !== 1 ? 's' : ''}</p>
    </div>
  )
}

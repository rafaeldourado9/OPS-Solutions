import { useState, useMemo } from 'react'
import { createPortal } from 'react-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Users, MagnifyingGlass, Plus, WhatsappLogo, Phone, EnvelopeSimple,
  DotsThreeVertical, PencilSimple, Trash, SpinnerGap, WarningCircle,
  X, Check, CaretLeft, CaretRight, Buildings, IdentificationCard,
} from '@phosphor-icons/react'
import { customersApi, type Customer, type CreateCustomerPayload } from '../../api/customers'

// ─── Helpers ───────────────────────────────────────────────────────────────────

const COLORS = ['bg-[#0ABAB5]', 'bg-violet-500', 'bg-orange-500', 'bg-rose-500', 'bg-blue-500', 'bg-emerald-600']

function Av({ name, sm }: { name: string; sm?: boolean }) {
  const initials = name.split(' ').filter(Boolean).map(w => w[0]).slice(0, 2).join('').toUpperCase()
  const c = COLORS[initials.charCodeAt(0) % COLORS.length]
  return (
    <div className={`${sm ? 'w-8 h-8 text-xs' : 'w-10 h-10 text-sm'} ${c} rounded-full flex items-center justify-center text-white font-bold shrink-0`}>
      {initials}
    </div>
  )
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
}

const SOURCE_LABELS: Record<string, { l: string; c: string }> = {
  whatsapp: { l: 'WhatsApp', c: 'bg-emerald-50 text-emerald-600 border-emerald-100' },
  manual:   { l: 'Manual',   c: 'bg-blue-50 text-blue-600 border-blue-100' },
  import:   { l: 'Import',   c: 'bg-violet-50 text-violet-600 border-violet-100' },
}

// ─── Modal ─────────────────────────────────────────────────────────────────────

interface ModalProps {
  initial?: Customer
  onClose: () => void
  onSave: (data: CreateCustomerPayload & { is_active?: boolean }) => void
  saving: boolean
}

function CustomerModal({ initial, onClose, onSave, saving }: ModalProps) {
  const [name, setName] = useState(initial?.name ?? '')
  const [phone, setPhone] = useState(initial?.phone ?? '')
  const [email, setEmail] = useState(initial?.email ?? '')
  const [company, setCompany] = useState(initial?.company_name ?? '')
  const [cpfCnpj, setCpfCnpj] = useState(initial?.cpf_cnpj ?? '')
  const [notes, setNotes] = useState(initial?.notes ?? '')
  const [isActive, setIsActive] = useState(initial?.is_active ?? true)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !phone.trim()) return
    onSave({
      name: name.trim(),
      phone: phone.trim(),
      email: email.trim() || undefined,
      company_name: company.trim() || undefined,
      cpf_cnpj: cpfCnpj.trim() || undefined,
      notes: notes.trim(),
      source: initial?.source ?? 'manual',
      ...(initial ? { is_active: isActive } : {}),
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100">
          <h2 className="text-[15px] font-bold text-[#1D1D1F]">
            {initial ? 'Editar Cliente' : 'Novo Cliente'}
          </h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
            <X size={16} weight="bold" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Nome *</label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="Nome completo"
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" required autoFocus />
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Telefone *</label>
              <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="+55 11 99999-0000"
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" required />
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Email</label>
              <input value={email} onChange={e => setEmail(e.target.value)} placeholder="email@empresa.com" type="email"
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Empresa</label>
              <input value={company} onChange={e => setCompany(e.target.value)} placeholder="Nome da empresa"
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
            </div>
            <div>
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">CPF/CNPJ</label>
              <input value={cpfCnpj} onChange={e => setCpfCnpj(e.target.value)} placeholder="000.000.000-00"
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all" />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-[12px] font-semibold text-zinc-500 mb-1.5">Observações</label>
              <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Notas sobre o cliente..." rows={2}
                className="w-full text-[14px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all resize-none" />
            </div>
          </div>

          {initial && (
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={isActive} onChange={e => setIsActive(e.target.checked)}
                className="w-4 h-4 rounded border-zinc-300 text-[#0ABAB5] focus:ring-[#0ABAB5]" />
              <span className="text-[13px] text-zinc-600">Cliente ativo</span>
            </label>
          )}

          <div className="flex items-center gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={saving || !name.trim() || !phone.trim()}
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

// ─── Delete Confirm ────────────────────────────────────────────────────────────

function DeleteConfirm({ name, onConfirm, onCancel, deleting }: { name: string; onConfirm: () => void; onCancel: () => void; deleting: boolean }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onCancel}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-5" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center shrink-0">
            <Trash size={18} weight="duotone" className="text-red-500" />
          </div>
          <div>
            <p className="text-[14px] font-bold text-[#1D1D1F]">Excluir cliente</p>
            <p className="text-[12px] text-zinc-400">Esta ação não pode ser desfeita</p>
          </div>
        </div>
        <p className="text-[13px] text-zinc-600 mb-5">
          Tem certeza que deseja excluir <strong>{name}</strong>?
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

// ─── Dropdown Menu ─────────────────────────────────────────────────────────────

interface MenuPos { top: number; right: number }

function ActionMenu({ pos, onEdit, onDelete, onClose }: { pos: MenuPos; onEdit: () => void; onDelete: () => void; onClose: () => void }) {
  return createPortal(
    <>
      <div className="fixed inset-0 z-40" onClick={onClose} />
      <div
        className="fixed w-40 bg-white rounded-xl border border-zinc-100 shadow-lg py-1 z-50"
        style={{ top: pos.top, right: pos.right }}
      >
        <button onClick={() => { onEdit(); onClose() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-zinc-600 hover:bg-zinc-50 transition-colors">
          <PencilSimple size={14} /> Editar
        </button>
        <button onClick={() => { onDelete(); onClose() }}
          className="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-red-500 hover:bg-red-50 transition-colors">
          <Trash size={14} /> Excluir
        </button>
      </div>
    </>,
    document.body
  )
}

// ─── Page ──────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 20

export default function CustomersPage() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [tab, setTab] = useState<'all' | 'active' | 'inactive'>('all')
  const [page, setPage] = useState(0)
  const [modal, setModal] = useState<'create' | Customer | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Customer | null>(null)
  const [menuOpen, setMenuOpen] = useState<{ id: string } & MenuPos | null>(null)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['customers', search, page],
    queryFn: () => customersApi.list({ search: search || undefined, offset: page * PAGE_SIZE, limit: PAGE_SIZE }),
  })

  const items = data?.items ?? []
  const total = data?.total ?? 0

  const filtered = useMemo(() => {
    if (tab === 'all') return items
    return items.filter((c: Customer) => tab === 'active' ? c.is_active : !c.is_active)
  }, [items, tab])

  const activeCount = items.filter((c: Customer) => c.is_active).length
  const totalPages = Math.ceil(total / PAGE_SIZE)

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: CreateCustomerPayload) => customersApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['customers'] }); setModal(null) },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateCustomerPayload> & { is_active?: boolean } }) =>
      customersApi.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['customers'] }); setModal(null) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => customersApi.remove(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['customers'] }); setDeleteTarget(null) },
  })

  function handleSave(data: CreateCustomerPayload & { is_active?: boolean }) {
    if (modal === 'create') {
      createMutation.mutate(data)
    } else if (modal && typeof modal === 'object') {
      updateMutation.mutate({ id: modal.id, data })
    }
  }

  const isSaving = createMutation.isPending || updateMutation.isPending

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-5">

      {/* Modals */}
      {modal !== null && (
        <CustomerModal
          initial={modal === 'create' ? undefined : modal}
          onClose={() => setModal(null)}
          onSave={handleSave}
          saving={isSaving}
        />
      )}

      {deleteTarget && (
        <DeleteConfirm
          name={deleteTarget.name}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
          onCancel={() => setDeleteTarget(null)}
          deleting={deleteMutation.isPending}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-[#1D1D1F] tracking-tight">Clientes</h1>
          <p className="text-zinc-500 text-sm mt-0.5">
            {isLoading ? '...' : `${total} cadastro${total !== 1 ? 's' : ''}`}
          </p>
        </div>
        <button onClick={() => setModal('create')}
          className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#089B97] text-white text-[13px] font-semibold px-4 py-2.5 rounded-xl transition-all active:scale-95">
          <Plus size={16} weight="bold" />
          <span className="hidden sm:inline">Novo cliente</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-2xl border border-zinc-100 p-4">
          <p className="text-xl font-bold text-[#1D1D1F] font-mono">{isLoading ? '-' : total}</p>
          <p className="text-xs text-zinc-400 mt-0.5">Total</p>
        </div>
        <div className="bg-white rounded-2xl border border-zinc-100 p-4">
          <p className="text-xl font-bold text-emerald-600 font-mono">{isLoading ? '-' : activeCount}</p>
          <p className="text-xs text-zinc-400 mt-0.5">Ativos</p>
        </div>
        <div className="bg-white rounded-2xl border border-zinc-100 p-4">
          <p className="text-xl font-bold text-zinc-400 font-mono">{isLoading ? '-' : items.length - activeCount}</p>
          <p className="text-xs text-zinc-400 mt-0.5">Inativos</p>
        </div>
      </div>

      {/* Search + Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex items-center gap-2 bg-white border border-zinc-200 rounded-xl px-3 py-2.5 flex-1 focus-within:border-[#0ABAB5]/50 focus-within:shadow-[0_0_0_3px_rgba(10,186,181,0.08)] transition-all">
          <MagnifyingGlass size={15} className="text-zinc-400 shrink-0" />
          <input
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(0) }}
            placeholder="Buscar por nome, telefone, empresa..."
            className="text-[13px] bg-transparent focus:outline-none w-full placeholder:text-zinc-400"
          />
        </div>
        <div className="flex gap-2 overflow-x-auto">
          {(['all', 'active', 'inactive'] as const).map(f => (
            <button key={f} onClick={() => setTab(f)}
              className={`shrink-0 text-[12px] font-semibold px-3.5 py-2 rounded-xl border transition-all ${
                tab === f ? 'bg-[#0ABAB5] text-white border-[#0ABAB5]' : 'bg-white text-zinc-500 border-zinc-200'
              }`}>
              {f === 'all' ? 'Todos' : f === 'active' ? 'Ativos' : 'Inativos'}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <SpinnerGap size={28} className="text-[#0ABAB5] animate-spin" />
        </div>
      ) : isError ? (
        <div className="flex flex-col items-center py-16 text-zinc-400 gap-2">
          <WarningCircle size={36} weight="duotone" className="text-red-400" />
          <p className="text-[13px]">Erro ao carregar clientes</p>
          <button onClick={() => qc.invalidateQueries({ queryKey: ['customers'] })}
            className="text-[12px] text-[#0ABAB5] font-semibold hover:underline mt-1">
            Tentar novamente
          </button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-zinc-200 flex flex-col items-center py-16 text-zinc-300 gap-2">
          <Users size={40} weight="duotone" />
          <p className="text-sm text-zinc-400">
            {search ? 'Nenhum cliente encontrado' : 'Nenhum cliente cadastrado'}
          </p>
          {!search && (
            <button onClick={() => setModal('create')}
              className="text-[12px] text-[#0ABAB5] font-semibold hover:underline mt-1">
              Criar primeiro cliente
            </button>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-zinc-100 overflow-hidden">
          {/* Desktop header */}
          <div className="hidden md:grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3 border-b border-zinc-100 bg-zinc-50/60">
            {['Cliente', 'Contato', 'Origem', 'Status', 'Criado em', ''].map(h => (
              <p key={h} className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">{h}</p>
            ))}
          </div>

          <div className="divide-y divide-zinc-50">
            {filtered.map((c: Customer) => {
              const src = SOURCE_LABELS[c.source] ?? SOURCE_LABELS.manual
              const statusStyle = c.is_active
                ? 'bg-emerald-50 text-emerald-600 border-emerald-100'
                : 'bg-zinc-50 text-zinc-500 border-zinc-200'
              return (
                <div key={c.id}>
                  {/* Desktop row */}
                  <div className="hidden md:grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_36px] gap-4 px-5 py-3.5 items-center hover:bg-zinc-50/60 transition-colors group">
                    <div className="flex items-center gap-3 min-w-0">
                      <Av name={c.name} sm />
                      <div className="min-w-0">
                        <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{c.name}</p>
                        <div className="flex items-center gap-1.5 min-w-0">
                          {c.company_name && (
                            <span className="flex items-center gap-1 text-[11px] text-zinc-400 truncate">
                              <Buildings size={10} className="shrink-0" />{c.company_name}
                            </span>
                          )}
                          {c.cpf_cnpj && (
                            <span className="flex items-center gap-1 text-[11px] text-zinc-400 truncate">
                              <IdentificationCard size={10} className="shrink-0" />{c.cpf_cnpj}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="min-w-0">
                      {c.email && <p className="text-[12px] text-zinc-500 truncate">{c.email}</p>}
                      <p className="text-[11px] text-zinc-400">{c.phone}</p>
                    </div>
                    <span className={`inline-flex w-fit text-[11px] font-semibold px-2.5 py-1 rounded-full border ${src.c}`}>{src.l}</span>
                    <span className={`inline-flex w-fit text-[11px] font-semibold px-2.5 py-1 rounded-full border ${statusStyle}`}>
                      {c.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                    <p className="text-[12px] text-zinc-400">{fmtDate(c.created_at)}</p>
                    <div>
                      <button
                        onClick={e => {
                          const r = e.currentTarget.getBoundingClientRect()
                          setMenuOpen(menuOpen?.id === c.id ? null : { id: c.id, top: r.bottom + 4, right: window.innerWidth - r.right })
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-all">
                        <DotsThreeVertical size={16} weight="bold" />
                      </button>
                      {menuOpen?.id === c.id && (
                        <ActionMenu
                          pos={menuOpen}
                          onEdit={() => setModal(c)}
                          onDelete={() => setDeleteTarget(c)}
                          onClose={() => setMenuOpen(null)}
                        />
                      )}
                    </div>
                  </div>

                  {/* Mobile card */}
                  <div className="md:hidden p-4 active:bg-zinc-50 transition-colors">
                    <div className="flex items-start gap-3">
                      <Av name={c.name} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-0.5">
                          <p className="text-[14px] font-semibold text-[#1D1D1F] truncate">{c.name}</p>
                          <div className="flex items-center gap-1 shrink-0">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${statusStyle}`}>
                              {c.is_active ? 'Ativo' : 'Inativo'}
                            </span>
                            <button
                              onClick={e => {
                                const r = e.currentTarget.getBoundingClientRect()
                                setMenuOpen(menuOpen?.id === c.id ? null : { id: c.id, top: r.bottom + 4, right: window.innerWidth - r.right })
                              }}
                              className="p-1 rounded-lg hover:bg-zinc-100 text-zinc-400">
                              <DotsThreeVertical size={16} weight="bold" />
                            </button>
                            {menuOpen?.id === c.id && (
                              <ActionMenu pos={menuOpen} onEdit={() => setModal(c)} onDelete={() => setDeleteTarget(c)} onClose={() => setMenuOpen(null)} />
                            )}
                          </div>
                        </div>
                        {c.company_name && <p className="text-[12px] text-zinc-400 mb-2.5">{c.company_name}</p>}
                        <div className="flex items-center gap-2 flex-wrap">
                          <a href={'tel:' + c.phone} className="flex items-center gap-1 text-[12px] text-zinc-500 bg-zinc-50 px-2.5 py-1.5 rounded-lg hover:bg-zinc-100 transition-colors">
                            <Phone size={12} />Ligar
                          </a>
                          <a href={'https://wa.me/' + c.phone.replace(/\D/g, '')} target="_blank" rel="noreferrer"
                            className="flex items-center gap-1 text-[12px] text-zinc-500 bg-zinc-50 px-2.5 py-1.5 rounded-lg hover:bg-emerald-50 hover:text-emerald-600 transition-colors">
                            <WhatsappLogo size={12} />WhatsApp
                          </a>
                          {c.email && (
                            <a href={'mailto:' + c.email} className="flex items-center gap-1 text-[12px] text-zinc-500 bg-zinc-50 px-2.5 py-1.5 rounded-lg hover:bg-blue-50 hover:text-blue-600 transition-colors">
                              <EnvelopeSimple size={12} />Email
                            </a>
                          )}
                        </div>
                        <div className="flex gap-6 mt-3 pt-2.5 border-t border-zinc-100">
                          <div>
                            <p className="text-[10px] text-zinc-400">Origem</p>
                            <span className={`inline-flex text-[10px] font-bold px-2 py-0.5 rounded-full border mt-0.5 ${src.c}`}>{src.l}</span>
                          </div>
                          <div>
                            <p className="text-[10px] text-zinc-400">Cadastro</p>
                            <p className="text-[12px] font-semibold text-zinc-600 mt-0.5">{fmtDate(c.created_at)}</p>
                          </div>
                        </div>
                      </div>
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
                <span className="text-[12px] font-semibold text-zinc-500 px-2">
                  {page + 1} / {totalPages}
                </span>
                <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
                  className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 disabled:opacity-30 transition-colors">
                  <CaretRight size={14} weight="bold" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

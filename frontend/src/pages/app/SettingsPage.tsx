import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FloppyDisk, CheckCircle, Bell, User, SpinnerGap, Warning, Camera, Prohibit, UsersThree, UserPlus, Crown, Shield, Headset } from '@phosphor-icons/react'
import { settingsApi, type UserProfile } from '../../api/settings'
import { usersApi, type TeamMember } from '../../api/users'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

type Tab = 'perfil' | 'equipe' | 'notificacoes'

const inputCls = 'w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2.5 text-[13px] text-[#1D1D1F] focus:outline-none focus:border-[#0ABAB5]/50 focus:ring-2 focus:ring-[#0ABAB5]/10 transition-all'
const labelCls = 'block text-[12px] font-semibold text-zinc-500 mb-1.5'

interface NotifItem { id: string; label: string; description: string; enabled: boolean }

const DEFAULT_NOTIFS: NotifItem[] = [
  { id: 'new_lead',       label: 'Novo lead criado',          description: 'O agente cadastrou um novo lead durante a conversa',           enabled: true  },
  { id: 'new_conv',       label: 'Nova conversa iniciada',    description: 'Um cliente entrou em contato pelo WhatsApp',                   enabled: true  },
  { id: 'lead_inactive',  label: 'Lead sem atualização',      description: 'Alerta quando um lead ficar 7+ dias sem movimentação',         enabled: true  },
  { id: 'quote_accepted', label: 'Orçamento aprovado',        description: 'Notificação quando um orçamento for marcado como aprovado',    enabled: true  },
  { id: 'takeover_req',   label: 'Takeover solicitado',       description: 'Quando um operador ativar o atendimento humano',               enabled: false },
  { id: 'weekly_report',  label: 'Resumo semanal',            description: 'Relatório semanal com conversas, leads e orçamentos por e-mail', enabled: false },
]

function Toggle({ enabled, onToggle }: { enabled: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      role="switch"
      aria-checked={enabled}
      className={`relative w-10 h-6 rounded-full transition-colors cursor-pointer shrink-0 ${enabled ? 'bg-[#0ABAB5]' : 'bg-zinc-200'}`}
    >
      <span className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${enabled ? 'translate-x-4' : 'translate-x-0'}`} />
    </button>
  )
}

// ─── Perfil Tab ───────────────────────────────────────────────────────────────

function PerfilTab() {
  const qc = useQueryClient()
  const { user: storeUser, setAuth, token, tenant: storeTenant } = useAuthStore()
  const [profileSaved, setProfileSaved] = useState(false)
  const [pwSaved, setPwSaved] = useState(false)
  const [pwError, setPwError] = useState('')
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)
  const avatarInputRef = useRef<HTMLInputElement>(null)

  const nameRef   = useRef<HTMLInputElement>(null)
  const emailRef  = useRef<HTMLInputElement>(null)
  const curPwRef  = useRef<HTMLInputElement>(null)
  const newPwRef  = useRef<HTMLInputElement>(null)
  const confPwRef = useRef<HTMLInputElement>(null)

  const { data: me } = useQuery<{ user: UserProfile; tenant: { id: string; name: string; slug: string; plan: string } }>({
    queryKey: ['me'],
    queryFn: settingsApi.getMe,
  })

  const uploadAvatar = useMutation({
    mutationFn: settingsApi.uploadAvatar,
    onSuccess: (data) => {
      if (token && storeUser && storeTenant) {
        setAuth(token, { ...storeUser, avatar_url: data.avatar_url }, storeTenant)
      }
      qc.invalidateQueries({ queryKey: ['me'] })
      toast.success('Foto atualizada!')
    },
    onError: () => toast.error('Erro ao fazer upload'),
  })

  const updateMe = useMutation({
    mutationFn: settingsApi.updateMe,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['me'] })
      if (token && storeTenant) {
        setAuth(token, { id: data.id, name: data.name, email: data.email, role: data.role, avatar_url: storeUser?.avatar_url }, storeTenant)
      }
      setProfileSaved(true)
      setTimeout(() => setProfileSaved(false), 2000)
    },
  })

  const changePw = useMutation({
    mutationFn: settingsApi.changePassword,
    onSuccess: () => {
      setPwSaved(true)
      setPwError('')
      if (curPwRef.current) curPwRef.current.value = ''
      if (newPwRef.current) newPwRef.current.value = ''
      if (confPwRef.current) confPwRef.current.value = ''
      setTimeout(() => setPwSaved(false), 2000)
    },
    onError: (err: any) => {
      const raw = err?.response?.data?.detail
      setPwError(typeof raw === 'string' ? raw : Array.isArray(raw) ? raw.map((e: any) => e?.msg ?? String(e)).join(', ') : 'Erro ao alterar senha')
    },
  })

  const displayName = me?.user?.name ?? storeUser?.name ?? ''
  const displayEmail = me?.user?.email ?? storeUser?.email ?? ''
  const displayAvatar = avatarPreview ?? storeUser?.avatar_url ?? null
  const initials = displayName.split(' ').map((w: string) => w[0]).slice(0, 2).join('').toUpperCase() || 'U'

  function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onloadend = () => setAvatarPreview(reader.result as string)
    reader.readAsDataURL(file)
    uploadAvatar.mutate(file)
  }

  function saveProfile() {
    updateMe.mutate({
      name: nameRef.current?.value || undefined,
      email: emailRef.current?.value || undefined,
    })
  }

  function savePassword() {
    setPwError('')
    const cur = curPwRef.current?.value ?? ''
    const nw  = newPwRef.current?.value ?? ''
    const conf = confPwRef.current?.value ?? ''
    if (!cur || !nw) return
    if (nw !== conf) { setPwError('As senhas não coincidem'); return }
    if (nw.length < 6) { setPwError('Mínimo 6 caracteres'); return }
    changePw.mutate({ current_password: cur, new_password: nw })
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6 space-y-5">
        {/* Avatar */}
        <div className="flex items-center gap-4">
          <div className="relative shrink-0">
            <div className="w-16 h-16 rounded-full overflow-hidden bg-[#0ABAB5] flex items-center justify-center">
              {displayAvatar ? (
                <img src={displayAvatar} alt={displayName} className="w-full h-full object-cover" />
              ) : (
                <span className="text-white text-xl font-bold tracking-wide">{initials}</span>
              )}
            </div>
            <button
              onClick={() => avatarInputRef.current?.click()}
              disabled={uploadAvatar.isPending}
              className="absolute -bottom-1 -right-1 w-6 h-6 bg-white border border-zinc-200 rounded-full flex items-center justify-center shadow-sm hover:bg-zinc-50 transition-colors disabled:opacity-60"
            >
              {uploadAvatar.isPending ? <SpinnerGap size={11} className="animate-spin text-zinc-400" /> : <Camera size={11} weight="bold" className="text-zinc-500" />}
            </button>
            <input ref={avatarInputRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={handleAvatarChange} />
          </div>
          <div>
            <p className="text-[14px] font-bold text-[#1D1D1F]">{displayName}</p>
            <p className="text-[12px] text-zinc-400 mt-0.5 capitalize">{storeUser?.role}</p>
            <button onClick={() => avatarInputRef.current?.click()} className="text-[11px] text-[#0ABAB5] hover:underline mt-0.5">
              Trocar foto
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Nome completo</label>
            <input ref={nameRef} type="text" defaultValue={displayName} key={displayName} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>E-mail</label>
            <input ref={emailRef} type="email" defaultValue={displayEmail} key={displayEmail} className={inputCls} />
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={saveProfile}
            disabled={updateMe.isPending}
            className={`flex items-center gap-2 text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95 disabled:opacity-60 ${profileSaved ? 'bg-emerald-500' : 'bg-[#0ABAB5] hover:bg-[#09a8a3]'}`}
          >
            {updateMe.isPending ? <SpinnerGap size={14} className="animate-spin" /> : profileSaved ? <CheckCircle size={14} weight="fill" /> : <FloppyDisk size={14} weight="bold" />}
            {profileSaved ? 'Salvo!' : 'Salvar Perfil'}
          </button>
        </div>
      </div>

      {/* Change password */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6 space-y-4">
        <div>
          <p className="text-[14px] font-bold text-[#1D1D1F]">Alterar Senha</p>
          <p className="text-[12px] text-zinc-400 mt-0.5">Deixe em branco para manter a senha atual</p>
        </div>
        <div className="space-y-3">
          <div>
            <label className={labelCls}>Senha atual</label>
            <input ref={curPwRef} type="password" placeholder="••••••••" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Nova senha</label>
            <input ref={newPwRef} type="password" placeholder="••••••••" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Confirmar nova senha</label>
            <input ref={confPwRef} type="password" placeholder="••••••••" className={inputCls} />
          </div>
        </div>
        {pwError && (
          <div className="flex items-center gap-2 text-red-500">
            <Warning size={13} weight="fill" />
            <span className="text-[12px]">{pwError}</span>
          </div>
        )}
        <div className="flex justify-end">
          <button
            onClick={savePassword}
            disabled={changePw.isPending}
            className={`flex items-center gap-2 text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95 disabled:opacity-60 ${pwSaved ? 'bg-emerald-500' : 'bg-[#0ABAB5] hover:bg-[#09a8a3]'}`}
          >
            {changePw.isPending ? <SpinnerGap size={14} className="animate-spin" /> : pwSaved ? <CheckCircle size={14} weight="fill" /> : <FloppyDisk size={14} weight="bold" />}
            {pwSaved ? 'Senha alterada!' : 'Alterar Senha'}
          </button>
        </div>
      </div>
    </div>
  )
}

const NOTIF_STORAGE_KEY = 'crm_notification_prefs'

function loadNotifPrefs(): NotifItem[] {
  try {
    const stored = localStorage.getItem(NOTIF_STORAGE_KEY)
    if (stored) {
      const parsed: Record<string, boolean> = JSON.parse(stored)
      return DEFAULT_NOTIFS.map(n => ({ ...n, enabled: parsed[n.id] ?? n.enabled }))
    }
  } catch { /* ignore */ }
  return DEFAULT_NOTIFS
}

// ─── Notificações Tab ─────────────────────────────────────────────────────────

function NotificacoesTab() {
  const [notifs, setNotifs] = useState<NotifItem[]>(loadNotifPrefs)
  const [saved, setSaved] = useState(false)

  function toggleNotif(id: string) {
    setNotifs(prev => prev.map(n => n.id === id ? { ...n, enabled: !n.enabled } : n))
  }

  function handleSave() {
    const prefs: Record<string, boolean> = {}
    notifs.forEach(n => { prefs[n.id] = n.enabled })
    localStorage.setItem(NOTIF_STORAGE_KEY, JSON.stringify(prefs))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-zinc-100 bg-zinc-50/60">
          <p className="text-[13px] font-bold text-[#1D1D1F]">Preferências de Notificação</p>
          <p className="text-[12px] text-zinc-400 mt-0.5">
            {notifs.filter(n => n.enabled).length} de {notifs.length} notificações ativas
          </p>
        </div>
        <div className="divide-y divide-zinc-100">
          {notifs.map(n => (
            <div key={n.id} className="flex items-center gap-4 px-5 py-4">
              <div className="flex-1 min-w-0">
                <p className="text-[13px] font-semibold text-[#1D1D1F]">{n.label}</p>
                <p className="text-[12px] text-zinc-400 mt-0.5 leading-snug">{n.description}</p>
              </div>
              <Toggle enabled={n.enabled} onToggle={() => toggleNotif(n.id)} />
            </div>
          ))}
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className={`flex items-center gap-2 text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95 ${saved ? 'bg-emerald-500' : 'bg-[#0ABAB5] hover:bg-[#09a8a3]'}`}
        >
          {saved ? <CheckCircle size={14} weight="fill" /> : <FloppyDisk size={14} weight="bold" />}
          {saved ? 'Salvo!' : 'Salvar Preferências'}
        </button>
      </div>
    </div>
  )
}

// ─── Assinatura Tab ───────────────────────────────────────────────────────────

// ─── Equipe Tab ───────────────────────────────────────────────────────────────

const ROLE_LABELS: Record<string, string> = { admin: 'Admin', manager: 'Gerente', operator: 'Operador' }
const ROLE_ICONS: Record<string, React.ReactNode> = {
  admin:    <Crown size={11} weight="fill" className="text-amber-500" />,
  manager:  <Shield size={11} weight="fill" className="text-blue-500" />,
  operator: <Headset size={11} weight="fill" className="text-zinc-400" />,
}

function EquipeTab() {
  const qc = useQueryClient()
  const { user: me } = useAuthStore()
  const [showInvite, setShowInvite] = useState(false)
  const [inviteName, setInviteName] = useState('')
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('operator')

  const { data: members = [], isLoading } = useQuery<TeamMember[]>({
    queryKey: ['team-members'],
    queryFn: usersApi.list,
  })

  const invite = useMutation({
    mutationFn: usersApi.invite,
    onSuccess: () => {
      toast.success('Convite enviado por e-mail')
      qc.invalidateQueries({ queryKey: ['team-members'] })
      setShowInvite(false)
      setInviteName('')
      setInviteEmail('')
      setInviteRole('operator')
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail ?? 'Erro ao convidar usuário'
      toast.error(typeof msg === 'string' ? msg : 'Erro ao convidar usuário')
    },
  })

  const updateRole = useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) => usersApi.updateRole(id, role),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['team-members'] }),
    onError: () => toast.error('Erro ao alterar role'),
  })

  const toggleActive = useMutation({
    mutationFn: (id: string) => usersApi.toggleActive(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['team-members'] }),
    onError: () => toast.error('Erro ao alterar status'),
  })

  const isAdmin = me?.role === 'admin'

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[13px] font-bold text-[#1D1D1F]">Membros da equipe</p>
          <p className="text-[12px] text-zinc-400 mt-0.5">{members.length} {members.length === 1 ? 'membro' : 'membros'}</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setShowInvite(v => !v)}
            className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#089B97] text-white text-[12px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95"
          >
            <UserPlus size={14} weight="bold" />
            Convidar membro
          </button>
        )}
      </div>

      {/* Invite form */}
      {showInvite && (
        <div className="bg-white rounded-2xl border border-zinc-200 p-4 space-y-3 shadow-sm">
          <p className="text-[12px] font-bold text-zinc-600">Novo convite</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className={labelCls}>Nome</label>
              <input
                value={inviteName}
                onChange={e => setInviteName(e.target.value)}
                placeholder="João Silva"
                className={inputCls}
              />
            </div>
            <div>
              <label className={labelCls}>E-mail</label>
              <input
                type="email"
                value={inviteEmail}
                onChange={e => setInviteEmail(e.target.value)}
                placeholder="joao@empresa.com"
                className={inputCls}
              />
            </div>
            <div>
              <label className={labelCls}>Role</label>
              <select value={inviteRole} onChange={e => setInviteRole(e.target.value)} className={inputCls}>
                <option value="operator">Operador</option>
                <option value="manager">Gerente</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowInvite(false)} className="text-[12px] font-semibold px-4 py-2 rounded-xl border border-zinc-200 text-zinc-500 hover:bg-zinc-50 transition-all">
              Cancelar
            </button>
            <button
              onClick={() => invite.mutate({ name: inviteName, email: inviteEmail, role: inviteRole })}
              disabled={invite.isPending || !inviteName || !inviteEmail}
              className="flex items-center gap-2 text-[12px] font-semibold px-4 py-2 rounded-xl bg-[#0ABAB5] text-white hover:bg-[#089B97] transition-all disabled:opacity-60"
            >
              {invite.isPending ? <SpinnerGap size={12} className="animate-spin" /> : <UserPlus size={12} weight="bold" />}
              {invite.isPending ? 'Enviando...' : 'Enviar convite'}
            </button>
          </div>
        </div>
      )}

      {/* Members list */}
      <div className="bg-white rounded-2xl border border-zinc-100 shadow-[0_1px_12px_rgba(0,0,0,0.06)] overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-10">
            <SpinnerGap size={24} className="animate-spin text-[#0ABAB5]" />
          </div>
        ) : members.length === 0 ? (
          <div className="flex flex-col items-center py-10 text-zinc-300">
            <UsersThree size={36} weight="duotone" />
            <p className="text-sm mt-2 text-zinc-400">Nenhum membro ainda</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-100">
            {members.map(m => (
              <div key={m.id} className={`flex items-center gap-3 px-5 py-3.5 transition-colors ${!m.is_active ? 'opacity-50' : 'hover:bg-zinc-50/60'}`}>
                {/* Avatar */}
                <div className="w-8 h-8 rounded-full bg-[#0ABAB5]/10 flex items-center justify-center shrink-0 text-[13px] font-bold text-[#0ABAB5]">
                  {m.name.charAt(0).toUpperCase()}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{m.name}</p>
                    {m.id === me?.id && (
                      <span className="text-[10px] font-semibold text-zinc-400 bg-zinc-100 px-1.5 py-0.5 rounded-full">você</span>
                    )}
                    {!m.is_active && (
                      <span className="text-[10px] font-semibold text-red-400 bg-red-50 px-1.5 py-0.5 rounded-full">inativo</span>
                    )}
                  </div>
                  <p className="text-[11px] text-zinc-400 truncate">{m.email}</p>
                </div>

                {/* Role selector */}
                {isAdmin && m.id !== me?.id ? (
                  <select
                    value={m.role}
                    onChange={e => updateRole.mutate({ id: m.id, role: e.target.value })}
                    className="text-[11px] font-semibold bg-zinc-50 border border-zinc-200 rounded-lg px-2 py-1 text-zinc-600 focus:outline-none focus:border-[#0ABAB5]/50 transition-all"
                  >
                    <option value="operator">Operador</option>
                    <option value="manager">Gerente</option>
                    <option value="admin">Admin</option>
                  </select>
                ) : (
                  <span className="flex items-center gap-1 text-[11px] font-semibold text-zinc-500 bg-zinc-100 px-2.5 py-1 rounded-full">
                    {ROLE_ICONS[m.role]}
                    {ROLE_LABELS[m.role]}
                  </span>
                )}

                {/* Actions */}
                {isAdmin && m.id !== me?.id && (
                  <button
                    onClick={() => toggleActive.mutate(m.id)}
                    title={m.is_active ? 'Desativar' : 'Reativar'}
                    className="p-1.5 rounded-lg text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 transition-all"
                  >
                    <Prohibit size={14} weight="bold" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>('perfil')

  const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'perfil',       label: 'Perfil',        icon: <User size={14} weight="duotone" />       },
    { key: 'equipe',       label: 'Equipe',        icon: <UsersThree size={14} weight="duotone" /> },
    { key: 'notificacoes', label: 'Notificações',  icon: <Bell size={14} weight="duotone" />       },
  ]

  return (
    <div className="p-4 md:p-6 space-y-5 pb-6">
      {/* Header */}
      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100">
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight">Configurações</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-zinc-100/70 p-1 rounded-2xl overflow-x-auto">
        {TABS.map(({ key, label, icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex-shrink-0 flex items-center justify-center gap-1.5 text-[12px] font-semibold py-2 px-3 rounded-xl transition-all ${
              tab === key ? 'bg-white text-[#0ABAB5] shadow-sm' : 'text-zinc-500 hover:text-zinc-700'
            }`}
          >
            {icon}
            <span className="hidden sm:inline">{label}</span>
            <span className="sm:hidden">{label.split(' ')[0]}</span>
          </button>
        ))}
      </div>

      {tab === 'perfil'       && <PerfilTab />}
      {tab === 'equipe'       && <EquipeTab />}
      {tab === 'notificacoes' && <NotificacoesTab />}
    </div>
  )
}

import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FloppyDisk, CheckCircle, Camera, Buildings, Bell, User, SpinnerGap, Warning, Plugs, CreditCard, ArrowSquareOut, Prohibit, UsersThree, UserPlus, Crown, Shield, Headset, WhatsappLogo, Plus, Gear } from '@phosphor-icons/react'
import { settingsApi, subscriptionApi, type UserProfile, type TenantProfile, type Integrations, type CompanyProfile, type BankingData, type SubscriptionInfo } from '../../api/settings'
import { usersApi, type TeamMember } from '../../api/users'
import { agentsApi, type AgentInstance } from '../../api/agents'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

type Tab = 'perfil' | 'empresa' | 'equipe' | 'whatsapp' | 'notificacoes' | 'integracoes' | 'assinatura'

const inputCls = 'w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2.5 text-[13px] text-[#1D1D1F] focus:outline-none focus:border-[#0ABAB5]/50 focus:ring-2 focus:ring-[#0ABAB5]/10 transition-all'
const labelCls = 'block text-[12px] font-semibold text-zinc-500 mb-1.5'

interface NotifItem { id: string; label: string; description: string; enabled: boolean }

const DEFAULT_NOTIFS: NotifItem[] = [
  { id: 'leads',     label: 'Novos Leads',        description: 'Receber notificação quando um novo lead for criado', enabled: true  },
  { id: 'conv',      label: 'Conversas',           description: 'Alertas de novas mensagens',                        enabled: true  },
  { id: 'stock',     label: 'Estoque Baixo',       description: 'Avisos quando produto atingir nível mínimo',        enabled: true  },
  { id: 'contracts', label: 'Contratos Vencendo',  description: 'Lembretes 30 dias antes do vencimento',            enabled: false },
  { id: 'report',    label: 'Relatório Semanal',   description: 'Resumo semanal por e-mail',                        enabled: false },
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

// ─── Empresa Tab ──────────────────────────────────────────────────────────────

function SaveBtn({ isPending, saved, label, onClick }: { isPending: boolean; saved: boolean; label: string; onClick: () => void }) {
  return (
    <div className="flex justify-end pt-1">
      <button
        onClick={onClick}
        disabled={isPending}
        className={`flex items-center gap-2 text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95 disabled:opacity-60 ${saved ? 'bg-emerald-500' : 'bg-[#0ABAB5] hover:bg-[#09a8a3]'}`}
      >
        {isPending ? <SpinnerGap size={14} className="animate-spin" /> : saved ? <CheckCircle size={14} weight="fill" /> : <FloppyDisk size={14} weight="bold" />}
        {saved ? 'Salvo!' : label}
      </button>
    </div>
  )
}

function EmpresaTab() {
  const qc = useQueryClient()
  const logoInputRef = useRef<HTMLInputElement>(null)

  // ── Tenant (name, color, logo) ─────────────────────────────────────────────
  const [primaryColor, setPrimaryColor] = useState('#0ABAB5')
  const [tenantSaved, setTenantSaved] = useState(false)
  const [logoSaved, setLogoSaved] = useState(false)
  const [localLogoUrl, setLocalLogoUrl] = useState<string | null>(null)
  const nameRef = useRef<HTMLInputElement>(null)

  const { data: tenant } = useQuery<TenantProfile>({ queryKey: ['tenant'], queryFn: settingsApi.getTenant })

  useEffect(() => {
    if (tenant?.primary_color) setPrimaryColor(tenant.primary_color)
  }, [tenant?.primary_color])

  const updateTenant = useMutation({
    mutationFn: settingsApi.updateTenant,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['tenant'] }); setTenantSaved(true); setTimeout(() => setTenantSaved(false), 2000) },
  })

  const uploadLogo = useMutation({
    mutationFn: settingsApi.uploadLogo,
    onSuccess: (data) => {
      setLocalLogoUrl(data.logo_url)
      qc.invalidateQueries({ queryKey: ['tenant'] })
      setLogoSaved(true)
      setTimeout(() => setLogoSaved(false), 2500)
    },
  })

  function handleLogoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) uploadLogo.mutate(file)
  }

  const displayLogoUrl = localLogoUrl ?? tenant?.logo_url
  const displayPlan: Record<string, string> = { starter: 'Starter', pro: 'Pro', enterprise: 'Enterprise' }

  // ── Company profile ────────────────────────────────────────────────────────
  const [companySaved, setCompanySaved] = useState(false)
  const [company, setCompany] = useState<Partial<CompanyProfile>>({})
  const [companyLoaded, setCompanyLoaded] = useState(false)

  const { data: companyData } = useQuery<CompanyProfile>({ queryKey: ['company'], queryFn: settingsApi.getCompany })
  if (companyData && !companyLoaded) { setCompany(companyData); setCompanyLoaded(true) }

  const updateCompany = useMutation({
    mutationFn: settingsApi.updateCompany,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['company'] }); setCompanySaved(true); setTimeout(() => setCompanySaved(false), 2000) },
  })

  // ── Banking ────────────────────────────────────────────────────────────────
  const [bankingSaved, setBankingSaved] = useState(false)
  const [banking, setBanking] = useState<Partial<BankingData>>({})
  const [bankingLoaded, setBankingLoaded] = useState(false)

  const { data: bankingData } = useQuery<BankingData>({ queryKey: ['banking'], queryFn: settingsApi.getBanking })
  if (bankingData && !bankingLoaded) { setBanking(bankingData); setBankingLoaded(true) }

  const updateBanking = useMutation({
    mutationFn: settingsApi.updateBanking,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['banking'] }); setBankingSaved(true); setTimeout(() => setBankingSaved(false), 2000) },
  })

  function setC(k: keyof CompanyProfile, v: string) { setCompany(p => ({ ...p, [k]: v })) }
  function setB(k: keyof BankingData, v: string) { setBanking(p => ({ ...p, [k]: v })) }

  return (
    <div className="space-y-4">
      {/* ── Logo + Aparência ─────────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6 space-y-5">
        <p className="text-[14px] font-bold text-[#1D1D1F]">Identidade Visual</p>

        {/* Logo */}
        <div>
          <p className={labelCls}>Logo da Empresa</p>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-xl border-2 border-dashed border-zinc-200 bg-zinc-50 flex items-center justify-center text-[#0ABAB5] font-bold text-lg overflow-hidden shrink-0">
              {displayLogoUrl
                ? <img src={displayLogoUrl} alt="logo" className="w-full h-full object-contain" />
                : (tenant?.name?.[0] ?? 'C').toUpperCase()
              }
            </div>
            <div>
              <input ref={logoInputRef} type="file" accept="image/png,image/jpeg,image/svg+xml,image/webp" className="hidden" onChange={handleLogoChange} />
              <button
                onClick={() => logoInputRef.current?.click()}
                disabled={uploadLogo.isPending}
                className="flex items-center gap-1.5 text-[13px] font-semibold text-[#0ABAB5] border border-[#0ABAB5]/30 hover:bg-[#0ABAB5]/5 px-3 py-1.5 rounded-xl transition-colors disabled:opacity-60"
              >
                {uploadLogo.isPending ? <SpinnerGap size={12} className="animate-spin" /> : logoSaved ? <CheckCircle size={12} weight="fill" /> : <Camera size={12} weight="bold" />}
                {uploadLogo.isPending ? 'Enviando...' : logoSaved ? 'Logo atualizado!' : 'Alterar logo'}
              </button>
              <p className="text-[11px] text-zinc-400 mt-1">PNG, JPG, SVG ou WebP — máx. 2 MB</p>
            </div>
          </div>
        </div>

        {/* Name + plan + color */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Nome da Empresa</label>
            <input ref={nameRef} type="text" defaultValue={tenant?.name ?? ''} key={tenant?.name} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Plano</label>
            <input type="text" value={displayPlan[tenant?.plan ?? ''] ?? tenant?.plan ?? ''} readOnly className={`${inputCls} bg-zinc-100 cursor-not-allowed text-zinc-400`} />
          </div>
          <div>
            <label className={labelCls}>Slug</label>
            <input type="text" value={tenant?.slug ?? ''} readOnly className={`${inputCls} bg-zinc-100 cursor-not-allowed text-zinc-400`} />
          </div>
          <div>
            <label className={labelCls}>Cor primária</label>
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg border-2 border-white shadow-md ring-1 ring-zinc-200 shrink-0" style={{ backgroundColor: primaryColor }} />
              <span className="text-[12px] font-mono font-semibold text-zinc-500 flex-1">{primaryColor.toUpperCase()}</span>
              <input type="color" value={primaryColor} onChange={e => setPrimaryColor(e.target.value)} className="w-9 h-9 rounded-lg border border-zinc-200 cursor-pointer bg-transparent p-0.5" />
            </div>
          </div>
        </div>

        <SaveBtn isPending={updateTenant.isPending} saved={tenantSaved} label="Salvar Aparência" onClick={() => updateTenant.mutate({ name: nameRef.current?.value || undefined, primary_color: primaryColor })} />
      </div>

      {/* ── Dados da Empresa ────────────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6 space-y-4">
        <p className="text-[14px] font-bold text-[#1D1D1F]">Dados da Empresa</p>
        <p className="text-[12px] text-zinc-400 -mt-1">Aparecem nas propostas, notas fiscais e comunicações</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>CNPJ</label>
            <input type="text" value={company.cnpj ?? ''} onChange={e => setC('cnpj', e.target.value)} placeholder="00.000.000/0001-00" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Telefone</label>
            <input type="text" value={company.phone ?? ''} onChange={e => setC('phone', e.target.value)} placeholder="(11) 99999-9999" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>E-mail Comercial</label>
            <input type="email" value={company.email ?? ''} onChange={e => setC('email', e.target.value)} placeholder="contato@empresa.com.br" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Site</label>
            <input type="text" value={company.website ?? ''} onChange={e => setC('website', e.target.value)} placeholder="https://empresa.com.br" className={inputCls} />
          </div>
        </div>

        <p className="text-[13px] font-semibold text-zinc-600 pt-1">Endereço</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="sm:col-span-2">
            <label className={labelCls}>Logradouro</label>
            <input type="text" value={company.address_street ?? ''} onChange={e => setC('address_street', e.target.value)} placeholder="Rua, Avenida, etc." className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Número</label>
            <input type="text" value={company.address_number ?? ''} onChange={e => setC('address_number', e.target.value)} placeholder="123" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Complemento</label>
            <input type="text" value={company.address_complement ?? ''} onChange={e => setC('address_complement', e.target.value)} placeholder="Sala 45, Apto 2..." className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Bairro</label>
            <input type="text" value={company.address_neighborhood ?? ''} onChange={e => setC('address_neighborhood', e.target.value)} placeholder="Centro" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>CEP</label>
            <input type="text" value={company.address_zip ?? ''} onChange={e => setC('address_zip', e.target.value)} placeholder="00000-000" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Cidade</label>
            <input type="text" value={company.address_city ?? ''} onChange={e => setC('address_city', e.target.value)} placeholder="São Paulo" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Estado (UF)</label>
            <select value={company.address_state ?? ''} onChange={e => setC('address_state', e.target.value)} className={inputCls}>
              <option value="">Selecione...</option>
              {['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'].map(uf => (
                <option key={uf} value={uf}>{uf}</option>
              ))}
            </select>
          </div>
        </div>

        <SaveBtn isPending={updateCompany.isPending} saved={companySaved} label="Salvar Dados da Empresa" onClick={() => updateCompany.mutate(company)} />
      </div>

      {/* ── Dados Bancários ────────────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6 space-y-4">
        <p className="text-[14px] font-bold text-[#1D1D1F]">Dados Bancários</p>
        <p className="text-[12px] text-zinc-400 -mt-1">Exibidos nas propostas para os clientes efetuarem pagamentos</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="sm:col-span-2">
            <label className={labelCls}>Beneficiário</label>
            <input type="text" value={banking.beneficiary ?? ''} onChange={e => setB('beneficiary', e.target.value)} placeholder="Razão social ou nome completo" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Banco</label>
            <input type="text" value={banking.bank_name ?? ''} onChange={e => setB('bank_name', e.target.value)} placeholder="Nubank, Itaú, Bradesco..." className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Tipo de Conta</label>
            <select value={banking.account_type ?? 'corrente'} onChange={e => setB('account_type', e.target.value)} className={inputCls}>
              <option value="corrente">Conta Corrente</option>
              <option value="poupanca">Conta Poupança</option>
              <option value="pagamento">Conta de Pagamento</option>
            </select>
          </div>
          <div>
            <label className={labelCls}>Agência</label>
            <input type="text" value={banking.agency ?? ''} onChange={e => setB('agency', e.target.value)} placeholder="0001" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Conta</label>
            <input type="text" value={banking.account ?? ''} onChange={e => setB('account', e.target.value)} placeholder="12345-6" className={inputCls} />
          </div>
        </div>

        <p className="text-[13px] font-semibold text-zinc-600 pt-1">PIX</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Tipo de Chave PIX</label>
            <select value={banking.pix_key_type ?? 'cpf_cnpj'} onChange={e => setB('pix_key_type', e.target.value)} className={inputCls}>
              <option value="cpf_cnpj">CPF / CNPJ</option>
              <option value="email">E-mail</option>
              <option value="phone">Telefone</option>
              <option value="random">Chave Aleatória</option>
            </select>
          </div>
          <div>
            <label className={labelCls}>Chave PIX</label>
            <input type="text" value={banking.pix_key ?? ''} onChange={e => setB('pix_key', e.target.value)} placeholder="00.000.000/0001-00" className={inputCls} />
          </div>
        </div>

        <SaveBtn isPending={updateBanking.isPending} saved={bankingSaved} label="Salvar Dados Bancários" onClick={() => updateBanking.mutate(banking)} />
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

// ─── Integrações Tab ──────────────────────────────────────────────────────────

function IntegracoesTab() {
  const qc = useQueryClient()
  const [saved, setSaved] = useState(false)
  const [form, setForm] = useState<Partial<Integrations>>({})
  const [loaded, setLoaded] = useState(false)

  const { data } = useQuery<Integrations>({
    queryKey: ['integrations'],
    queryFn: settingsApi.getIntegrations,
  })

  if (data && !loaded) {
    setForm(data)
    setLoaded(true)
  }

  const update = useMutation({
    mutationFn: settingsApi.updateIntegrations,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['integrations'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    },
  })

  const testWebhook = useMutation({
    mutationFn: settingsApi.testWebhook,
    onSuccess: (data) => toast.success(`Webhook OK — HTTP ${data.http_status}`),
    onError: (err: any) => toast.error(err?.response?.data?.detail ?? 'Erro ao testar webhook'),
  })

  function set(key: keyof Integrations, value: string) {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="space-y-4">
      {/* Webhook de Eventos */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6 space-y-4">
        <div>
          <p className="text-[14px] font-bold text-[#1D1D1F]">Webhook de Eventos</p>
          <p className="text-[12px] text-zinc-400 mt-0.5">Receba eventos do CRM em qualquer sistema externo — Zapier, n8n, Make, sistemas próprios</p>
        </div>
        <div className="space-y-3">
          <div>
            <label className={labelCls}>URL do Webhook <span className="text-zinc-400 font-normal">(opcional)</span></label>
            <div className="flex gap-2">
              <input
                type="url"
                value={(form as any).webhook_url ?? ''}
                onChange={e => set('webhook_url' as any, e.target.value)}
                placeholder="https://hooks.zapier.com/hooks/catch/..."
                className={inputCls}
              />
              <button
                type="button"
                onClick={() => testWebhook.mutate()}
                disabled={testWebhook.isPending || !(form as any).webhook_url}
                className="shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-xl border border-zinc-200 text-[12px] font-medium text-zinc-600 hover:bg-zinc-50 disabled:opacity-40 transition-all"
              >
                {testWebhook.isPending ? <SpinnerGap size={13} className="animate-spin" /> : <ArrowSquareOut size={13} />}
                Testar
              </button>
            </div>
          </div>
          <div className="bg-zinc-50 rounded-xl p-3 space-y-1.5">
            <p className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wide">Eventos enviados</p>
            {['new_contact', 'message_received', 'agent_response_sent', 'conversation_closed'].map(ev => (
              <div key={ev} className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#0ABAB5] shrink-0" />
                <span className="text-[12px] font-mono text-zinc-600">{ev}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Infra info */}
      <div className="bg-zinc-50 rounded-2xl border border-zinc-100 p-4 space-y-2">
        <p className="text-[12px] font-bold text-zinc-500">Infraestrutura Docker</p>
        <p className="text-[11px] text-zinc-400 leading-relaxed">
          As configurações de banco de dados, Redis, MinIO e RabbitMQ são definidas no arquivo <code className="bg-zinc-100 px-1 rounded text-[10px]">.env</code> na raiz do projeto e aplicadas ao subir os containers. Edite esse arquivo para alterar conexões de infraestrutura.
        </p>
      </div>

      <div className="flex justify-end">
        <button
          onClick={() => update.mutate(form)}
          disabled={update.isPending}
          className={`flex items-center gap-2 text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95 disabled:opacity-60 ${saved ? 'bg-emerald-500' : 'bg-[#0ABAB5] hover:bg-[#09a8a3]'}`}
        >
          {update.isPending ? <SpinnerGap size={14} className="animate-spin" /> : saved ? <CheckCircle size={14} weight="fill" /> : <FloppyDisk size={14} weight="bold" />}
          {saved ? 'Salvo!' : 'Salvar Integrações'}
        </button>
      </div>
    </div>
  )
}

// ─── Assinatura Tab ───────────────────────────────────────────────────────────

type FeatureValue = boolean | string
interface PlanFeatureRow { label: string; starter: FeatureValue; pro: FeatureValue; enterprise: FeatureValue }

const FEATURE_MATRIX: PlanFeatureRow[] = [
  { label: 'Clientes & Contatos',          starter: true,           pro: true,              enterprise: true },
  { label: 'Pipeline de Leads (Kanban)',    starter: true,           pro: true,              enterprise: true },
  { label: 'Conversas WhatsApp',           starter: true,           pro: true,              enterprise: true },
  { label: 'Orçamentos',                   starter: 'Básico',       pro: 'Ilimitado',       enterprise: 'Ilimitado' },
  { label: 'Contratos',                    starter: 'Básico',       pro: 'Ilimitado',       enterprise: 'Ilimitado' },
  { label: 'Estoque & Inventário',         starter: false,          pro: true,              enterprise: true },
  { label: 'Relatórios PDF',               starter: false,          pro: true,              enterprise: true },
  { label: 'Templates DOCX',               starter: false,          pro: true,              enterprise: true },
  { label: 'Agente IA WhatsApp',           starter: '1 número',     pro: 'Múltiplos',       enterprise: 'Ilimitado' },
  { label: 'RAG / Documentos IA',          starter: false,          pro: true,              enterprise: true },
  { label: 'Dashboard avançado',           starter: false,          pro: true,              enterprise: true },
  { label: 'Membros da equipe',            starter: 'Até 3',        pro: 'Ilimitado',       enterprise: 'Ilimitado' },
  { label: 'Identidade visual (logo)',     starter: true,           pro: true,              enterprise: true },
  { label: 'Dados bancários / PIX',        starter: true,           pro: true,              enterprise: true },
  { label: 'API & Integrações custom',     starter: false,          pro: false,             enterprise: true },
  { label: 'Suporte',                      starter: 'Por e-mail',   pro: 'Prioritário',     enterprise: 'Dedicado' },
]

const PLAN_PRICES: Record<string, number> = { starter: 297, pro: 497 }

function FeatureCell({ value }: { value: FeatureValue }) {
  if (value === true)  return <CheckCircle size={15} weight="fill" className="text-[#0ABAB5] mx-auto" />
  if (value === false) return <span className="text-zinc-300 text-lg mx-auto block text-center">—</span>
  return <span className="text-[11px] text-zinc-500 text-center block">{value}</span>
}

function StatusBadge({ status }: { status: string | null }) {
  if (!status) return null
  const cfg: Record<string, { label: string; cls: string }> = {
    authorized: { label: 'Ativa',         cls: 'bg-emerald-100 text-emerald-700' },
    pending:    { label: 'Pendente',       cls: 'bg-amber-100 text-amber-700' },
    paused:     { label: 'Pausada',        cls: 'bg-zinc-100 text-zinc-500' },
    cancelled:  { label: 'Cancelada',      cls: 'bg-red-100 text-red-600' },
    trial:      { label: 'Teste — Pro',    cls: 'bg-violet-100 text-violet-700' },
  }
  const c = cfg[status] ?? { label: status, cls: 'bg-zinc-100 text-zinc-500' }
  return (
    <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full ${c.cls}`}>{c.label}</span>
  )
}

function AssinaturaTab() {
  const { tenant: storeTenant } = useAuthStore()
  const { data } = useQuery<SubscriptionInfo>({
    queryKey: ['subscription'],
    queryFn: subscriptionApi.getCurrent,
  })

  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null)
  const [cancelConfirm, setCancelConfirm] = useState(false)
  const cancelMut = useMutation({
    mutationFn: subscriptionApi.cancel,
    onSuccess: () => window.location.reload(),
  })

  async function handleCheckout(plan: 'starter' | 'pro') {
    setCheckoutLoading(plan)
    try {
      const res = await subscriptionApi.checkout(plan)
      window.location.href = res.checkout_url
    } catch {
      setCheckoutLoading(null)
    }
  }

  const currentPlan = data?.plan ?? storeTenant?.plan ?? 'starter'
  const effectivePlan = storeTenant?.effective_plan ?? currentPlan
  const subStatus = data?.subscription_status
  const trialDays = storeTenant?.trial_days_remaining ?? 0
  const isTrial = !!storeTenant?.trial_ends_at && trialDays > 0

  const planLabel: Record<string, string> = { starter: 'Starter', pro: 'Pro', enterprise: 'Enterprise' }

  return (
    <div className="space-y-4">
      {/* Current plan card */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[12px] font-semibold text-zinc-400 uppercase tracking-wider mb-1">Plano Atual</p>
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-[22px] font-black text-[#1D1D1F]">{planLabel[effectivePlan] ?? effectivePlan}</p>
              {isTrial && (
                <span className="bg-amber-100 text-amber-700 text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest">
                  Trial
                </span>
              )}
            </div>
            {isTrial && (
              <p className="text-[12px] text-amber-600 mt-1 font-medium">
                Acesso completo Pro por mais {trialDays} dia{trialDays !== 1 ? 's' : ''}
              </p>
            )}
            {data?.mp_payer_email && (
              <p className="text-[12px] text-zinc-400 mt-0.5">{data.mp_payer_email}</p>
            )}
          </div>
          <StatusBadge status={subStatus ?? (isTrial ? 'trial' : null)} />
        </div>

        {subStatus === 'authorized' && (
          <div className="mt-4 pt-4 border-t border-zinc-100 flex gap-3">
            {!cancelConfirm ? (
              <button
                onClick={() => setCancelConfirm(true)}
                className="flex items-center gap-1.5 text-[12px] font-semibold text-red-500 hover:text-red-600 transition-colors"
              >
                <Prohibit size={13} weight="bold" />
                Cancelar assinatura
              </button>
            ) : (
              <div className="flex items-center gap-3">
                <p className="text-[12px] text-zinc-500">Confirmar cancelamento?</p>
                <button
                  onClick={() => cancelMut.mutate()}
                  disabled={cancelMut.isPending}
                  className="text-[12px] font-bold text-white bg-red-500 hover:bg-red-600 px-3 py-1 rounded-lg transition-colors"
                >
                  {cancelMut.isPending ? 'Cancelando...' : 'Sim, cancelar'}
                </button>
                <button onClick={() => setCancelConfirm(false)} className="text-[12px] text-zinc-400 hover:text-zinc-600">
                  Não
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Feature matrix table */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-4 border-b border-zinc-100">
          <div className="p-4 text-[11px] font-bold text-zinc-400 uppercase tracking-wider">Funcionalidade</div>
          {(['starter', 'pro', 'enterprise'] as const).map(plan => {
            const isActive = effectivePlan === plan && (subStatus === 'authorized' || (isTrial && plan === 'pro'))
            return (
              <div key={plan} className={`p-4 text-center border-l border-zinc-100 ${plan === 'pro' ? 'bg-violet-50' : ''}`}>
                {plan === 'pro' && (
                  <span className="block text-[9px] font-black text-violet-500 uppercase tracking-widest mb-1">Mais Popular</span>
                )}
                <p className="text-[13px] font-black text-[#1D1D1F] capitalize">{plan}</p>
                {plan !== 'enterprise' ? (
                  <p className="text-[11px] text-zinc-400 mt-0.5">R${PLAN_PRICES[plan]}/mês</p>
                ) : (
                  <p className="text-[11px] text-zinc-400 mt-0.5">Sob consulta</p>
                )}
                {isActive && (
                  <span className="inline-flex items-center gap-1 bg-[#0ABAB5]/10 text-[#0ABAB5] text-[10px] font-bold px-2 py-0.5 rounded-full mt-1.5">
                    <CheckCircle size={10} weight="fill" />
                    Seu plano
                  </span>
                )}
              </div>
            )
          })}
        </div>

        {/* Rows */}
        {FEATURE_MATRIX.map((row, i) => (
          <div key={row.label} className={`grid grid-cols-4 border-b border-zinc-50 ${i % 2 === 0 ? '' : 'bg-zinc-50/40'}`}>
            <div className="p-3 px-4 text-[12px] text-zinc-600 font-medium flex items-center">{row.label}</div>
            {(['starter', 'pro', 'enterprise'] as const).map(plan => (
              <div key={plan} className={`p-3 border-l border-zinc-100 flex items-center justify-center ${plan === 'pro' ? 'bg-violet-50/50' : ''}`}>
                <FeatureCell value={row[plan]} />
              </div>
            ))}
          </div>
        ))}

        {/* CTA row */}
        <div className="grid grid-cols-4 bg-zinc-50/60 border-t border-zinc-100">
          <div className="p-4" />
          {(['starter', 'pro', 'enterprise'] as const).map(plan => {
            const isActive = (effectivePlan === plan && subStatus === 'authorized') || (isTrial && plan === 'pro' && !subStatus)
            return (
              <div key={plan} className={`p-3 border-l border-zinc-100 ${plan === 'pro' ? 'bg-violet-50/50' : ''}`}>
                {isActive ? (
                  <div className="flex items-center gap-1.5 justify-center text-[12px] font-bold text-[#0ABAB5] py-1">
                    <CheckCircle size={13} weight="fill" />
                    {isTrial && plan === 'pro' ? 'Em uso (trial)' : 'Plano atual'}
                  </div>
                ) : plan === 'enterprise' ? (
                  <a
                    href="https://wa.me/5511999999999?text=Quero+o+plano+Enterprise"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full flex items-center justify-center gap-1.5 text-[12px] font-bold py-2 rounded-xl bg-zinc-700 hover:bg-zinc-800 text-white transition-all active:scale-95"
                  >
                    <ArrowSquareOut size={12} weight="bold" />
                    Falar com vendas
                  </a>
                ) : (
                  <button
                    onClick={() => handleCheckout(plan as 'starter' | 'pro')}
                    disabled={!!checkoutLoading}
                    className={`w-full flex items-center justify-center gap-1.5 text-[12px] font-bold py-2 rounded-xl transition-all active:scale-95 disabled:opacity-60 ${
                      plan === 'pro'
                        ? 'bg-violet-500 hover:bg-violet-600 text-white'
                        : 'bg-[#0ABAB5] hover:bg-[#09a8a3] text-white'
                    }`}
                  >
                    {checkoutLoading === plan ? <SpinnerGap size={12} className="animate-spin" /> : <ArrowSquareOut size={12} weight="bold" />}
                    {checkoutLoading === plan ? '...' : 'Assinar'}
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Info */}
      <div className="bg-zinc-50 rounded-2xl border border-zinc-100 p-4 space-y-1.5">
        <p className="text-[12px] font-bold text-zinc-500">Pagamento seguro via Mercado Pago</p>
        <p className="text-[11px] text-zinc-400 leading-relaxed">
          Ao clicar em "Assinar" você será redirecionado para o Mercado Pago para completar o pagamento. Após a confirmação, seu plano será ativado automaticamente. Você pode cancelar a qualquer momento.
        </p>
      </div>
    </div>
  )
}

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

// ─── WhatsApp Tab ─────────────────────────────────────────────────────────────

function WhatsAppTab() {
  const qc = useQueryClient()
  const [creating, setCreating] = useState(false)
  const [newId, setNewId] = useState('')
  const [newName, setNewName] = useState('')

  const { data: instances = [], isLoading } = useQuery<AgentInstance[]>({
    queryKey: ['agent-instances'],
    queryFn: agentsApi.listInstances,
  })

  const createMut = useMutation({
    mutationFn: (data: { agent_id: string; name: string }) => agentsApi.createInstance(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agent-instances'] })
      setCreating(false)
      setNewId('')
      setNewName('')
      toast.success('Número adicionado')
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail ?? 'Erro ao criar instância'
      toast.error(typeof msg === 'string' ? msg : 'Erro ao criar instância')
    },
  })

  const activateMut = useMutation({
    mutationFn: (agent_id: string) => agentsApi.activateInstance(agent_id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agent-instances'] })
      toast.success('Agente ativado')
    },
  })

  const deleteMut = useMutation({
    mutationFn: (agent_id: string) => agentsApi.deleteInstance(agent_id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agent-instances'] })
      toast.success('Número removido')
    },
    onError: () => toast.error('Não é possível remover o número principal'),
  })

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 overflow-hidden">
        <div className="flex items-center justify-between p-4 md:p-5 border-b border-zinc-100">
          <div>
            <p className="text-[14px] font-bold text-[#1D1D1F]">Números WhatsApp</p>
            <p className="text-[12px] text-zinc-400 mt-0.5">Gerencie os agentes IA conectados à sua conta</p>
          </div>
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-1.5 text-[12px] font-bold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] px-3 py-2 rounded-xl transition-all active:scale-95"
          >
            <Plus size={13} weight="bold" />
            Adicionar
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <SpinnerGap size={20} className="animate-spin text-zinc-300" />
          </div>
        ) : (
          <div className="divide-y divide-zinc-50">
            {instances.map(inst => (
              <div key={inst.agent_id} className="flex items-center gap-3 px-4 md:px-5 py-3.5">
                <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
                  <WhatsappLogo size={18} weight="fill" className="text-emerald-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{inst.name}</p>
                    {inst.active && (
                      <span className="bg-[#0ABAB5]/10 text-[#0ABAB5] text-[10px] font-bold px-1.5 py-0.5 rounded-full">Ativo</span>
                    )}
                  </div>
                  <p className="text-[11px] text-zinc-400 font-mono">{inst.agent_id}</p>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  {!inst.active && (
                    <button
                      onClick={() => activateMut.mutate(inst.agent_id)}
                      disabled={activateMut.isPending}
                      className="text-[11px] font-semibold text-zinc-500 hover:text-[#0ABAB5] bg-zinc-100 hover:bg-zinc-200 px-2.5 py-1.5 rounded-lg transition-all"
                    >
                      Ativar
                    </button>
                  )}
                  <Link
                    to="/app/agents"
                    className="flex items-center justify-center w-7 h-7 rounded-lg text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 transition-all"
                    title="Configurar"
                  >
                    <Gear size={14} weight="bold" />
                  </Link>
                  {!inst.active && (
                    <button
                      onClick={() => {
                        if (confirm(`Remover o agente "${inst.name}"?`)) {
                          deleteMut.mutate(inst.agent_id)
                        }
                      }}
                      className="flex items-center justify-center w-7 h-7 rounded-lg text-zinc-400 hover:bg-red-50 hover:text-red-500 transition-all"
                      title="Remover"
                    >
                      <Prohibit size={14} weight="bold" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create new */}
      {creating && (
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5 space-y-4">
          <p className="text-[13px] font-bold text-[#1D1D1F]">Novo Número WhatsApp</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>ID do agente</label>
              <input type="text" value={newId} onChange={e => setNewId(e.target.value)} placeholder="ex: empresa-suporte" className={inputCls} />
              <p className="text-[10px] text-zinc-400 mt-1">Use letras minúsculas e hífens</p>
            </div>
            <div>
              <label className={labelCls}>Nome</label>
              <input type="text" value={newName} onChange={e => setNewName(e.target.value)} placeholder="ex: Suporte Comercial" className={inputCls} />
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setCreating(false)} className="text-[12px] font-semibold text-zinc-500 hover:text-zinc-700 px-3 py-2 rounded-xl hover:bg-zinc-100 transition-all">
              Cancelar
            </button>
            <button
              onClick={() => createMut.mutate({ agent_id: newId, name: newName })}
              disabled={!newId || !newName || createMut.isPending}
              className="flex items-center gap-1.5 text-[12px] font-bold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] px-4 py-2 rounded-xl transition-all active:scale-95 disabled:opacity-50"
            >
              {createMut.isPending ? <SpinnerGap size={12} className="animate-spin" /> : <Plus size={12} weight="bold" />}
              Criar
            </button>
          </div>
        </div>
      )}

      <div className="bg-zinc-50 rounded-2xl border border-zinc-100 p-4">
        <p className="text-[11px] text-zinc-400 leading-relaxed">
          Cada número WhatsApp corresponde a um agente IA com configuração independente. Para conectar um número, clique em <strong>Configurar</strong> e escaneie o QR code na aba WhatsApp do agente.
        </p>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>('perfil')

  const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'perfil',       label: 'Perfil',        icon: <User size={14} weight="duotone" />           },
    { key: 'empresa',      label: 'Empresa',       icon: <Buildings size={14} weight="duotone" />      },
    { key: 'equipe',       label: 'Equipe',        icon: <UsersThree size={14} weight="duotone" />     },
    { key: 'whatsapp',     label: 'WhatsApp',      icon: <WhatsappLogo size={14} weight="duotone" />   },
    { key: 'notificacoes', label: 'Notificações',  icon: <Bell size={14} weight="duotone" />           },
    { key: 'integracoes',  label: 'Integrações',   icon: <Plugs size={14} weight="duotone" />          },
    { key: 'assinatura',   label: 'Assinatura',    icon: <CreditCard size={14} weight="duotone" />     },
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
      {tab === 'empresa'      && <EmpresaTab />}
      {tab === 'equipe'       && <EquipeTab />}
      {tab === 'whatsapp'     && <WhatsAppTab />}
      {tab === 'notificacoes' && <NotificacoesTab />}
      {tab === 'integracoes'  && <IntegracoesTab />}
      {tab === 'assinatura'   && <AssinaturaTab />}
    </div>
  )
}

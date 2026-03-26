import { useState } from 'react'
import { FloppyDisk, CheckCircle, Camera, Buildings, Bell, User } from '@phosphor-icons/react'

type Tab = 'perfil' | 'empresa' | 'notificacoes'

interface NotifItem {
  id: string
  label: string
  description: string
  enabled: boolean
}

const INITIAL_NOTIFS: NotifItem[] = [
  { id: 'leads',     label: 'Novos Leads',          description: 'Receber notificação quando um novo lead for criado',     enabled: true  },
  { id: 'conv',      label: 'Conversas',             description: 'Alertas de novas mensagens',                            enabled: true  },
  { id: 'stock',     label: 'Estoque Baixo',         description: 'Avisos quando produto atingir nível mínimo',            enabled: true  },
  { id: 'contracts', label: 'Contratos Vencendo',    description: 'Lembretes 30 dias antes do vencimento',                 enabled: false },
  { id: 'report',    label: 'Relatório Semanal',     description: 'Resumo semanal por e-mail',                             enabled: false },
]

const inputCls = 'w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2.5 text-[13px] text-[#1D1D1F] focus:outline-none focus:border-[#0ABAB5]/50 focus:ring-2 focus:ring-[#0ABAB5]/10 transition-all'
const labelCls = 'block text-[12px] font-semibold text-zinc-500 mb-1.5'

function Toggle({ enabled, onToggle }: { enabled: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      role="switch"
      aria-checked={enabled}
      className={`relative w-10 h-6 rounded-full transition-colors cursor-pointer shrink-0 ${
        enabled ? 'bg-[#0ABAB5]' : 'bg-zinc-200'
      }`}
    >
      <span
        className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${
          enabled ? 'translate-x-4' : 'translate-x-0'
        }`}
      />
    </button>
  )
}

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>('perfil')
  const [notifs, setNotifs] = useState<NotifItem[]>(INITIAL_NOTIFS)
  const [saved, setSaved] = useState(false)

  function toggleNotif(id: string) {
    setNotifs(prev => prev.map(n => n.id === id ? { ...n, enabled: !n.enabled } : n))
  }

  function handleSave() {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'perfil',        label: 'Perfil',         icon: <User size={14} weight="duotone" />          },
    { key: 'empresa',       label: 'Empresa',        icon: <Buildings size={14} weight="duotone" />     },
    { key: 'notificacoes',  label: 'Notificações',   icon: <Bell size={14} weight="duotone" />          },
  ]

  return (
    <div className="p-4 md:p-6 space-y-5 pb-6">

      {/* Sticky header */}
      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100 flex items-center justify-between">
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight">Configurações</h1>
        <button
          onClick={handleSave}
          className={`flex items-center gap-2 text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95 ${
            saved ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-[#0ABAB5] hover:bg-[#09a8a3]'
          }`}
        >
          {saved ? <CheckCircle size={15} weight="fill" /> : <FloppyDisk size={15} weight="bold" />}
          {saved ? 'Salvo!' : 'Salvar'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-zinc-100/70 p-1 rounded-2xl">
        {TABS.map(({ key, label, icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex-1 flex items-center justify-center gap-1.5 text-[12px] font-semibold py-2 px-2 rounded-xl transition-all ${
              tab === key
                ? 'bg-white text-[#0ABAB5] shadow-sm'
                : 'text-zinc-500 hover:text-zinc-700'
            }`}
          >
            {icon}
            <span className="hidden sm:inline">{label}</span>
            <span className="sm:hidden">{label.split(' ')[0]}</span>
          </button>
        ))}
      </div>

      {/* Tab 1: Perfil */}
      {tab === 'perfil' && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6 space-y-5">

            {/* Avatar */}
            <div className="flex items-center gap-4">
              <div className="relative shrink-0">
                <div className="w-16 h-16 rounded-full bg-[#0ABAB5] flex items-center justify-center">
                  <span className="text-white text-xl font-bold tracking-wide">A</span>
                </div>
                <button className="absolute -bottom-1 -right-1 w-6 h-6 bg-white border border-zinc-200 rounded-full flex items-center justify-center shadow-sm hover:bg-zinc-50 transition-colors">
                  <Camera size={11} weight="bold" className="text-zinc-500" />
                </button>
              </div>
              <div>
                <p className="text-[14px] font-bold text-[#1D1D1F]">Admin</p>
                <button className="text-[12px] font-semibold text-[#0ABAB5] hover:underline mt-0.5">
                  Alterar foto
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Nome completo</label>
                <input type="text" defaultValue="Admin" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Cargo</label>
                <input type="text" defaultValue="Administrador" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>E-mail</label>
                <input type="email" defaultValue="admin@ops.com" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Telefone</label>
                <input type="tel" defaultValue="+55 11 99999-9999" className={inputCls} />
              </div>
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
                <input type="password" placeholder="••••••••" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Nova senha</label>
                <input type="password" placeholder="••••••••" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Confirmar nova senha</label>
                <input type="password" placeholder="••••••••" className={inputCls} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Empresa */}
      {tab === 'empresa' && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6 space-y-5">

            {/* Logo upload */}
            <div>
              <p className={labelCls}>Logo da Empresa</p>
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-xl border-2 border-dashed border-zinc-200 bg-zinc-50 flex items-center justify-center text-[#0ABAB5] font-bold text-lg">
                  OPS
                </div>
                <div>
                  <button className="text-[13px] font-semibold text-[#0ABAB5] border border-[#0ABAB5]/30 hover:bg-[#0ABAB5]/5 px-3 py-1.5 rounded-xl transition-colors">
                    Alterar logo
                  </button>
                  <p className="text-[11px] text-zinc-400 mt-1">PNG, JPG ou SVG até 2 MB</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Nome da Empresa</label>
                <input type="text" defaultValue="OPS Solutions" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Segmento</label>
                <input type="text" defaultValue="Energia Solar" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>CNPJ</label>
                <input type="text" defaultValue="00.000.000/0001-00" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Telefone</label>
                <input type="tel" defaultValue="+55 11 3000-0000" className={inputCls} />
              </div>
              <div className="sm:col-span-2">
                <label className={labelCls}>Site</label>
                <input type="url" defaultValue="https://opssolutions.com.br" className={inputCls} />
              </div>
            </div>
          </div>

          {/* Color picker */}
          <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6">
            <p className="text-[14px] font-bold text-[#1D1D1F] mb-4">Cores do Sistema</p>
            <div className="flex items-center justify-between gap-4 p-3 bg-zinc-50 rounded-xl border border-zinc-100">
              <div>
                <p className="text-[13px] font-semibold text-[#1D1D1F]">Cor primária</p>
                <p className="text-[11px] text-zinc-400 mt-0.5">Usada em botões, ícones e acentos</p>
              </div>
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-[#0ABAB5] border-2 border-white shadow-md ring-1 ring-zinc-200" />
                <span className="text-[12px] font-mono font-semibold text-zinc-500">#0ABAB5</span>
                <input
                  type="color"
                  defaultValue="#0ABAB5"
                  className="w-8 h-8 rounded-lg border border-zinc-200 cursor-pointer bg-transparent p-0.5"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Notificações */}
      {tab === 'notificacoes' && (
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
      )}
    </div>
  )
}

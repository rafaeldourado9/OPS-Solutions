import { NavLink } from 'react-router-dom'
import {
  SquaresFour, Users, Kanban, ChatCircleDots,
  Robot, Gear, SignOut, Question, X
} from '@phosphor-icons/react'
import { useAuthStore } from '../../store/authStore'

const ALL_NAV: { to: string; icon: React.ElementType; label: string }[] = [
  { to: '/app/dashboard',     icon: SquaresFour,   label: 'Dashboard'      },
  { to: '/app/customers',     icon: Users,         label: 'Clientes'        },
  { to: '/app/leads',         icon: Kanban,        label: 'Leads'           },
  { to: '/app/conversations', icon: ChatCircleDots,label: 'Conversas'       },
  { to: '/app/agents',        icon: Robot,         label: 'Agente IA'       },
  { to: '/app/settings',      icon: Gear,          label: 'Configurações'   },
]

interface SidebarProps {
  isOpen?: boolean
  onClose?: () => void
}

export default function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const logout = useAuthStore(s => s.logout)
  const tenant = useAuthStore(s => s.tenant)

  const nav = ALL_NAV

  return (
    <aside
      className={`
        fixed lg:relative top-0 left-0 h-full lg:h-auto z-50
        w-[260px] lg:w-60 shrink-0 flex flex-col min-h-screen
        transition-transform duration-300 ease-out lg:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}
      style={{
        background: 'rgba(255,255,255,0.92)',
        backdropFilter: 'blur(28px) saturate(1.8)',
        WebkitBackdropFilter: 'blur(28px) saturate(1.8)',
        borderRight: '1px solid rgba(0,0,0,0.06)',
      }}
    >
      {/* Logo + Mobile close */}
      <div className="px-5 py-[18px] border-b border-zinc-100/80 flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-xl bg-[#0ABAB5]/10 flex items-center justify-center shrink-0 overflow-hidden">
            <img src="/logoo.png" alt="Logo" className="w-6 h-6 object-contain" />
          </div>
          <div className="min-w-0">
            <p className="text-[13px] font-semibold text-[#1D1D1F] truncate leading-tight">OPS Solutions</p>
            <p className="text-[11px] text-zinc-400 truncate leading-tight mt-0.5">{tenant?.name ?? 'Carregando...'}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="lg:hidden flex items-center justify-center w-8 h-8 rounded-xl text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 transition-all ml-2 shrink-0"
        >
          <X size={16} weight="bold" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `relative flex items-center gap-3 px-3 py-[9px] rounded-xl text-[13px] font-medium transition-all duration-200 ease-out group ${
                isActive
                  ? 'bg-[#0ABAB5]/10 text-[#0ABAB5]'
                  : 'text-zinc-500 hover:bg-zinc-50/80 hover:text-[#1D1D1F]'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={`absolute left-0 top-1/2 -translate-y-1/2 w-[3px] rounded-r-full transition-all duration-300 ease-out ${
                    isActive ? 'h-5 bg-[#0ABAB5] opacity-100' : 'h-0 opacity-0'
                  }`}
                  style={isActive ? { boxShadow: '2px 0 8px rgba(10,186,181,0.4)' } : {}}
                />
                <span
                  className={`flex items-center justify-center w-[30px] h-[30px] rounded-lg transition-all duration-200 shrink-0 ${
                    isActive ? 'bg-[#0ABAB5]/15' : 'group-hover:bg-zinc-100'
                  }`}
                >
                  <Icon size={16} weight={isActive ? 'fill' : 'regular'} />
                </span>
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom actions */}
      <div className="px-3 py-3 border-t border-zinc-100/80 space-y-0.5">
        <p className="px-3 pb-1 text-[10px] text-zinc-300 select-none font-medium tracking-wide">v0.0.1</p>
        <a
          href="#"
          className="flex items-center gap-3 px-3 py-[9px] rounded-xl text-[13px] font-medium text-zinc-500 hover:bg-zinc-50/80 hover:text-[#1D1D1F] transition-all duration-200 group"
        >
          <span className="flex items-center justify-center w-[30px] h-[30px] rounded-lg group-hover:bg-zinc-100 transition-all duration-200 shrink-0">
            <Question size={16} />
          </span>
          Ajuda
        </a>
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-[9px] rounded-xl text-[13px] font-medium text-zinc-500 hover:bg-red-50/80 hover:text-red-500 transition-all duration-200 group"
        >
          <span className="flex items-center justify-center w-[30px] h-[30px] rounded-lg group-hover:bg-red-100/60 transition-all duration-200 shrink-0">
            <SignOut size={16} />
          </span>
          Sair
        </button>
      </div>
    </aside>
  )
}

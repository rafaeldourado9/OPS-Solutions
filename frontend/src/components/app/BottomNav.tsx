import { NavLink } from 'react-router-dom'
import { SquaresFour, Users, Kanban, ChatCircleDots, Robot } from '@phosphor-icons/react'

const BOTTOM_NAV = [
  { to: '/app/dashboard', icon: SquaresFour, label: 'Início' },
  { to: '/app/customers', icon: Users, label: 'Clientes' },
  { to: '/app/leads', icon: Kanban, label: 'Leads' },
  { to: '/app/conversations', icon: ChatCircleDots, label: 'Conversas' },
  { to: '/app/agents', icon: Robot, label: 'Agente' },
]

export default function BottomNav() {
  return (
    <nav
      className="lg:hidden fixed bottom-0 left-0 right-0 z-30 flex items-center justify-around px-2 h-16"
      style={{
        background: 'rgba(255,255,255,0.92)',
        backdropFilter: 'blur(24px) saturate(1.8)',
        WebkitBackdropFilter: 'blur(24px) saturate(1.8)',
        borderTop: '1px solid rgba(0,0,0,0.07)',
      }}
    >
      {BOTTOM_NAV.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            `flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-2xl transition-all duration-200 min-w-[56px] ${
              isActive
                ? 'text-[#0ABAB5]'
                : 'text-zinc-400'
            }`
          }
        >
          {({ isActive }) => (
            <>
              <span className={`flex items-center justify-center w-9 h-7 rounded-xl transition-all duration-200 ${isActive ? 'bg-[#0ABAB5]/12' : ''}`}>
                <Icon
                  size={20}
                  weight={isActive ? 'fill' : 'regular'}
                />
              </span>
              <span className={`text-[10px] font-semibold leading-none ${isActive ? 'text-[#0ABAB5]' : 'text-zinc-400'}`}>
                {label}
              </span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}

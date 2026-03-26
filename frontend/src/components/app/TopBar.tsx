import { useState } from 'react'
import { Bell, MagnifyingGlass, List, X } from '@phosphor-icons/react'
import { useAuthStore } from '../../store/authStore'

interface TopBarProps {
  onMenuClick?: () => void
}

export default function TopBar({ onMenuClick }: TopBarProps) {
  const user = useAuthStore(s => s.user)
  const initials = user?.name?.split(' ').map(n => n[0]).slice(0, 2).join('') ?? 'U'
  const [searchOpen, setSearchOpen] = useState(false)

  return (
    <header
      className="h-14 flex items-center gap-3 px-4 md:px-6 shrink-0"
      style={{
        background: 'rgba(249,250,251,0.88)',
        backdropFilter: 'blur(20px) saturate(1.6)',
        WebkitBackdropFilter: 'blur(20px) saturate(1.6)',
        borderBottom: '1px solid rgba(0,0,0,0.06)',
      }}
    >
      {/* Hamburger — mobile/tablet only */}
      <button
        onClick={onMenuClick}
        className="lg:hidden flex items-center justify-center w-9 h-9 rounded-xl text-zinc-500 hover:bg-white/80 hover:text-zinc-800 transition-all duration-200 shrink-0"
      >
        <List size={20} weight="bold" />
      </button>

      {/* Search — expands on mobile tap */}
      <div
        className={`flex items-center gap-2.5 flex-1 transition-all duration-200 ${
          searchOpen ? 'max-w-full' : 'max-w-xs md:max-w-sm'
        }`}
      >
        <div className="flex items-center gap-2.5 bg-white/70 border border-zinc-200/70 rounded-xl px-3 py-2 w-full shadow-[0_1px_4px_rgba(0,0,0,0.04)] transition-all duration-200 focus-within:border-[#0ABAB5]/50 focus-within:shadow-[0_0_0_3px_rgba(10,186,181,0.08)]">
          <MagnifyingGlass size={14} className="text-zinc-400 shrink-0" />
          <input
            type="text"
            placeholder="Buscar..."
            className="text-[13px] text-zinc-700 placeholder:text-zinc-400 bg-transparent focus:outline-none w-full"
            onFocus={() => setSearchOpen(true)}
            onBlur={() => setSearchOpen(false)}
          />
          {searchOpen && (
            <button
              className="shrink-0 text-zinc-400 hover:text-zinc-600 transition-colors"
              onMouseDown={e => { e.preventDefault(); setSearchOpen(false) }}
            >
              <X size={13} />
            </button>
          )}
        </div>
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-1.5 ml-auto">
        <button className="relative flex items-center justify-center w-9 h-9 rounded-xl hover:bg-white/80 transition-all duration-200 group">
          <Bell size={17} className="text-zinc-400 group-hover:text-zinc-600 transition-colors" />
          {/* Notification dot */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#0ABAB5] rounded-full border-2 border-white" />
        </button>

        <div className="flex items-center gap-2.5 pl-3 border-l border-zinc-200/60">
          <div
            className="w-8 h-8 rounded-full bg-[#0ABAB5] flex items-center justify-center text-white text-xs font-bold shadow-[0_2px_8px_rgba(10,186,181,0.3)] cursor-pointer"
          >
            {initials}
          </div>
          <div className="hidden md:block">
            <p className="text-[13px] font-semibold text-[#1D1D1F] leading-tight">{user?.name?.split(' ')[0]}</p>
            <p className="text-[11px] text-zinc-400 leading-tight capitalize">{user?.role}</p>
          </div>
        </div>
      </div>
    </header>
  )
}

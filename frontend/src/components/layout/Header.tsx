import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { List, X, Robot, ChartBar, ChatCircleDots, ArrowRight, Code, HardDrives, ArrowsClockwise, Storefront, House, Heartbeat, ForkKnife, Buildings } from '@phosphor-icons/react'

// ─── Dropdown content per nav item ────────────────────────────────────────────

function PlatformDropdown() {
  return (
    <div className="flex gap-6">
      {/* Mini CRM preview */}
      <div className="shrink-0 w-[200px]">
        <div className="bg-white rounded-xl border border-zinc-200 overflow-hidden shadow-sm">
          {/* Chrome */}
          <div className="flex items-center gap-1.5 px-3 py-2 bg-zinc-50 border-b border-zinc-100">
            <span className="w-2 h-2 rounded-full bg-[#FF5F57]/70" />
            <span className="w-2 h-2 rounded-full bg-[#FEBC2E]/70" />
            <span className="w-2 h-2 rounded-full bg-[#28C840]/70" />
            <span className="ml-2 text-[9px] text-zinc-400 font-mono truncate">OPS CRM</span>
          </div>
          {/* Dashboard mock */}
          <div className="flex h-28">
            <div className="w-8 bg-[#F9F9FB] border-r border-zinc-100 flex flex-col items-center py-2 gap-2">
              {[true, false, false, false].map((active, i) => (
                <div key={i} className={`w-5 h-5 rounded-lg ${active ? 'bg-[#0ABAB5]/20' : 'bg-zinc-100'}`} />
              ))}
            </div>
            <div className="flex-1 p-2 bg-white">
              <div className="grid grid-cols-2 gap-1 mb-2">
                {['R$87k', '143', '34%', '12'].map((v, i) => (
                  <div key={i} className="bg-zinc-50 rounded-lg p-1.5 border border-zinc-100">
                    <div className="text-[8px] text-zinc-400">metric</div>
                    <div className="text-[10px] font-bold text-zinc-700">{v}</div>
                  </div>
                ))}
              </div>
              <div className="flex gap-1">
                {['Novos', 'Proposta', 'Fechado'].map((col, i) => (
                  <div key={col} className="flex-1">
                    <div className={`text-[7px] font-bold px-1 py-0.5 rounded mb-1 ${i === 2 ? 'bg-[#0ABAB5]/10 text-[#0ABAB5]' : 'bg-zinc-100 text-zinc-500'}`}>{col}</div>
                    <div className="bg-white border border-zinc-100 rounded p-1 shadow-[0_1px_3px_rgba(0,0,0,0.06)]">
                      <div className="w-full h-1.5 bg-zinc-100 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        <p className="text-[10px] text-zinc-400 mt-2 text-center">CRM com dados reais</p>
      </div>

      {/* Feature list */}
      <div className="space-y-1 min-w-[180px]">
        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-3">Plataforma CRM</p>
        {[
          { icon: ChartBar, label: 'Dashboard & Analytics', href: '#planos' },
          { icon: ChatCircleDots, label: 'Conversas + Takeover', href: '#planos' },
          { icon: Robot, label: 'Agente IA no WhatsApp', href: '#agentes' },
          { icon: ChartBar, label: 'Pipeline Kanban', href: '#planos' },
          { icon: Code, label: 'Propostas & Contratos PDF', href: '#planos' },
        ].map(({ icon: Icon, label, href }) => (
          <a key={label} href={href}
            className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-zinc-50 transition-colors group cursor-pointer">
            <div className="w-6 h-6 rounded-lg bg-[#0ABAB5]/10 flex items-center justify-center shrink-0">
              <Icon size={11} weight="duotone" className="text-[#0ABAB5]" />
            </div>
            <span className="text-[12px] font-medium text-zinc-600 group-hover:text-[#1D1D1F] transition-colors">{label}</span>
          </a>
        ))}
        <div className="pt-2">
          <Link to="/auth/signup"
            className="flex items-center gap-1.5 text-[11px] font-bold text-[#0ABAB5] hover:gap-2.5 transition-all">
            Ver todos os recursos <ArrowRight size={11} weight="bold" />
          </Link>
        </div>
      </div>
    </div>
  )
}

function AgentsDropdown() {
  const niches = [
    { icon: Heartbeat, label: 'Clínicas & Saúde', color: 'text-rose-400 bg-rose-50' },
    { icon: House, label: 'Imobiliárias', color: 'text-amber-500 bg-amber-50' },
    { icon: Storefront, label: 'E-commerce', color: 'text-violet-500 bg-violet-50' },
    { icon: ForkKnife, label: 'Restaurantes', color: 'text-orange-500 bg-orange-50' },
  ]
  return (
    <div className="space-y-4 min-w-[280px]">
      <div className="bg-gradient-to-br from-[#0ABAB5]/10 to-transparent rounded-xl p-4 border border-[#0ABAB5]/10">
        <div className="flex items-baseline gap-1.5 mb-1">
          <span className="text-2xl font-black text-[#1D1D1F]">R$&nbsp;5,40</span>
          <span className="text-xs text-zinc-400 font-medium">/dia</span>
        </div>
        <p className="text-[11px] text-zinc-500">Agente IA personalizado para seu negócio — sem precisar do CRM</p>
        <a
          href="#agentes"
          className="mt-3 inline-flex items-center gap-1.5 text-[11px] font-bold text-[#0ABAB5] hover:gap-2 transition-all"
        >
          Ver catálogo de nichos <ArrowRight size={10} weight="bold" />
        </a>
      </div>

      <div>
        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2">Nichos disponíveis</p>
        <div className="grid grid-cols-2 gap-1.5">
          {niches.map(({ icon: Icon, label, color }) => (
            <a key={label} href="#agentes"
              className="flex items-center gap-2 px-2.5 py-2 rounded-lg bg-zinc-50 hover:bg-zinc-100 transition-colors cursor-pointer">
              <div className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 ${color}`}>
                <Icon size={12} weight="duotone" />
              </div>
              <span className="text-[11px] font-medium text-zinc-600 leading-tight">{label}</span>
            </a>
          ))}
        </div>
        <a href="#agentes" className="mt-2 block text-center text-[10px] text-zinc-400 hover:text-[#0ABAB5] transition-colors">
          + 4 outros nichos →
        </a>
      </div>
    </div>
  )
}

function DevDropdown() {
  const items = [
    { icon: Code, label: 'Aplicações Web & Mobile', sub: 'Sistemas sob medida' },
    { icon: HardDrives, label: 'Self-Hosted + Código-Fonte', sub: 'Você é dono' },
    { icon: ArrowsClockwise, label: 'Automações & Integrações', sub: 'RPA, pipelines' },
    { icon: Buildings, label: 'Marketplace de Devs', sub: 'Em breve' },
  ]
  return (
    <div className="min-w-[240px] space-y-1">
      <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-3">Fábrica de Software</p>
      {items.map(({ icon: Icon, label, sub }) => (
        <a key={label} href="#desenvolvedores"
          className="flex items-center gap-3 px-2 py-2 rounded-xl hover:bg-zinc-50 transition-colors group cursor-pointer">
          <div className="w-8 h-8 rounded-xl bg-zinc-100 group-hover:bg-[#0ABAB5]/10 flex items-center justify-center shrink-0 transition-colors">
            <Icon size={14} weight="duotone" className="text-zinc-500 group-hover:text-[#0ABAB5] transition-colors" />
          </div>
          <div>
            <p className="text-[12px] font-semibold text-zinc-700 leading-none mb-0.5">{label}</p>
            <p className="text-[10px] text-zinc-400">{sub}</p>
          </div>
        </a>
      ))}
    </div>
  )
}

// ─── Nav item with dropdown ────────────────────────────────────────────────────

type DropdownContent = 'platform' | 'agents' | 'dev' | null

function NavItem({
  label,
  href,
  dropdown,
  active,
  onEnter,
  onLeave,
}: {
  label: string
  href: string
  dropdown?: DropdownContent
  active: boolean
  onEnter: () => void
  onLeave: () => void
}) {
  return (
    <div className="relative" onMouseEnter={onEnter} onMouseLeave={onLeave}>
      <a
        href={href}
        className="relative px-3.5 py-2 text-[13px] font-medium text-zinc-600 hover:text-[#1D1D1F] rounded-lg transition-colors duration-200 group flex items-center gap-1"
      >
        {label}
        {dropdown && (
          <svg
            width="10" height="10" viewBox="0 0 10 10" fill="none"
            className={`transition-transform duration-200 ${active ? 'rotate-180' : ''} text-zinc-400`}
          >
            <path d="M2 3.5l3 3 3-3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" fill="none" />
          </svg>
        )}
        <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-0 group-hover:w-3.5 h-[1.5px] bg-[#0ABAB5] rounded-full transition-all duration-300 ease-out" />
      </a>

      {dropdown && active && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 pt-2 z-50">
          <div className="bg-white border border-zinc-200/80 rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.12),0_4px_16px_rgba(0,0,0,0.06)] p-4 animate-fade-down">
            {/* Arrow */}
            <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-l border-t border-zinc-200/80 rotate-45" />
            {dropdown === 'platform' && <PlatformDropdown />}
            {dropdown === 'agents'   && <AgentsDropdown />}
            {dropdown === 'dev'      && <DevDropdown />}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Main Header ──────────────────────────────────────────────────────────────

export default function Header() {
  const [scrolled, setScrolled] = useState(false)
  const [scrollProgress, setScrollProgress] = useState(0)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [activeDropdown, setActiveDropdown] = useState<DropdownContent>(null)
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 20)
      const docHeight = document.body.scrollHeight - window.innerHeight
      setScrollProgress(docHeight > 0 ? (window.scrollY / docHeight) * 100 : 0)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  function openDropdown(key: DropdownContent) {
    if (closeTimer.current) clearTimeout(closeTimer.current)
    setActiveDropdown(key)
  }

  function scheduleClose() {
    closeTimer.current = setTimeout(() => setActiveDropdown(null), 120)
  }

  const NAV: { label: string; href: string; dropdown?: DropdownContent }[] = [
    { label: 'Plataforma',      href: '#plataforma',    dropdown: 'platform' },
    { label: 'Agentes',         href: '#agentes',       dropdown: 'agents'   },
    { label: 'Desenvolvedores', href: '#desenvolvedores', dropdown: 'dev'    },
    { label: 'Planos',          href: '#planos'                               },
    { label: 'Recursos',        href: '#'                                     },
  ]

  return (
    <header
      className={`fixed top-0 w-full z-50 transition-all duration-500 ease-out ${
        scrolled
          ? 'bg-white/80 backdrop-blur-2xl shadow-[0_1px_0_rgba(0,0,0,0.06),0_4px_20px_rgba(0,0,0,0.04)]'
          : 'bg-transparent'
      }`}
    >
      {/* Scroll progress line */}
      <div
        className="absolute bottom-0 left-0 h-[1.5px] bg-gradient-to-r from-[#0ABAB5] to-[#06d4ce] transition-all duration-100 ease-out"
        style={{ width: `${scrollProgress}%`, opacity: scrolled ? 1 : 0 }}
      />

      <div className="max-w-7xl mx-auto px-6 lg:px-8 h-[52px] flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="flex items-center gap-2.5 shrink-0 group">
          <img
            src="/logoo.png"
            alt="Logo"
            className="w-7 h-7 object-contain transition-transform duration-300 group-hover:scale-110"
          />
          <span className="font-semibold text-[15px] tracking-tight text-[#1D1D1F]">
            OPS Solutions
          </span>
        </a>

        {/* Desktop nav */}
        <nav
          className="hidden md:flex items-center gap-0.5"
          onMouseLeave={scheduleClose}
        >
          {NAV.map(item => (
            <NavItem
              key={item.label}
              label={item.label}
              href={item.href}
              dropdown={item.dropdown}
              active={activeDropdown === (item.dropdown ?? null)}
              onEnter={() => item.dropdown ? openDropdown(item.dropdown) : setActiveDropdown(null)}
              onLeave={scheduleClose}
            />
          ))}
        </nav>

        {/* Right actions */}
        <div className="hidden md:flex items-center gap-2.5">
          <Link
            to="/auth/login"
            className="text-[13px] font-medium text-zinc-600 hover:text-[#1D1D1F] transition-colors px-3 py-2 rounded-lg hover:bg-zinc-50"
          >
            Entrar
          </Link>
          <Link
            to="/auth/signup"
            className="btn-liquid bg-[#0ABAB5] hover:bg-[#089B97] text-white text-[13px] font-semibold px-5 py-2 rounded-full"
          >
            Teste Grátis
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 rounded-xl hover:bg-zinc-100 transition-colors"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Menu"
        >
          {mobileOpen ? <X size={19} weight="bold" /> : <List size={19} weight="bold" />}
        </button>
      </div>

      {/* Mobile panel */}
      <div
        className={`md:hidden transition-all duration-300 ease-out overflow-hidden bg-white/95 backdrop-blur-2xl border-b border-zinc-100 ${
          mobileOpen ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-6 py-4 flex flex-col gap-1">
          {NAV.map(item => (
            <a
              key={item.label}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className="py-2.5 text-sm font-medium text-zinc-700 hover:text-[#0ABAB5] transition-colors"
            >
              {item.label}
            </a>
          ))}
          <div className="pt-3 border-t border-zinc-100 mt-2 flex flex-col gap-2">
            <Link to="/auth/login" className="text-sm font-medium text-zinc-600 py-2">Entrar</Link>
            <Link
              to="/auth/signup"
              className="bg-[#0ABAB5] text-white text-sm font-semibold px-5 py-3 rounded-full text-center"
            >
              Teste Grátis
            </Link>
          </div>
        </div>
      </div>
    </header>
  )
}

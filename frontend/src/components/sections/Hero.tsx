import { useRef, useState, useEffect } from 'react'
import { ArrowRight, PlayCircle } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'

export default function Hero() {
  const mockupRef = useRef<HTMLDivElement>(null)
  const sectionRef = useRef<HTMLElement>(null)
  const [tilt, setTilt] = useState({ x: -4, y: 2 })

  useEffect(() => {
    const handleMove = (e: MouseEvent) => {
      if (!sectionRef.current) return
      const rect = sectionRef.current.getBoundingClientRect()
      const cx = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2)
      const cy = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2)
      setTilt({ x: -4 + cx * 3, y: 2 - cy * 2.5 })
    }
    window.addEventListener('mousemove', handleMove, { passive: true })
    return () => window.removeEventListener('mousemove', handleMove)
  }, [])

  return (
    <section
      ref={sectionRef}
      className="mesh-bg min-h-[100dvh] flex flex-col justify-end pb-0 pt-16 overflow-hidden relative"
    >
      {/* Aurora orbs */}
      <div
        className="aurora-1 absolute top-[5%] right-[8%] w-[650px] h-[650px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(10,186,181,0.11) 0%, transparent 65%)', filter: 'blur(70px)' }}
      />
      <div
        className="aurora-2 absolute bottom-[15%] left-[-5%] w-[550px] h-[550px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(10,186,181,0.07) 0%, transparent 65%)', filter: 'blur(60px)' }}
      />
      <div
        className="aurora-3 absolute top-[45%] left-[28%] w-[380px] h-[380px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(6,214,208,0.05) 0%, transparent 70%)', filter: 'blur(50px)' }}
      />

      {/* Content container */}
      <div className="max-w-7xl mx-auto w-full px-6 lg:px-8 pb-20 md:pb-28 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-0 items-end">

          {/* Left — text block */}
          <div className="lg:pb-4">
            {/* Pill badge */}
            <div className="fade-in inline-flex items-center gap-2 glass border border-zinc-200/60 rounded-full px-4 py-1.5 mb-8 shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="ping-ring absolute inline-flex h-full w-full rounded-full bg-[#0ABAB5] opacity-50" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[#0ABAB5]" />
              </span>
              <span className="text-xs font-medium text-zinc-600 tracking-wide">Plataforma B2B — versão 2.0 disponível</span>
            </div>

            {/* Headline */}
            <h1
              className="fade-in text-5xl sm:text-6xl lg:text-[4.75rem] font-bold tracking-tighter leading-[1.0] text-[#1D1D1F] mb-6"
              style={{ transitionDelay: '0.1s' }}
            >
              Sua operação inteira.
              <br />
              <span className="text-gradient-teal">Uma única plataforma.</span>
            </h1>

            <p
              className="fade-in text-lg text-zinc-500 max-w-xl leading-relaxed mb-10"
              style={{ transitionDelay: '0.18s' }}
            >
              CRM inteligente, agentes de WhatsApp com IA e automações sob medida —
              tudo conectado, tudo seu.
            </p>

            {/* CTAs */}
            <div
              className="fade-in flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-5"
              style={{ transitionDelay: '0.26s' }}
            >
              <Link
                to="/auth/signup"
                className="btn-liquid group inline-flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#089B97] text-white font-semibold px-8 py-3.5 rounded-full"
              >
                Começar agora — é grátis
                <ArrowRight size={16} weight="bold" className="group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link
                to="/auth/signup?demo=true"
                className="inline-flex items-center gap-2 text-[#1D1D1F] font-semibold px-2 py-3.5 hover:text-[#0ABAB5] transition-colors group"
              >
                <PlayCircle size={20} weight="fill" className="text-zinc-400 group-hover:text-[#0ABAB5] transition-colors" />
                Ver demonstração
              </Link>
            </div>

            <p
              className="fade-in text-sm text-zinc-400"
              style={{ transitionDelay: '0.32s' }}
            >
              Sem cartão de crédito &bull; Setup em 5 minutos &bull; Cancele quando quiser
            </p>
          </div>

          {/* Right — Dashboard visual */}
          <div
            className="fade-in relative lg:translate-x-12"
            style={{ transitionDelay: '0.2s' }}
          >
            {/* Floating notification — glass */}
            <div
              className="float-slow absolute -top-6 left-4 z-10 glass rounded-2xl px-4 py-3 shadow-[0_12px_40px_rgba(0,0,0,0.1)] flex items-center gap-3"
            >
              <div className="w-9 h-9 bg-[#0ABAB5]/15 rounded-xl flex items-center justify-center shrink-0">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M9 1.5C4.86 1.5 1.5 4.86 1.5 9c0 1.32.345 2.565.945 3.645L1.5 16.5l3.855-.945A7.453 7.453 0 009 16.5c4.14 0 7.5-3.36 7.5-7.5S13.14 1.5 9 1.5z" fill="#0ABAB5" opacity=".2"/><path d="M9 1.5C4.86 1.5 1.5 4.86 1.5 9c0 1.32.345 2.565.945 3.645L1.5 16.5l3.855-.945A7.453 7.453 0 009 16.5c4.14 0 7.5-3.36 7.5-7.5S13.14 1.5 9 1.5z" stroke="#0ABAB5" strokeWidth="1.2" fill="none"/>
                </svg>
              </div>
              <div>
                <p className="text-xs font-semibold text-[#1D1D1F]">Novo lead qualificado</p>
                <p className="text-xs text-zinc-400">Beatriz Fontes — R$ 24.800</p>
              </div>
              <span className="w-2 h-2 bg-[#0ABAB5] rounded-full ml-1 shrink-0" style={{ boxShadow: '0 0 8px rgba(10,186,181,0.6)' }} />
            </div>

            {/* Ambient glow behind mockup */}
            <div
              className="absolute inset-0 -z-10 rounded-3xl"
              style={{
                background: 'radial-gradient(ellipse 80% 60% at 50% 60%, rgba(10,186,181,0.1) 0%, transparent 70%)',
                filter: 'blur(30px)',
                transform: 'scale(1.1)',
              }}
            />

            {/* Main dashboard mockup with parallax tilt */}
            <div
              ref={mockupRef}
              className="bg-white rounded-3xl shadow-[0_40px_100px_rgba(0,0,0,0.15),0_8px_24px_rgba(0,0,0,0.06)] border border-zinc-100/80 overflow-hidden"
              style={{
                transform: `perspective(1400px) rotateY(${tilt.x}deg) rotateX(${tilt.y}deg)`,
                transition: 'transform 0.2s ease-out',
                willChange: 'transform',
              }}
            >
              {/* Window chrome */}
              <div className="flex items-center gap-2 px-5 py-3.5 bg-zinc-50/80 border-b border-zinc-100/80 backdrop-blur-sm">
                <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
                <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
                <span className="w-3 h-3 rounded-full bg-[#28C840]" />
                <span className="ml-4 text-xs text-zinc-400 font-medium">OPS CRM — Dashboard</span>
              </div>

              {/* Sidebar + content */}
              <div className="flex h-[320px]">
                {/* Sidebar */}
                <div className="w-14 bg-[#F9F9FB] border-r border-zinc-100 flex flex-col items-center py-4 gap-4">
                  {([
                    <path key="a" d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" stroke="#0ABAB5" strokeWidth="1.5" fill="none"/>,
                    <><rect key="b1" x="3" y="3" width="7" height="7" rx="1" stroke="#999" strokeWidth="1.5" fill="none"/><rect key="b2" x="14" y="3" width="7" height="7" rx="1" stroke="#999" strokeWidth="1.5" fill="none"/><rect key="b3" x="3" y="14" width="7" height="7" rx="1" stroke="#999" strokeWidth="1.5" fill="none"/><rect key="b4" x="14" y="14" width="7" height="7" rx="1" stroke="#999" strokeWidth="1.5" fill="none"/></>,
                    <><circle key="c1" cx="12" cy="8" r="4" stroke="#999" strokeWidth="1.5" fill="none"/><path key="c2" d="M4 20v-2a4 4 0 014-4h8a4 4 0 014 4v2" stroke="#999" strokeWidth="1.5" fill="none"/></>,
                    <path key="d" d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke="#999" strokeWidth="1.5" fill="none"/>,
                  ] as React.ReactNode[]).map((icon, i) => (
                    <div key={i} className={`w-8 h-8 rounded-xl flex items-center justify-center ${i === 0 ? 'bg-[#0ABAB5]/12 shadow-sm' : 'hover:bg-zinc-200'} cursor-pointer transition-all`}>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none">{icon}</svg>
                    </div>
                  ))}
                </div>

                {/* Main content area */}
                <div className="flex-1 p-4 overflow-hidden bg-white">
                  {/* KPI row */}
                  <div className="grid grid-cols-3 gap-3 mb-4">
                    {[
                      { label: 'Leads ativos', val: '143', trend: '+12%', up: true },
                      { label: 'Receita mês', val: 'R$ 87k', trend: '+23%', up: true },
                      { label: 'Taxa conv.', val: '34,7%', trend: '-2%', up: false },
                    ].map(kpi => (
                      <div key={kpi.label} className="bg-zinc-50/80 rounded-xl p-3 border border-zinc-100/60">
                        <p className="text-xs text-zinc-400 mb-1">{kpi.label}</p>
                        <p className="text-base font-bold text-[#1D1D1F] leading-none">{kpi.val}</p>
                        <p className={`text-[10px] font-semibold mt-1 ${kpi.up ? 'text-emerald-500' : 'text-red-400'}`}>{kpi.trend}</p>
                      </div>
                    ))}
                  </div>

                  {/* Mini kanban */}
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { col: 'Novos', cards: ['Beatriz F.', 'Caio D.'], color: 'bg-zinc-100 text-zinc-500' },
                      { col: 'Proposta', cards: ['Rodrigo M.'], color: 'bg-amber-50 text-amber-600' },
                      { col: 'Fechado', cards: ['Lucas P.'], color: 'bg-[#0ABAB5]/10 text-[#089B97]' },
                    ].map(({ col, cards, color }) => (
                      <div key={col}>
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${color} mb-2 inline-block`}>{col}</span>
                        {cards.map(c => (
                          <div key={c} className="bg-white border border-zinc-100 rounded-lg p-2 mb-1.5 shadow-[0_1px_6px_rgba(0,0,0,0.05)]">
                            <p className="text-[11px] font-semibold text-[#1D1D1F]">{c}</p>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom floating metric — glass dark */}
            <div className="float-reverse absolute -bottom-5 right-6 glass-dark text-white rounded-2xl px-4 py-3 flex items-center gap-3">
              <div>
                <p className="text-xs text-zinc-400">Conversões hoje</p>
                <p className="text-lg font-bold tracking-tight">+R$ 12.400</p>
              </div>
              <div className="text-xs font-bold text-emerald-400 bg-emerald-400/15 px-2 py-0.5 rounded-full">+18%</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

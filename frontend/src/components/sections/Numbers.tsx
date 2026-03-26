import { useEffect, useRef, useState } from 'react'
import { TrendUp, Clock, Users, Lightning } from '@phosphor-icons/react'

const STATS = [
  { value: 500, prefix: '+', suffix: '', label: 'empresas atendidas', icon: Users, color: '#0ABAB5' },
  { value: 3, prefix: '', suffix: 'x', label: 'mais conversão com IA', icon: TrendUp, color: '#0ABAB5' },
  { value: 24, prefix: '', suffix: '/7', label: 'atendimento automatizado', icon: Clock, color: '#0ABAB5' },
  { value: 5, prefix: '<', suffix: 'min', label: 'tempo médio de setup', icon: Lightning, color: '#0ABAB5' },
]

function CountUp({ target, prefix, suffix }: { target: number; prefix: string; suffix: string }) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const started = useRef(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && !started.current) {
          started.current = true
          const duration = 1800
          const start = performance.now()
          const tick = (now: number) => {
            const p = Math.min((now - start) / duration, 1)
            const ease = 1 - Math.pow(1 - p, 3)
            setCount(Math.round(ease * target))
            if (p < 1) requestAnimationFrame(tick)
          }
          requestAnimationFrame(tick)
        }
      },
      { threshold: 0.5 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [target])

  return <div ref={ref} className="font-mono">{prefix}{count}{suffix}</div>
}

export default function Numbers() {
  return (
    <section className="bg-white py-28 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16 fade-in">
          <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-[0.2em] mb-4">Resultados</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-[#1D1D1F]">
            Números que falam por si.
          </h2>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-0 divide-x divide-y lg:divide-y-0 divide-zinc-100">
          {STATS.map(({ value, prefix, suffix, label, icon: Icon }, i) => (
            <div
              key={label}
              className="fade-in px-8 py-10 text-center group hover:bg-zinc-50/80 transition-colors"
              style={{ transitionDelay: `${i * 0.1}s` }}
            >
              <div className="w-10 h-10 rounded-2xl bg-[#0ABAB5]/10 flex items-center justify-center mx-auto mb-4 group-hover:bg-[#0ABAB5]/20 transition-colors">
                <Icon size={20} weight="duotone" className="text-[#0ABAB5]" />
              </div>
              <div className="text-5xl md:text-6xl font-bold text-[#1D1D1F] tracking-tighter mb-2">
                <CountUp target={value} prefix={prefix} suffix={suffix} />
              </div>
              <p className="text-sm text-zinc-500 leading-snug">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

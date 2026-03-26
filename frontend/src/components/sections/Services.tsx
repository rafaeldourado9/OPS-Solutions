import { Wrench, Code, ChartLineUp } from '@phosphor-icons/react'

const SERVICES = [
  {
    icon: Wrench,
    title: 'Automações Customizadas',
    desc: 'Fluxos inteligentes, integrações entre sistemas, RPAs e pipelines 100% automatizados para a sua realidade.',
    tag: 'Mais solicitado',
  },
  {
    icon: Code,
    title: 'Desenvolvimento de Software',
    desc: 'Sistemas web, aplicativos mobile e APIs robustas, construídos sob medida para a sua operação.',
    tag: null,
  },
  {
    icon: ChartLineUp,
    title: 'Consultoria Estratégica',
    desc: 'Análise da operação, roadmap técnico, priorização de entregas e acompanhamento na execução.',
    tag: null,
  },
]

export default function Services() {
  return (
    <section className="bg-[#111111] py-28 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="max-w-xl mb-14 fade-in">
          <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-[0.2em] mb-4">Serviços</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white leading-tight mb-5">
            Precisa de algo único?<br />
            <span className="text-zinc-500">A gente constrói.</span>
          </h2>
          <p className="text-lg text-zinc-400 leading-relaxed">
            Da consultoria à entrega. Automações, integrações e sistemas completos.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {SERVICES.map(({ icon: Icon, title, desc, tag }, i) => (
            <div
              key={title}
              className="fade-in spotlight-card bg-[#1A1A1E] rounded-2xl p-8 border border-[#242428] hover:border-[#0ABAB5]/35 transition-all duration-300 cursor-pointer group relative"
              style={{ transitionDelay: `${i * 0.12}s` }}
            >
              {/* content above spotlight overlay */}
              <div className="relative z-[1]">
                {tag && (
                  <span className="text-[10px] font-bold text-[#0ABAB5] bg-[#0ABAB5]/10 px-3 py-1 rounded-full mb-5 inline-block uppercase tracking-wider">
                    {tag}
                  </span>
                )}
                <div className="w-11 h-11 rounded-xl bg-[#0ABAB5]/15 flex items-center justify-center mb-6 group-hover:bg-[#0ABAB5]/25 transition-colors">
                  <Icon size={22} weight="duotone" className="text-[#0ABAB5]" />
                </div>
                <h3 className="font-semibold text-white text-lg mb-3">{title}</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">{desc}</p>
                <div className="mt-6 flex items-center gap-1.5 text-[#0ABAB5] text-sm font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  Saiba mais
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M3 7h8M8 4l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
                  </svg>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

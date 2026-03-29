import { ArrowRight, ChatCircleDots, Storefront, House, Heartbeat, ForkKnife, Barbell, PawPrint, Car, Briefcase, Sparkle } from '@phosphor-icons/react'

const NICHES = [
  {
    icon: Heartbeat,
    title: 'Clínicas & Consultórios',
    desc: 'Agendamento automático, confirmação de consultas, envio de lembretes e pré-triagem de sintomas via WhatsApp.',
    tags: ['Saúde', 'Agendamento'],
    color: 'from-rose-500/20 to-rose-500/5 border-rose-500/20',
    iconColor: 'text-rose-400',
  },
  {
    icon: House,
    title: 'Imobiliárias',
    desc: 'Captação de leads, envio de portfólio personalizado, qualificação de compradores e agendamento de visitas.',
    tags: ['Imóveis', 'Vendas'],
    color: 'from-amber-500/20 to-amber-500/5 border-amber-500/20',
    iconColor: 'text-amber-400',
  },
  {
    icon: Storefront,
    title: 'E-commerce & Lojas',
    desc: 'Consulta de estoque, rastreamento de pedidos, suporte pós-venda e recuperação de carrinho abandonado.',
    tags: ['Varejo', 'Suporte'],
    color: 'from-violet-500/20 to-violet-500/5 border-violet-500/20',
    iconColor: 'text-violet-400',
  },
  {
    icon: ForkKnife,
    title: 'Restaurantes & Delivery',
    desc: 'Cardápio interativo, recebimento de pedidos, confirmação de reservas e gestão de filas no WhatsApp.',
    tags: ['Alimentação', 'Pedidos'],
    color: 'from-orange-500/20 to-orange-500/5 border-orange-500/20',
    iconColor: 'text-orange-400',
  },
  {
    icon: Barbell,
    title: 'Academias & Personal',
    desc: 'Matrícula online, check-in via WhatsApp, envio de treinos e lembretes de pagamento automatizados.',
    tags: ['Fitness', 'Engajamento'],
    color: 'from-green-500/20 to-green-500/5 border-green-500/20',
    iconColor: 'text-green-400',
  },
  {
    icon: PawPrint,
    title: 'Pet Shops & Vet',
    desc: 'Agendamento de banho, tosa e consultas, envio de lembretes de vacina e follow-up pós-atendimento.',
    tags: ['PetCare', 'Fidelização'],
    color: 'from-pink-500/20 to-pink-500/5 border-pink-500/20',
    iconColor: 'text-pink-400',
  },
  {
    icon: Car,
    title: 'Oficinas & Serviços',
    desc: 'Orçamento automático, acompanhamento de serviço em tempo real, aviso de prontidão e cobrança via Pix.',
    tags: ['Automotivo', 'Serviços'],
    color: 'from-sky-500/20 to-sky-500/5 border-sky-500/20',
    iconColor: 'text-sky-400',
  },
  {
    icon: Briefcase,
    title: 'Escritórios & Consultorias',
    desc: 'Triagem de clientes, coleta de documentos, envio de propostas e lembretes de reunião — tudo automatizado.',
    tags: ['B2B', 'Produtividade'],
    color: 'from-teal-500/20 to-teal-500/5 border-teal-500/20',
    iconColor: 'text-[#0ABAB5]',
  },
]

export default function AgentCatalog() {
  return (
    <section className="bg-[#080808] py-28 px-6 overflow-hidden" id="agentes">
      <div className="max-w-7xl mx-auto">

        {/* Hero price hook */}
        <div className="text-center mb-16 fade-in">
          <div className="inline-flex items-center gap-2 bg-[#0ABAB5]/10 border border-[#0ABAB5]/20 rounded-full px-4 py-2 mb-6">
            <Sparkle size={13} weight="fill" className="text-[#0ABAB5]" />
            <span className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-wider">Agentes Prontos</span>
          </div>

          <h2 className="text-4xl md:text-6xl font-black tracking-tight text-white leading-none mb-5">
            A partir de{' '}
            <span className="relative">
              <span className="text-[#0ABAB5]">R$&nbsp;5,40</span>
              <span className="text-2xl md:text-3xl text-zinc-500 font-semibold">/dia</span>
            </span>
            <br />
            seu negócio no automático.
          </h2>
          <p className="text-lg text-zinc-400 max-w-2xl mx-auto leading-relaxed">
            Agentes de IA personalizados para o seu nicho — <strong className="text-white">sem precisar do CRM.</strong>{' '}
            Você contrata o agente, a gente configura, hospeda e entrega pronto para atender no WhatsApp.
          </p>

          {/* Price cards */}
          <div className="flex flex-wrap justify-center gap-4 mt-10 mb-2">
            {[
              { label: 'Agente Solo', price: 'R$162', period: '/mês', sub: '= R$5,40/dia', highlight: false },
              { label: 'Agente + CRM Starter', price: 'R$297', period: '/mês', sub: 'CRM completo incluso', highlight: true },
              { label: 'Agente + CRM Pro', price: 'R$497', period: '/mês', sub: 'Multi-agente + analytics', highlight: false },
            ].map(c => (
              <div
                key={c.label}
                className={`rounded-2xl px-6 py-4 text-center border transition-all ${
                  c.highlight
                    ? 'bg-[#0ABAB5] border-[#0ABAB5] shadow-[0_0_40px_rgba(10,186,181,0.3)]'
                    : 'bg-[#141414] border-[#242424]'
                }`}
              >
                <p className={`text-[11px] font-bold uppercase tracking-wider mb-1 ${c.highlight ? 'text-white/70' : 'text-zinc-500'}`}>
                  {c.label}
                </p>
                <div className="flex items-end justify-center gap-1">
                  <span className={`text-3xl font-black ${c.highlight ? 'text-white' : 'text-white'}`}>{c.price}</span>
                  <span className={`text-sm mb-1 ${c.highlight ? 'text-white/60' : 'text-zinc-500'}`}>{c.period}</span>
                </div>
                <p className={`text-[11px] font-semibold mt-0.5 ${c.highlight ? 'text-white/80' : 'text-[#0ABAB5]'}`}>{c.sub}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Niches grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          {NICHES.map(({ icon: Icon, title, desc, tags, color, iconColor }, i) => (
            <a
              href={`https://wa.me/5511947880561?text=${encodeURIComponent(`Olá! Quero saber mais sobre o agente para ${title}`)}`}
              target="_blank"
              rel="noopener noreferrer"
              key={title}
              className={`block fade-in group relative rounded-2xl p-5 border bg-gradient-to-br ${color} hover:scale-[1.02] transition-all duration-300 cursor-pointer`}
              style={{ transitionDelay: `${i * 0.05}s` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center`}>
                  <Icon size={20} weight="duotone" className={iconColor} />
                </div>
                <div className="flex flex-wrap gap-1 justify-end">
                  {tags.map(t => (
                    <span key={t} className="text-[9px] font-bold text-white/50 bg-white/5 px-2 py-0.5 rounded-full uppercase tracking-wide">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
              <h3 className="font-bold text-white text-[14px] mb-2 leading-snug">{title}</h3>
              <p className="text-[12px] text-zinc-400 leading-relaxed">{desc}</p>

              <div className="mt-4 flex items-center gap-1.5 text-[12px] font-semibold text-white/40 group-hover:text-white/70 transition-colors">
                Quero esse agente
                <ArrowRight size={11} weight="bold" className="group-hover:translate-x-0.5 transition-transform" />
              </div>
            </a>
          ))}

          {/* Custom niche CTA */}
          <div className="fade-in col-span-1 sm:col-span-2 lg:col-span-4 rounded-2xl p-6 border border-dashed border-[#0ABAB5]/30 bg-[#0ABAB5]/5 flex flex-col sm:flex-row items-center justify-between gap-5">
            <div>
              <p className="text-[#0ABAB5] text-xs font-bold uppercase tracking-wider mb-1">Seu nicho não está aqui?</p>
              <h3 className="text-white font-bold text-lg">Construímos um agente para qualquer negócio.</h3>
              <p className="text-zinc-400 text-sm mt-1">Conta como funciona a sua operação — a gente modela e entrega em até 5 dias úteis.</p>
            </div>
            <a
              href="https://wa.me/5511947880561?text=Quero+um+agente+personalizado+para+meu+negocio"
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#089B97] text-white font-bold text-sm px-6 py-3 rounded-full transition-all active:scale-95 shadow-[0_0_20px_rgba(10,186,181,0.3)]"
            >
              <ChatCircleDots size={15} weight="fill" />
              Falar no WhatsApp
            </a>
          </div>
        </div>

        {/* What's included */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 fade-in">
          {[
            { n: '5', label: 'dias úteis para entrega' },
            { n: '24/7', label: 'atendimento automático' },
            { n: '∞', label: 'mensagens por mês' },
            { n: '0', label: 'setup inicial cobrado' },
          ].map(({ n, label }) => (
            <div key={label} className="bg-[#111] border border-[#222] rounded-2xl p-5 text-center">
              <p className="text-3xl font-black text-[#0ABAB5] mb-1">{n}</p>
              <p className="text-[11px] text-zinc-500 leading-snug">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

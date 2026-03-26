const TESTIMONIALS = [
  {
    quote: 'O CRM da OPS transformou nosso processo de vendas. Em 90 dias, a taxa de conversão subiu 2,3x e o ciclo encurtou pela metade.',
    name: 'Marina Fonseca',
    role: 'Head de Vendas',
    company: 'Luminar Tech',
    initials: 'MF',
    color: '#7C3AED',
  },
  {
    quote: 'Os agentes de WhatsApp são absurdamente bons. Nossos clientes não percebem que estão falando com IA — e isso é exatamente o que queremos.',
    name: 'Rafael Drummond',
    role: 'CEO',
    company: 'LogisPrime',
    initials: 'RD',
    color: '#0891B2',
  },
  {
    quote: 'API limpa, documentação excelente e suporte que responde em minutos. Raridade no mercado. Já migramos toda a stack para a OPS.',
    name: 'Camila Arantes',
    role: 'CTO',
    company: 'DataFlow',
    initials: 'CA',
    color: '#059669',
  },
  {
    quote: 'Contratamos a consultoria e em 6 semanas 73% da nossa operação estava automatizada. O ROI foi imediato.',
    name: 'Pedro Cavalcante',
    role: 'COO',
    company: 'Nexus Retail',
    initials: 'PC',
    color: '#D97706',
  },
]

export default function Testimonials() {
  return (
    <section className="bg-[#F5F5F7] py-28 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16 fade-in">
          <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-[0.2em] mb-4">Depoimentos</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-[#1D1D1F]">
            Quem usa, recomenda.
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {TESTIMONIALS.map((t, i) => (
            <div
              key={t.name}
              className="fade-in bg-white rounded-3xl p-8 shadow-[0_2px_24px_rgba(0,0,0,0.05)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.09)] transition-all duration-300"
              style={{ transitionDelay: `${i * 0.1}s` }}
            >
              {/* Quote mark */}
              <svg width="32" height="24" viewBox="0 0 32 24" fill="none" className="mb-5 opacity-20">
                <path d="M0 24V14.4C0 6.4 4.667 1.067 14 0l1.4 2.8C10.333 4 7.733 7.067 7.2 12H14V24H0zm18 0V14.4C18 6.4 22.667 1.067 32 0l1.4 2.8C28.333 4 25.733 7.067 25.2 12H32V24H18z" fill="#0ABAB5"/>
              </svg>

              <p className="text-[#1D1D1F] leading-relaxed text-[15px] mb-6">{t.quote}</p>

              <div className="flex items-center gap-3 pt-5 border-t border-zinc-100">
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
                  style={{ background: t.color }}
                >
                  {t.initials}
                </div>
                <div>
                  <p className="font-semibold text-sm text-[#1D1D1F]">{t.name}</p>
                  <p className="text-xs text-zinc-400">{t.role}, {t.company}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

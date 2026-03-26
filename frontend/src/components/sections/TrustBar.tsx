const METRICS = [
  { value: '+6.000', label: 'clientes ativos' },
  { value: '+1,5bi', label: 'mensagens processadas' },
  { value: '99,97%', label: 'uptime em 2025' },
  { value: '<5min', label: 'tempo de setup' },
]

const BRANDS = ['VortexTech', 'PulseCorp', 'NovaBuild', 'ClearMind', 'FluxLayer', 'AxisCore', 'ZenithCloud', 'DataFlow']

export default function TrustBar() {
  return (
    <section className="bg-zinc-950 py-14 px-6 overflow-hidden">
      {/* Metrics */}
      <div className="max-w-7xl mx-auto mb-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 border-b border-zinc-800 pb-10">
          {METRICS.map((m, i) => (
            <div key={i} className="fade-in text-center" style={{ transitionDelay: `${i * 0.08}s` }}>
              <p className="text-3xl font-bold text-white tracking-tight font-mono">{m.value}</p>
              <p className="text-xs text-zinc-500 mt-1 tracking-wide uppercase">{m.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Marquee logos */}
      <div className="overflow-hidden" aria-hidden="true">
        <p className="text-center text-xs text-zinc-600 uppercase tracking-widest mb-6">Confiado por líderes de mercado</p>
        <div className="flex overflow-hidden">
          <div className="marquee-track gap-16 items-center">
            {[...BRANDS, ...BRANDS].map((name, i) => (
              <div key={i} className="flex items-center gap-2 opacity-30 hover:opacity-60 transition-opacity shrink-0">
                <div className="w-6 h-6 rounded bg-zinc-600" />
                <span className="text-sm font-semibold text-zinc-400 whitespace-nowrap">{name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

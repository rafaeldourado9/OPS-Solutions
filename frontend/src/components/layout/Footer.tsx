export default function Footer() {
  const cols = [
    {
      title: 'Plataforma',
      links: ['CRM', 'Automações', 'Integrações', 'Analytics', 'API'],
    },
    {
      title: 'Produtos',
      links: ['Agentes WhatsApp', 'Licenças', 'Factory Software', 'SDKs'],
    },
    {
      title: 'Desenvolvedores',
      links: ['API Reference', 'SDKs', 'Documentação', 'Status', 'Changelog'],
    },
    {
      title: 'Empresa',
      links: ['Sobre', 'Blog', 'Carreiras', 'Contato', 'Parceiros'],
    },
  ]

  return (
    <footer className="bg-[#0A0A0A] pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 lg:gap-12">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
                <polygon points="16,2 28,9 28,23 16,30 4,23 4,9" stroke="#0ABAB5" strokeWidth="2" fill="none"/>
                <circle cx="16" cy="16" r="3" fill="#0ABAB5"/>
                <line x1="16" y1="13" x2="16" y2="5" stroke="#0ABAB5" strokeWidth="1.5"/>
                <line x1="18.6" y1="14.5" x2="25.4" y2="10.5" stroke="#0ABAB5" strokeWidth="1.5"/>
                <line x1="18.6" y1="17.5" x2="25.4" y2="21.5" stroke="#0ABAB5" strokeWidth="1.5"/>
                <circle cx="16" cy="4.5" r="1.5" fill="#0ABAB5"/>
                <circle cx="26.5" cy="10.5" r="1.5" fill="#0ABAB5"/>
                <circle cx="26.5" cy="21.5" r="1.5" fill="#0ABAB5"/>
              </svg>
              <span className="font-semibold text-white text-sm">OPS Solutions</span>
            </div>
            <p className="text-sm text-[#555] leading-relaxed max-w-[180px]">
              Plataforma unificada para operações inteligentes.
            </p>
          </div>

          {cols.map(col => (
            <div key={col.title}>
              <h4 className="text-xs font-semibold text-white uppercase tracking-widest mb-4">{col.title}</h4>
              <ul className="space-y-3">
                {col.links.map(link => (
                  <li key={link}>
                    <a href="#" className="text-sm text-[#666] hover:text-white transition-colors">{link}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-[#1E1E1E] mt-12 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-[#444]">© 2026 OPS Solutions. Todos os direitos reservados.</p>
          <div className="flex items-center gap-6">
            <span className="text-sm text-[#444]">Português (BR)</span>
            <div className="flex items-center gap-4">
              {['LinkedIn', 'Instagram', 'GitHub'].map(s => (
                <a key={s} href="#" className="text-sm text-[#444] hover:text-white transition-colors">{s}</a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

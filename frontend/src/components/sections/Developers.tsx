import { ArrowRight, Code, Robot, ArrowsClockwise, GitFork, Database, HardDrives, FileCode, TreeStructure, Users, CurrencyDollar, Package } from '@phosphor-icons/react'

const PRODUCTS = [
  {
    icon: Code,
    title: 'Aplicações Web & Mobile',
    desc: 'Sistemas sob medida, SaaS, painéis internos, B2B e apps nativos. Da concepção ao deploy.',
    tag: 'Produto',
    accent: 'text-[#0ABAB5]',
    bg: 'bg-[#0ABAB5]/10',
  },
  {
    icon: HardDrives,
    title: 'Self-Hosted & Código-Fonte',
    desc: 'Você compra a aplicação e a hospeda onde quiser. Inclui código-fonte, documentação técnica e onboarding.',
    tag: 'Propriedade sua',
    accent: 'text-violet-400',
    bg: 'bg-violet-500/10',
  },
  {
    icon: Robot,
    title: 'Agentes IA Customizados',
    desc: 'WhatsApp, Instagram, web chat. Qualquer canal, qualquer nicho, com RAG e memória persistente.',
    tag: 'IA + WhatsApp',
    accent: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
  },
  {
    icon: Database,
    title: 'IA Local com Ollama',
    desc: 'Rodamos modelos LLM na infraestrutura do cliente. Calculamos o custo da VPS, embutimos no orçamento — zero token por mensagem.',
    tag: 'On-Premise',
    accent: 'text-amber-400',
    bg: 'bg-amber-500/10',
  },
  {
    icon: ArrowsClockwise,
    title: 'Automações & Integrações',
    desc: 'Eliminamos trabalho manual. Notificações, pipelines de dados, RPA, integrações entre sistemas legados e modernos.',
    tag: 'Automação',
    accent: 'text-sky-400',
    bg: 'bg-sky-500/10',
  },
  {
    icon: FileCode,
    title: 'APIs Sob Medida',
    desc: 'REST e GraphQL com tipagem completa, documentação automática e SDKs prontos. Do MVP à escala de produção.',
    tag: 'Backend',
    accent: 'text-pink-400',
    bg: 'bg-pink-500/10',
  },
  {
    icon: GitFork,
    title: 'Refatoração & Modernização',
    desc: 'Transformamos código legado em sistemas modernos, testáveis e escaláveis sem parar sua operação.',
    tag: 'Qualidade',
    accent: 'text-orange-400',
    bg: 'bg-orange-500/10',
  },
  {
    icon: Package,
    title: 'Venda de Automações Prontas',
    desc: 'Catálogo de automações e scripts prontos para compra direta — ativação imediata, sem hora de desenvolvimento.',
    tag: 'Pronto para usar',
    accent: 'text-teal-400',
    bg: 'bg-teal-500/10',
  },
]

export default function Developers() {
  return (
    <section className="bg-[#0A0A0A] py-28 px-6" id="desenvolvedores">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-8 mb-16 fade-in">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-[0.2em] mb-4">Fábrica de Software</p>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white leading-tight mb-5">
              Além do CRM,<br />
              <span className="text-[#0ABAB5]">somos uma fábrica.</span>
            </h2>
            <p className="text-lg text-zinc-400 leading-relaxed">
              Aplicações, agentes, automações, APIs, código-fonte, IA local — construímos e vendemos tudo que envolve tecnologia.
              Você escolhe se quer o produto <strong className="text-white">hospedado por nós</strong> ou <strong className="text-white">na sua própria infraestrutura.</strong>
            </p>
          </div>

          {/* Self-hosted callout */}
          <div className="shrink-0 bg-[#141414] border border-[#2a2a2a] rounded-2xl p-6 max-w-xs w-full">
            <div className="flex items-center gap-2 mb-3">
              <HardDrives size={16} weight="duotone" className="text-violet-400" />
              <p className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Self-Hosted</p>
            </div>
            <p className="text-white font-bold text-[15px] mb-2 leading-snug">
              Quer ser dono do código?
            </p>
            <p className="text-zinc-500 text-sm leading-relaxed mb-4">
              Comprando a versão self-hosted, você recebe o código-fonte completo, documentação e pode hospedar onde quiser.
            </p>
            <a
              href="https://wa.me/5511947880561?text=Quero+saber+sobre+a+versao+self-hosted"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-violet-400 font-semibold text-sm hover:gap-3 transition-all group"
            >
              Perguntar sobre preço
              <ArrowRight size={13} weight="bold" className="group-hover:translate-x-0.5 transition-transform" />
            </a>
          </div>
        </div>

        {/* Products grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          {PRODUCTS.map(({ icon: Icon, title, desc, tag, accent, bg }, i) => (
            <div
              key={title}
              className="fade-in group relative bg-[#141414] border border-[#242424] rounded-2xl p-5 hover:border-[#0ABAB5]/30 hover:bg-[#161616] transition-all duration-300"
              style={{ transitionDelay: `${i * 0.05}s` }}
            >
              <span className={`inline-block text-[10px] font-bold ${accent} bg-white/5 px-2.5 py-1 rounded-full mb-4 uppercase tracking-wide`}>
                {tag}
              </span>
              <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                <Icon size={20} weight="duotone" className={accent} />
              </div>
              <h3 className="font-bold text-white mb-2 text-[14px] leading-snug">{title}</h3>
              <p className="text-[12px] text-zinc-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        {/* Marketplace teaser */}
        <div className="fade-in relative overflow-hidden bg-gradient-to-br from-[#0ABAB5]/10 via-[#141414] to-violet-900/10 border border-[#0ABAB5]/20 rounded-2xl p-8">
          {/* Background decoration */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-[#0ABAB5]/5 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-1/2 w-48 h-48 bg-violet-500/5 rounded-full blur-3xl pointer-events-none" />

          <div className="relative flex flex-col lg:flex-row lg:items-center gap-8">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-[10px] font-black text-amber-400 bg-amber-400/10 border border-amber-400/20 px-3 py-1 rounded-full uppercase tracking-widest">
                  Em Breve
                </span>
                <span className="text-[10px] text-zinc-500 font-semibold uppercase tracking-wider">Marketplace de Devs Parceiros</span>
              </div>
              <h3 className="text-white font-bold text-2xl md:text-3xl leading-tight mb-3">
                Conectamos empresas<br />
                <span className="text-[#0ABAB5]">a devs especializados.</span>
              </h3>
              <p className="text-zinc-400 leading-relaxed max-w-xl">
                Cadastre-se como dev parceiro, receba projetos qualificados via nosso agente IA e defina seu próprio preço dentro da margem sugerida pela plataforma.
                Você constrói, a gente distribui.
              </p>
            </div>

            <div className="shrink-0 space-y-3 min-w-[260px]">
              {/* Example negotiation card */}
              <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <TreeStructure size={14} className="text-[#0ABAB5]" />
                  <p className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider">Tabela de Serviços</p>
                </div>
                {[
                  { service: 'Landing Page', cost: 'R$150', suggested: 'R$255' },
                  { service: 'Agente IA Solo', cost: 'R$200', suggested: 'R$360' },
                  { service: 'API REST básica', cost: 'R$300', suggested: 'R$510' },
                ].map(row => (
                  <div key={row.service} className="flex items-center justify-between py-1.5 border-b border-[#242424] last:border-0">
                    <span className="text-[12px] text-zinc-300">{row.service}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] text-zinc-600 line-through">{row.cost}</span>
                      <span className="text-[12px] font-bold text-[#0ABAB5]">{row.suggested}</span>
                    </div>
                  </div>
                ))}
                <div className="mt-3 flex items-center gap-1.5">
                  <CurrencyDollar size={12} className="text-emerald-400" />
                  <p className="text-[10px] text-emerald-400 font-semibold">Você fica com o spread — ~70%</p>
                </div>
              </div>

              <div className="flex items-center gap-2 px-4 py-3 bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl">
                <Users size={14} className="text-violet-400 shrink-0" />
                <p className="text-[11px] text-zinc-400">
                  <strong className="text-white">Devs parceiros</strong> recebem leads qualificados via nosso agente monitorado
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Code snippet */}
        <div className="fade-in mt-8 max-w-2xl">
          <div className="bg-[#141414] border border-[#242424] rounded-2xl overflow-hidden">
            <div className="flex items-center gap-2 px-5 py-3 bg-[#0D0D0D] border-b border-[#242424]">
              <span className="w-2.5 h-2.5 rounded-full bg-[#FF5F57]/70" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#FEBC2E]/70" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#28C840]/70" />
              <span className="ml-3 text-xs text-zinc-600 font-mono">agente-ia.py</span>
              <span className="ml-auto text-[10px] text-[#0ABAB5] font-semibold">Self-hosted com Ollama</span>
            </div>
            <pre className="p-5 text-[13px] font-mono leading-6 overflow-x-auto">
              <code>
                <span className="text-zinc-500"># IA local: zero custo por token, dados na sua VPS{'\n'}</span>
                <span className="text-purple-400">from </span>
                <span className="text-blue-300">ops_sdk </span>
                <span className="text-purple-400">import </span>
                <span className="text-zinc-300">Agent, OllamaBackend{'\n\n'}</span>
                <span className="text-blue-300">agent </span>
                <span className="text-zinc-300">= </span>
                <span className="text-yellow-300">Agent</span>
                <span className="text-zinc-300">({'\n  '}</span>
                <span className="text-blue-300">name</span>
                <span className="text-zinc-300">=</span>
                <span className="text-green-400">"Assistente Vendas"</span>
                <span className="text-zinc-300">{',\n  '}</span>
                <span className="text-blue-300">llm</span>
                <span className="text-zinc-300">=</span>
                <span className="text-yellow-300">OllamaBackend</span>
                <span className="text-zinc-300">(</span>
                <span className="text-blue-300">model</span>
                <span className="text-zinc-300">=</span>
                <span className="text-green-400">"llama3.2"</span>
                <span className="text-zinc-300">),{'\n  '}</span>
                <span className="text-blue-300">host</span>
                <span className="text-zinc-300">=</span>
                <span className="text-green-400">"sua-vps.com.br"</span>
                <span className="text-zinc-300">{',\n  '}</span>
                <span className="text-zinc-500"># VPS inclusa no orçamento — você é dono{'\n  '}</span>
                <span className="text-zinc-300">)</span>
              </code>
            </pre>
          </div>
        </div>

      </div>
    </section>
  )
}

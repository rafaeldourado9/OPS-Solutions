import { ArrowRight, Code, Robot, ArrowsClockwise, Buildings, GitFork, MagnifyingGlass, CheckSquare } from '@phosphor-icons/react'

const SERVICES = [
  {
    icon: Code,
    title: 'APIs Sob Medida',
    desc: 'REST e GraphQL construídas para o seu caso de uso específico. Tipagem completa, documentação automática, SDKs prontos.',
    tag: 'Backend',
  },
  {
    icon: Robot,
    title: 'Agentes WhatsApp Customizados',
    desc: 'Agentes de IA conversacional para qualquer nicho — sem precisar do CRM. Suporte ao cliente, vendas, cobrança, RH.',
    tag: 'IA + WhatsApp',
  },
  {
    icon: ArrowsClockwise,
    title: 'Automações de Processos',
    desc: 'Eliminamos tarefas manuais com automações inteligentes. Notificações, integrações, pipelines de dados e mais.',
    tag: 'Automação',
  },
  {
    icon: Buildings,
    title: 'Softwares Enterprise Sob Medida',
    desc: 'Da concepção ao deploy. ERPs, plataformas B2B, painéis internos e sistemas complexos com arquitetura robusta.',
    tag: 'Enterprise',
  },
  {
    icon: GitFork,
    title: 'Refatoração',
    desc: 'Transformamos código legado em sistemas modernos, testáveis e escaláveis — sem parar sua operação.',
    tag: 'Qualidade',
  },
  {
    icon: MagnifyingGlass,
    title: 'Levantamento de Requisitos',
    desc: 'Mapeamos seu processo de ponta a ponta, definimos escopo técnico e entregamos documentação completa antes de uma linha de código.',
    tag: 'Consultoria',
  },
  {
    icon: CheckSquare,
    title: 'Code Review',
    desc: 'Auditoria detalhada do seu código — segurança, performance, boas práticas e débito técnico. Relatório acionável.',
    tag: 'Auditoria',
  },
]

export default function Developers() {
  return (
    <section className="bg-[#0A0A0A] py-28 px-6" id="desenvolvedores">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="max-w-2xl mb-16 fade-in">
          <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-[0.2em] mb-4">Factory de Software</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white leading-tight mb-5">
            Especialistas em IA,<br />
            <span className="text-[#0ABAB5]">automação e software.</span>
          </h2>
          <p className="text-lg text-zinc-400 leading-relaxed">
            Da ideia ao produto final. Construímos soluções digitais sob medida para empresas que precisam de tecnologia de alto nível sem montar um time interno.
          </p>
        </div>

        {/* Services grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-12">
          {SERVICES.map(({ icon: Icon, title, desc, tag }, i) => (
            <div
              key={title}
              className="fade-in group relative bg-[#141414] border border-[#242424] rounded-2xl p-6 hover:border-[#0ABAB5]/40 hover:bg-[#141414] transition-all duration-300 cursor-pointer"
              style={{ transitionDelay: `${i * 0.06}s` }}
            >
              {/* Tag */}
              <span className="inline-block text-[10px] font-semibold text-[#0ABAB5] bg-[#0ABAB5]/10 px-2.5 py-1 rounded-full mb-4 uppercase tracking-wide">
                {tag}
              </span>

              {/* Icon */}
              <div className="w-10 h-10 rounded-xl bg-[#0ABAB5]/10 flex items-center justify-center mb-4 group-hover:bg-[#0ABAB5]/20 transition-colors">
                <Icon size={20} weight="duotone" className="text-[#0ABAB5]" />
              </div>

              <h3 className="font-semibold text-white mb-2 text-[15px]">{title}</h3>
              <p className="text-sm text-zinc-500 leading-relaxed">{desc}</p>
            </div>
          ))}

          {/* CTA card */}
          <div className="fade-in bg-gradient-to-br from-[#0ABAB5]/20 to-[#0ABAB5]/5 border border-[#0ABAB5]/30 rounded-2xl p-6 flex flex-col justify-between"
            style={{ transitionDelay: `${SERVICES.length * 0.06}s` }}
          >
            <div>
              <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-wide mb-3">Tem um projeto?</p>
              <h3 className="font-bold text-white text-lg leading-snug mb-3">
                Vamos conversar sobre o que você precisa.
              </h3>
              <p className="text-sm text-zinc-400">
                Sem compromisso. Você explica o desafio e a gente diz se consegue resolver.
              </p>
            </div>
            <a
              href="https://wa.me/5511947880561"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-6 inline-flex items-center gap-2 text-[#0ABAB5] font-semibold text-sm hover:gap-3 transition-all group"
            >
              Falar com a equipe
              <ArrowRight size={14} weight="bold" className="group-hover:translate-x-0.5 transition-transform" />
            </a>
          </div>
        </div>

        {/* Code snippet — keeping developer credibility */}
        <div className="fade-in max-w-2xl" style={{ transitionDelay: '0.5s' }}>
          <div className="bg-[#141414] border border-[#242424] rounded-2xl overflow-hidden">
            <div className="flex items-center gap-2 px-5 py-3 bg-[#0D0D0D] border-b border-[#242424]">
              <span className="w-2.5 h-2.5 rounded-full bg-[#FF5F57]/70" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#FEBC2E]/70" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#28C840]/70" />
              <span className="ml-3 text-xs text-zinc-600 font-mono">agente-ia.py</span>
              <span className="ml-auto text-[10px] text-[#0ABAB5] font-semibold">Agente WhatsApp com RAG</span>
            </div>
            <pre className="p-5 text-[13px] font-mono leading-6 overflow-x-auto">
              <code>
                <span className="text-zinc-500"># Criar agente customizado com base de conhecimento RAG{'\n'}</span>
                <span className="text-purple-400">from </span>
                <span className="text-blue-300">ops_sdk </span>
                <span className="text-purple-400">import </span>
                <span className="text-zinc-300">Agent, RAGStore{'\n\n'}</span>
                <span className="text-blue-300">agent </span>
                <span className="text-zinc-300">= </span>
                <span className="text-yellow-300">Agent</span>
                <span className="text-zinc-300">({'\n  '}</span>
                <span className="text-blue-300">name</span>
                <span className="text-zinc-300">=</span>
                <span className="text-green-400">"Assistente Vendas"</span>
                <span className="text-zinc-300">{',\n  '}</span>
                <span className="text-blue-300">rag</span>
                <span className="text-zinc-300">=</span>
                <span className="text-yellow-300">RAGStore</span>
                <span className="text-zinc-300">.</span>
                <span className="text-yellow-300">from_docs</span>
                <span className="text-zinc-300">([</span>
                <span className="text-green-400">"catalogo.pdf"</span>
                <span className="text-zinc-300">, </span>
                <span className="text-green-400">"faq.txt"</span>
                <span className="text-zinc-300">]),{'\n  '}</span>
                <span className="text-blue-300">persona</span>
                <span className="text-zinc-300">=</span>
                <span className="text-green-400">"Especialista em energia solar"</span>
                <span className="text-zinc-300">{'\n})\n\n'}</span>
                <span className="text-zinc-500"># Responde clientes no WhatsApp 24/7 com contexto da sua empresa{'\n'}</span>
                <span className="text-purple-400">await </span>
                <span className="text-blue-300">agent</span>
                <span className="text-zinc-300">.</span>
                <span className="text-yellow-300">deploy</span>
                <span className="text-zinc-300">(</span>
                <span className="text-blue-300">phone</span>
                <span className="text-zinc-300">=</span>
                <span className="text-green-400">"+55 11 9XXXX-XXXX"</span>
                <span className="text-zinc-300">)</span>
              </code>
            </pre>
          </div>
        </div>
      </div>
    </section>
  )
}

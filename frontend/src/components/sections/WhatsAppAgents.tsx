import { Robot, Brain, ArrowsClockwise } from '@phosphor-icons/react'

const MESSAGES = [
  { from: 'user', text: 'Oi! Gostaria de saber sobre o plano Professional.' },
  { from: 'agent', text: 'Olá, Beatriz! O Professional inclui CRM completo, 5 agentes de IA e automações por R$ 197/mês. Posso agendar uma demo?' },
  { from: 'user', text: 'Sim, pode ser amanhã às 14h?' },
  { from: 'agent', text: 'Perfeito! Agendado para amanhã, 14h. Enviei a confirmação no seu e-mail.' },
]

const FEATURES = [
  { icon: Robot, label: 'Qualificação automática de leads 24/7' },
  { icon: Brain, label: 'Respostas contextuais com memória de conversa' },
  { icon: ArrowsClockwise, label: 'Integração nativa com OPS CRM' },
]

export default function WhatsAppAgents() {
  return (
    <section className="bg-[#111111] py-28 px-6 overflow-hidden">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left */}
          <div className="fade-in order-2 lg:order-1">
            <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-[0.2em] mb-5">Agentes Inteligentes</p>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white leading-[1.08] mb-6">
              WhatsApp que vende,<br />atende e resolve.<br />
              <span className="text-[#0ABAB5]">Sozinho.</span>
            </h2>
            <p className="text-lg text-zinc-400 leading-relaxed mb-10">
              Agentes de IA conversacional construídos do zero pela OPS — sem dependência de ferramentas de terceiros,
              com controle total do seu negócio.
            </p>
            <ul className="space-y-4 mb-10">
              {FEATURES.map(({ icon: Icon, label }) => (
                <li key={label} className="flex items-center gap-3">
                  <span className="w-9 h-9 rounded-xl bg-[#0ABAB5]/15 flex items-center justify-center shrink-0">
                    <Icon size={17} weight="duotone" className="text-[#0ABAB5]" />
                  </span>
                  <span className="text-sm text-zinc-300 font-medium">{label}</span>
                </li>
              ))}
            </ul>
            <a
              href="#"
              className="inline-flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#089B97] text-white font-semibold px-7 py-3.5 rounded-full transition-all hover:shadow-[0_8px_32px_rgba(10,186,181,0.35)] active:scale-[0.97]"
            >
              Ver demonstração
            </a>
          </div>

          {/* Right — Phone mockup */}
          <div className="fade-in flex justify-center order-1 lg:order-2" style={{ transitionDelay: '0.18s' }}>
            <div className="relative">
              {/* Glow */}
              <div className="absolute inset-0 rounded-[50px] blur-3xl bg-[#0ABAB5]/15 scale-90 translate-y-4" />

              <div className="relative w-[280px] h-[580px] bg-[#1A1A1E] rounded-[46px] border-[3px] border-[#2A2A2E] p-2.5 shadow-[0_50px_100px_rgba(0,0,0,0.7)]">
                {/* Dynamic island */}
                <div className="absolute top-4 left-1/2 -translate-x-1/2 w-24 h-7 bg-[#0A0A0A] rounded-full z-10" />

                <div className="w-full h-full bg-[#0B141A] rounded-[38px] overflow-hidden flex flex-col">
                  {/* Status bar */}
                  <div className="flex items-center justify-between px-5 pt-5 pb-2">
                    <span className="text-[11px] text-white font-semibold">9:41</span>
                    <div className="flex items-center gap-1.5">
                      <svg width="16" height="12" viewBox="0 0 16 12" fill="white" opacity=".8">
                        <rect x="0" y="4" width="3" height="8" rx="1"/>
                        <rect x="4.5" y="2" width="3" height="10" rx="1"/>
                        <rect x="9" y="0" width="3" height="12" rx="1"/>
                      </svg>
                      <svg width="16" height="12" viewBox="0 0 16 12" fill="white" opacity=".8">
                        <path d="M8 2C5.2 2 2.7 3.1 0.9 4.9L2.3 6.3C3.7 4.9 5.75 4 8 4s4.3.9 5.7 2.3l1.4-1.4C13.3 3.1 10.8 2 8 2zm0 4c-1.65 0-3.15.65-4.25 1.7L5.15 9.1C5.9 8.4 6.9 8 8 8s2.1.4 2.85 1.1l1.4-1.4C11.15 6.65 9.65 6 8 6zm0 4a1.5 1.5 0 100 3 1.5 1.5 0 000-3z"/>
                      </svg>
                    </div>
                  </div>

                  {/* Chat header */}
                  <div className="flex items-center gap-3 px-4 py-3 bg-[#1F2C33] border-b border-[#2A3942]">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#0ABAB5] to-[#089B97] flex items-center justify-center text-white font-bold text-[11px] shadow-lg">
                      OPS
                    </div>
                    <div className="flex-1">
                      <p className="text-white text-[13px] font-semibold">OPS Agente IA</p>
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        <p className="text-[10px] text-emerald-400 font-medium">online agora</p>
                      </div>
                    </div>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="5" r="1.5" fill="white" opacity=".5"/>
                      <circle cx="12" cy="12" r="1.5" fill="white" opacity=".5"/>
                      <circle cx="12" cy="19" r="1.5" fill="white" opacity=".5"/>
                    </svg>
                  </div>

                  {/* Date pill */}
                  <div className="flex justify-center py-2.5">
                    <span className="text-[10px] text-[#8696A0] bg-[#182229] px-3 py-1 rounded-full">Hoje</span>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 px-3 pb-2 space-y-2 overflow-hidden">
                    {MESSAGES.map((msg, i) => (
                      <div key={i} className={`flex ${msg.from === 'agent' ? 'justify-end' : 'justify-start'}`}>
                        <div
                          className={`max-w-[82%] rounded-2xl px-3.5 py-2 text-[12px] leading-relaxed ${
                            msg.from === 'agent'
                              ? 'bg-[#005C4B] text-white rounded-br-[4px]'
                              : 'bg-[#1E2A30] text-[#E9EDF0] rounded-bl-[4px]'
                          }`}
                        >
                          {msg.text}
                          <span className={`text-[9px] ml-2 ${msg.from === 'agent' ? 'text-[#88C4B7]' : 'text-[#8696A0]'}`}>
                            {['09:32', '09:32', '09:33', '09:33'][i]}
                          </span>
                        </div>
                      </div>
                    ))}

                    {/* Typing indicator */}
                    <div className="flex justify-start">
                      <div className="bg-[#1E2A30] rounded-2xl rounded-bl-[4px] px-4 py-3 flex items-center gap-1">
                        <span className="typing-dot w-1.5 h-1.5 bg-[#8696A0] rounded-full" />
                        <span className="typing-dot w-1.5 h-1.5 bg-[#8696A0] rounded-full" />
                        <span className="typing-dot w-1.5 h-1.5 bg-[#8696A0] rounded-full" />
                      </div>
                    </div>
                  </div>

                  {/* Input bar */}
                  <div className="px-3 pb-4 pt-2 bg-[#0B141A]">
                    <div className="bg-[#1F2C33] rounded-full px-4 py-2.5 flex items-center gap-2">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" opacity=".5">
                        <circle cx="12" cy="12" r="9" stroke="#8696A0" strokeWidth="1.5"/>
                        <path d="M12 8v4l3 3" stroke="#8696A0" strokeWidth="1.5" strokeLinecap="round"/>
                      </svg>
                      <span className="text-[12px] text-[#8696A0] flex-1">Mensagem</span>
                      <div className="w-8 h-8 rounded-full bg-[#0ABAB5] flex items-center justify-center">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                          <path d="M12 7H2M7 2l5 5-5 5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

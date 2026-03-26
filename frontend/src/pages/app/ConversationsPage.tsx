import { useState } from 'react'
import { ChatCircleDots, MagnifyingGlass, Robot, User, ArrowRight } from '@phosphor-icons/react'

const CONVS = [
  { id: '1', name: 'Beatriz Fontes', phone: '+55 11 98847-3621', last: 'Olá! Gostaria de saber sobre o plano Professional.', time: '14:32', unread: 2, takeover: false, status: 'online', av: 'BF' },
  { id: '2', name: 'Caio Drummond', phone: '+55 21 97654-1234', last: 'Pode ser amanhã às 14h?', time: '13:15', unread: 0, takeover: true, status: 'online', av: 'CD' },
  { id: '3', name: 'Isabela Cruz', phone: '+55 11 91234-5678', last: 'Perfeito! Aguardo o retorno.', time: '11:48', unread: 0, takeover: false, status: 'offline', av: 'IC' },
  { id: '4', name: 'Rodrigo Matos', phone: '+55 31 98765-4321', last: 'Qual o prazo de entrega?', time: '10:20', unread: 1, takeover: false, status: 'online', av: 'RM' },
  { id: '5', name: 'Fernanda Leal', phone: '+55 11 99876-5432', last: 'Obrigada pelas informações!', time: 'Seg', unread: 0, takeover: false, status: 'offline', av: 'FL' },
  { id: '6', name: 'Thiago Bastos', phone: '+55 41 97777-8888', last: 'Vou analisar a proposta.', time: 'Dom', unread: 0, takeover: false, status: 'offline', av: 'TB' },
]

const MSGS = [
  { id: '1', from: 'user', text: 'Olá! Gostaria de saber sobre o plano Professional.', time: '14:30' },
  { id: '2', from: 'bot', text: 'Olá, Beatriz! O Professional inclui CRM completo, 5 agentes de IA e automações por R$ 197/mês. Posso agendar uma demo?', time: '14:30' },
  { id: '3', from: 'user', text: 'Sim, pode ser amanhã às 14h?', time: '14:31' },
  { id: '4', from: 'bot', text: 'Perfeito! Agendado para amanhã, 14h. Enviei a confirmação no seu e-mail. 😊', time: '14:31' },
  { id: '5', from: 'user', text: 'Olá! Gostaria de saber sobre o plano Professional.', time: '14:32' },
]

const COLORS = ['bg-[#0ABAB5]', 'bg-violet-500', 'bg-orange-500', 'bg-rose-500', 'bg-blue-500', 'bg-emerald-600']
function Av({ v, size = 10 }: { v: string; size?: number }) {
  const c = COLORS[v.charCodeAt(0) % COLORS.length]
  const sz = size === 10 ? 'w-10 h-10 text-sm' : 'w-9 h-9 text-xs'
  return <div className={`${sz} ${c} rounded-full flex items-center justify-center text-white font-bold shrink-0`}>{v}</div>
}

export default function ConversationsPage() {
  const [selected, setSelected] = useState<string | null>('1')
  const [message, setMessage] = useState('')

  const conv = CONVS.find(c => c.id === selected)

  return (
    <div className="flex h-[calc(100dvh-56px-64px)] lg:h-[calc(100dvh-56px)] overflow-hidden">
      {/* Conversation list */}
      <div className={`${selected ? 'hidden lg:flex' : 'flex'} flex-col w-full lg:w-[320px] xl:w-[360px] shrink-0 bg-white border-r border-zinc-100`}>
        <div className="p-4 border-b border-zinc-100">
          <h2 className="text-[15px] font-bold text-[#1D1D1F] mb-3">Conversas</h2>
          <div className="flex items-center gap-2 bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2 focus-within:border-[#0ABAB5]/50 transition-all">
            <MagnifyingGlass size={14} className="text-zinc-400" />
            <input placeholder="Buscar conversas..." className="text-[13px] bg-transparent focus:outline-none w-full placeholder:text-zinc-400" />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {CONVS.map(c => (
            <button
              key={c.id}
              onClick={() => setSelected(c.id)}
              className={`w-full flex items-start gap-3 px-4 py-3.5 text-left transition-colors ${selected === c.id ? 'bg-[#0ABAB5]/8 border-l-2 border-[#0ABAB5]' : 'hover:bg-zinc-50 border-l-2 border-transparent'}`}
            >
              <div className="relative">
                <Av v={c.av} />
                {c.status === 'online' && <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-white" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 mb-0.5">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{c.name}</p>
                    {c.takeover && (
                      <span className="shrink-0 flex items-center gap-0.5 text-[9px] font-bold text-orange-600 bg-orange-50 px-1.5 py-0.5 rounded-full border border-orange-100">
                        <User size={8} weight="bold" />HUMANO
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-zinc-400 shrink-0">{c.time}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[12px] text-zinc-400 truncate">{c.last}</p>
                  {c.unread > 0 && (
                    <span className="shrink-0 w-5 h-5 rounded-full bg-[#0ABAB5] text-white text-[10px] font-bold flex items-center justify-center">{c.unread}</span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      {conv ? (
        <div className={`${selected ? 'flex' : 'hidden lg:flex'} flex-col flex-1 bg-white min-w-0`}>
          {/* Chat header */}
          <div className="flex items-center gap-3 px-4 py-3.5 border-b border-zinc-100 shrink-0">
            <button onClick={() => setSelected(null)} className="lg:hidden p-1.5 rounded-lg text-zinc-400 hover:bg-zinc-100 transition-colors mr-1">
              <ArrowRight size={16} weight="bold" className="rotate-180" />
            </button>
            <div className="relative">
              <Av v={conv.av} />
              {conv.status === 'online' && <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-white" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[14px] font-semibold text-[#1D1D1F]">{conv.name}</p>
              <p className="text-[12px] text-zinc-400">{conv.phone}</p>
            </div>
            <div className="flex items-center gap-2">
              {conv.takeover ? (
                <button className="text-[12px] font-semibold text-orange-600 bg-orange-50 border border-orange-100 px-3 py-1.5 rounded-xl hover:bg-orange-100 transition-colors">
                  Devolver ao Bot
                </button>
              ) : (
                <button className="text-[12px] font-semibold text-white bg-[#0ABAB5] px-3 py-1.5 rounded-xl hover:bg-[#089B97] transition-colors">
                  Assumir
                </button>
              )}
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            <div className="flex justify-center">
              <span className="text-[11px] text-zinc-400 bg-zinc-100 px-3 py-1 rounded-full">Hoje</span>
            </div>
            {MSGS.map(msg => (
              <div key={msg.id} className={`flex items-end gap-2 ${msg.from === 'user' ? 'justify-start' : 'justify-end'}`}>
                {msg.from === 'user' && (
                  <div className="w-6 h-6 rounded-full bg-zinc-200 flex items-center justify-center shrink-0">
                    <User size={12} className="text-zinc-500" />
                  </div>
                )}
                <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
                  msg.from === 'user'
                    ? 'bg-zinc-100 text-[#1D1D1F] rounded-bl-sm'
                    : 'bg-[#0ABAB5] text-white rounded-br-sm'
                }`}>
                  <p className="text-[13px] leading-relaxed">{msg.text}</p>
                  <div className={`flex items-center gap-1 mt-1 ${msg.from === 'user' ? 'justify-start' : 'justify-end'}`}>
                    {msg.from === 'bot' && <Robot size={10} className="text-white/60" />}
                    <span className={`text-[10px] ${msg.from === 'user' ? 'text-zinc-400' : 'text-white/60'}`}>{msg.time}</span>
                  </div>
                </div>
                {msg.from === 'bot' && (
                  <div className="w-6 h-6 rounded-full bg-[#0ABAB5]/15 flex items-center justify-center shrink-0">
                    <Robot size={12} className="text-[#0ABAB5]" />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-zinc-100 shrink-0">
            {conv.takeover ? (
              <div className="flex items-end gap-3">
                <div className="flex-1 bg-zinc-50 border border-zinc-200 rounded-2xl px-4 py-3 focus-within:border-[#0ABAB5]/50 focus-within:shadow-[0_0_0_3px_rgba(10,186,181,0.08)] transition-all">
                  <textarea
                    value={message}
                    onChange={e => setMessage(e.target.value)}
                    placeholder="Digite sua mensagem..."
                    rows={1}
                    className="text-[13px] bg-transparent focus:outline-none w-full resize-none placeholder:text-zinc-400"
                  />
                </div>
                <button className="w-10 h-10 rounded-2xl bg-[#0ABAB5] hover:bg-[#089B97] text-white flex items-center justify-center transition-all active:scale-95 shrink-0">
                  <ArrowRight size={16} weight="bold" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-zinc-400 bg-zinc-50 rounded-2xl px-4 py-3 border border-zinc-200">
                <Robot size={15} className="text-[#0ABAB5] shrink-0" />
                <p className="text-[13px]">Agente IA está respondendo automaticamente</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="hidden lg:flex flex-1 flex-col items-center justify-center text-zinc-300 bg-zinc-50/30">
          <ChatCircleDots size={48} weight="duotone" />
          <p className="text-sm mt-2 text-zinc-400">Selecione uma conversa</p>
        </div>
      )}
    </div>
  )
}

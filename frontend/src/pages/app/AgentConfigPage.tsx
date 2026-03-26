import { useState } from 'react'
import { Robot, FloppyDisk, CloudArrowUp, FileText, Trash, CheckCircle } from '@phosphor-icons/react'

type Tab = 'personalidade' | 'rag'

interface RagDoc {
  id: string
  name: string
  size: string
  uploaded: string
}

const INITIAL_DOCS: RagDoc[] = [
  { id: '1', name: 'catalogo_produtos_2025.pdf', size: '2.4 MB', uploaded: 'há 3 dias'    },
  { id: '2', name: 'manual_instalacao.pdf',       size: '1.1 MB', uploaded: 'há 1 semana'  },
  { id: '3', name: 'faq_clientes.txt',            size: '45 KB',  uploaded: 'há 2 semanas' },
]

const DAYS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'] as const

const inputCls = 'w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2.5 text-[13px] text-[#1D1D1F] focus:outline-none focus:border-[#0ABAB5]/50 focus:ring-2 focus:ring-[#0ABAB5]/10 transition-all'
const labelCls = 'block text-[12px] font-semibold text-zinc-500 mb-1.5'

export default function AgentConfigPage() {
  const [tab, setTab] = useState<Tab>('personalidade')
  const [docs, setDocs] = useState<RagDoc[]>(INITIAL_DOCS)
  const [activeDays, setActiveDays] = useState<string[]>(['Seg', 'Ter', 'Qua', 'Qui', 'Sex'])
  const [saved, setSaved] = useState(false)

  function toggleDay(day: string) {
    setActiveDays(prev =>
      prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]
    )
  }

  function handleSave() {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  function handleDeleteDoc(id: string) {
    setDocs(prev => prev.filter(d => d.id !== id))
  }

  return (
    <div className="p-4 md:p-6 space-y-5 pb-6">

      {/* Sticky header */}
      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100 flex items-center justify-between">
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight">Agente IA</h1>
        <button
          onClick={handleSave}
          className={`flex items-center gap-2 text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95 ${
            saved ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-[#0ABAB5] hover:bg-[#09a8a3]'
          }`}
        >
          {saved ? <CheckCircle size={15} weight="fill" /> : <FloppyDisk size={15} weight="bold" />}
          <span className="hidden sm:inline">{saved ? 'Salvo!' : 'Salvar Alterações'}</span>
          <span className="sm:hidden">{saved ? 'Salvo!' : 'Salvar'}</span>
        </button>
      </div>

      {/* Status banner */}
      <div className="flex items-center gap-3 p-3.5 bg-emerald-50 rounded-2xl border border-emerald-100">
        <div className="w-8 h-8 rounded-xl bg-emerald-100 flex items-center justify-center shrink-0">
          <Robot size={16} weight="duotone" className="text-emerald-600" />
        </div>
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="relative flex h-2 w-2 shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <p className="text-[13px] font-semibold text-emerald-800 truncate">Agente ativo e respondendo</p>
        </div>
        <span className="text-[11px] font-semibold text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded-full shrink-0">Online</span>
      </div>

      {/* Tabs */}
      <div className="flex gap-6 border-b border-zinc-100">
        {([
          { key: 'personalidade', label: 'Personalidade' },
          { key: 'rag',           label: 'Documentos RAG' },
        ] as { key: Tab; label: string }[]).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`text-[13px] font-medium pb-2.5 border-b-2 transition-colors -mb-px ${
              tab === key
                ? 'border-[#0ABAB5] text-[#0ABAB5]'
                : 'border-transparent text-zinc-500 hover:text-zinc-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab 1: Personalidade */}
      {tab === 'personalidade' && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6 space-y-5">

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Nome do Agente</label>
                <input
                  type="text"
                  defaultValue="Assistente OPS"
                  className={inputCls}
                />
              </div>
              <div>
                <label className={labelCls}>Idioma Principal</label>
                <select className={inputCls} defaultValue="pt">
                  <option value="pt">Português</option>
                  <option value="en">English</option>
                  <option value="es">Español</option>
                </select>
              </div>
            </div>

            <div>
              <label className={labelCls}>Persona do Agente</label>
              <textarea
                rows={4}
                defaultValue="Você é um assistente especializado em energia solar, projetado para ajudar clientes com dúvidas, orçamentos e suporte técnico de forma clara e objetiva."
                className={`${inputCls} resize-none leading-relaxed`}
              />
            </div>

            <div>
              <label className={labelCls}>Tom de Resposta</label>
              <select className={inputCls} defaultValue="amigavel">
                <option value="formal">Formal</option>
                <option value="amigavel">Amigável</option>
                <option value="tecnico">Técnico</option>
                <option value="casual">Casual</option>
              </select>
            </div>

            {/* Working hours */}
            <div className="pt-2 border-t border-zinc-100">
              <p className="text-[13px] font-bold text-[#1D1D1F] mb-3">Horário de Atendimento</p>
              <div className="flex flex-wrap gap-2 mb-4">
                {DAYS.map(day => (
                  <button
                    key={day}
                    onClick={() => toggleDay(day)}
                    className={`text-[12px] font-semibold px-3 py-1.5 rounded-xl border transition-all ${
                      activeDays.includes(day)
                        ? 'bg-[#0ABAB5] text-white border-[#0ABAB5]'
                        : 'bg-zinc-50 text-zinc-500 border-zinc-200 hover:border-zinc-300'
                    }`}
                  >
                    {day}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <label className={labelCls}>Início</label>
                  <input type="time" defaultValue="08:00" className={inputCls} />
                </div>
                <div className="flex-1">
                  <label className={labelCls}>Fim</label>
                  <input type="time" defaultValue="18:00" className={inputCls} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: RAG Documents */}
      {tab === 'rag' && (
        <div className="space-y-4">

          {/* Upload zone */}
          <div className="flex flex-col items-center gap-3 p-8 bg-white rounded-2xl border-2 border-dashed border-zinc-200 hover:border-[#0ABAB5]/50 hover:bg-[#0ABAB5]/3 transition-all cursor-pointer">
            <div className="w-11 h-11 rounded-2xl bg-zinc-50 border border-zinc-200 flex items-center justify-center">
              <CloudArrowUp size={22} weight="duotone" className="text-zinc-400" />
            </div>
            <div className="text-center">
              <p className="text-[13px] font-semibold text-[#1D1D1F]">Arraste PDFs ou TXTs aqui</p>
              <p className="text-[12px] text-zinc-400 mt-0.5">ou clique para selecionar arquivos</p>
            </div>
          </div>

          {/* Document list */}
          <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 overflow-hidden">
            <div className="px-5 py-3 border-b border-zinc-100 bg-zinc-50/60">
              <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">
                Documentos indexados ({docs.length})
              </p>
            </div>
            {docs.length === 0 ? (
              <div className="flex flex-col items-center py-10 text-zinc-300">
                <FileText size={36} weight="duotone" />
                <p className="text-sm mt-2 text-zinc-400">Nenhum documento indexado</p>
              </div>
            ) : (
              <div className="divide-y divide-zinc-100">
                {docs.map(doc => (
                  <div key={doc.id} className="flex items-center gap-3 px-5 py-3.5 hover:bg-zinc-50/60 transition-colors group">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
                      <FileText size={15} weight="duotone" className="text-blue-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{doc.name}</p>
                      <p className="text-[11px] text-zinc-400">{doc.size} · {doc.uploaded}</p>
                    </div>
                    <button
                      onClick={() => handleDeleteDoc(doc.id)}
                      className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-50 text-zinc-400 hover:text-red-500 transition-all"
                      aria-label="Excluir documento"
                    >
                      <Trash size={14} weight="bold" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <p className="text-[12px] text-zinc-400 px-1">
            Documentos adicionados são processados e indexados automaticamente para o agente usar como base de conhecimento.
          </p>
        </div>
      )}
    </div>
  )
}

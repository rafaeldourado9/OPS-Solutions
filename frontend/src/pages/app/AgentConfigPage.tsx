import { useState, useRef, useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Robot, FloppyDisk, CloudArrowUp, FileText, Trash, CheckCircle,
  SpinnerGap, Warning, WifiHigh, WifiX, QrCode, ArrowClockwise,
} from '@phosphor-icons/react'
import toast from 'react-hot-toast'
import { agentsApi, type RagDocument } from '../../api/agents'
import { whatsappApi, type WhatsAppNumber } from '../../api/whatsapp'

type Tab = 'status' | 'personalidade' | 'rag'

const inputCls = 'w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2.5 text-[13px] text-[#1D1D1F] focus:outline-none focus:border-[#0ABAB5]/50 focus:ring-2 focus:ring-[#0ABAB5]/10 transition-all'
const labelCls = 'block text-[12px] font-semibold text-zinc-500 mb-1.5'

// ─── Status Tab ───────────────────────────────────────────────────────────────

function StatusTab() {
  const qc = useQueryClient()

  const { data: numbers = [], isLoading } = useQuery<WhatsAppNumber[]>({
    queryKey: ['whatsapp-numbers'],
    queryFn: whatsappApi.listNumbers,
    refetchInterval: 5000,
  })

  const number = numbers[0] as WhatsAppNumber | undefined

  // Global status/QR as fallback when no number is registered yet
  const { data: globalStatus } = useQuery({
    queryKey: ['whatsapp-global-status'],
    queryFn: agentsApi.getWhatsAppStatus,
    refetchInterval: 5000,
    enabled: !number,
  })
  const { data: globalQr, isLoading: loadingGlobalQr } = useQuery({
    queryKey: ['whatsapp-global-qr'],
    queryFn: agentsApi.getWhatsAppQr,
    refetchInterval: 8000,
    enabled: !number,
  })

  const isConnected = number ? number.status === 'connected' : globalStatus?.status === 'connected'
  const isConnecting = number
    ? (number.status === 'connecting' || number.status === 'qr')
    : (globalStatus?.status === 'connecting' || globalStatus?.status === 'qr')

  const { data: qrData, isLoading: loadingQr } = useQuery({
    queryKey: ['whatsapp-qr', number?.id],
    queryFn: () => whatsappApi.getQr(number!.id),
    refetchInterval: 8000,
    enabled: !!number && !isConnected,
  })

  const restart = useMutation({
    mutationFn: () => number ? whatsappApi.restart(number.id) : agentsApi.restartWhatsApp(),
    onSuccess: () => {
      toast.success('Gateway reiniciado')
      qc.invalidateQueries({ queryKey: ['whatsapp-numbers'] })
      qc.invalidateQueries({ queryKey: ['whatsapp-qr'] })
      qc.invalidateQueries({ queryKey: ['whatsapp-global-status'] })
      qc.invalidateQueries({ queryKey: ['whatsapp-global-qr'] })
    },
    onError: () => toast.error('Erro ao reiniciar'),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <SpinnerGap size={28} className="animate-spin text-[#0ABAB5]" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Status card */}
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-5">
        <div className="flex items-center gap-4">
          <div className={`relative w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${
            isConnected ? 'bg-emerald-50' : 'bg-zinc-50'
          }`}>
            {isConnected ? (
              <WifiHigh size={22} weight="fill" className="text-emerald-500" />
            ) : (
              <WifiX size={22} weight="fill" className="text-zinc-400" />
            )}
            {isConnected && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500" />
              </span>
            )}
          </div>
          <div className="flex-1">
            <p className="text-[15px] font-bold text-[#1D1D1F]">Agente Alexandre</p>
            <p className={`text-[13px] mt-0.5 font-medium ${
              isConnected ? 'text-emerald-600' : isConnecting ? 'text-amber-500' : 'text-zinc-400'
            }`}>
              {isConnected
                ? `Conectado${number?.phone_number ? ` · ${number.phone_number}` : ''}`
                : isConnecting
                  ? 'Aguardando leitura do QR Code...'
                  : 'Offline — escaneie o QR Code para conectar'}
            </p>
          </div>
          {number && (
            <button
              onClick={() => restart.mutate()}
              disabled={restart.isPending}
              title="Reiniciar gateway"
              className="p-2 rounded-xl border border-zinc-200 text-zinc-400 hover:bg-zinc-50 hover:text-zinc-600 transition-all disabled:opacity-50"
            >
              {restart.isPending
                ? <SpinnerGap size={15} className="animate-spin" />
                : <ArrowClockwise size={15} />}
            </button>
          )}
        </div>
      </div>

      {/* QR Code — shown when offline */}
      {!isConnected && (
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-6">
          <div className="flex items-center gap-2 mb-4">
            <QrCode size={16} weight="duotone" className="text-[#0ABAB5]" />
            <p className="text-[13px] font-semibold text-[#1D1D1F]">Conectar WhatsApp</p>
          </div>
          <p className="text-[12px] text-zinc-400 mb-5">
            Abra o WhatsApp no celular → <strong>Dispositivos conectados</strong> → <strong>Conectar dispositivo</strong> → escaneie o código abaixo.
          </p>
          <div className="flex justify-center">
            {(number ? loadingQr : loadingGlobalQr) ? (
              <div className="flex flex-col items-center gap-3 py-10">
                <SpinnerGap size={28} className="animate-spin text-[#0ABAB5]" />
                <p className="text-[12px] text-zinc-400">Gerando QR Code...</p>
              </div>
            ) : (number ? qrData?.qr : globalQr?.qr) ? (
              <div className="p-3 bg-white border-2 border-zinc-100 rounded-2xl shadow-sm inline-block">
                <img src={(number ? qrData?.qr : globalQr?.qr) || ''} alt="QR Code WhatsApp" className="w-52 h-52 block" />
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3 py-10 text-zinc-400">
                <Warning size={32} weight="duotone" className="text-amber-400" />
                <p className="text-[12px] text-center">QR Code indisponível.<br/>Clique em reiniciar e aguarde.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}


// ─── Personalidade Tab ────────────────────────────────────────────────────────

const AGENT_ROLES = [
  {
    key: 'vendas',
    label: 'Vendas',
    description: 'Foco em qualificar leads e conduzir até o fechamento',
  },
  {
    key: 'suporte',
    label: 'Suporte',
    description: 'Resolve problemas técnicos e escala quando necessário',
  },
  {
    key: 'faq',
    label: 'FAQ',
    description: 'Responde dúvidas com base nos documentos cadastrados',
  },
]

function PersonalidadeTab() {
  const qc = useQueryClient()
  const [saved, setSaved] = useState(false)

  const { data: config, isLoading } = useQuery({
    queryKey: ['agent-config'],
    queryFn: agentsApi.getConfig,
  })

  const update = useMutation({
    mutationFn: agentsApi.updateConfig,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agent-config'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    },
    onError: () => toast.error('Erro ao salvar configuração'),
  })

  const nameRef = useRef<HTMLInputElement>(null)
  const ttsVoiceRef = useRef<HTMLSelectElement>(null)
  const [ttsEnabled, setTtsEnabled] = useState(false)
  const [ttsChance, setTtsChance] = useState(0.75)
  const [role, setRole] = useState('vendas')

  useEffect(() => {
    if (config) {
      setTtsEnabled(!!config.media?.tts_enabled)
      setTtsChance(config.media?.tts_chance ?? 0.75)
      setRole(config.agent?.role ?? 'vendas')
    }
  }, [config])

  function handleSave() {
    update.mutate({
      agent: {
        name: nameRef.current?.value,
        role,
      },
      media: {
        tts_enabled: ttsEnabled,
        tts_voice: ttsVoiceRef.current?.value,
        tts_chance: ttsChance,
      },
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <SpinnerGap size={28} className="animate-spin text-[#0ABAB5]" />
      </div>
    )
  }

  if (!config) {
    return (
      <div className="flex flex-col items-center gap-2 py-16 text-zinc-400">
        <Warning size={28} weight="duotone" />
        <p className="text-[13px]">Configuração não encontrada.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6 space-y-5">

        {/* Nome do agente */}
        <div className="max-w-xs">
          <label className={labelCls}>Nome do Agente</label>
          <input
            ref={nameRef}
            type="text"
            defaultValue={config.agent?.name ?? ''}
            placeholder="Alexandre, Sofia..."
            className={inputCls}
          />
          <p className="text-[11px] text-zinc-400 mt-1">Como o agente se apresenta aos clientes</p>
        </div>

        {/* Função */}
        <div>
          <label className={labelCls}>Personalidade do Agente</label>
          <p className="text-[11px] text-zinc-400 mb-3">Alexandre adapta seu comportamento conforme a personalidade selecionada</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-1">
            {AGENT_ROLES.map(r => (
              <button
                key={r.key}
                type="button"
                onClick={() => setRole(r.key)}
                className={`text-left p-4 rounded-2xl border-2 transition-all ${
                  role === r.key
                    ? 'border-[#0ABAB5] bg-[#0ABAB5]/5'
                    : 'border-zinc-100 hover:border-zinc-200 bg-white'
                }`}
              >
                <p className={`text-[13px] font-bold mb-1 ${role === r.key ? 'text-[#0ABAB5]' : 'text-[#1D1D1F]'}`}>
                  {r.label}
                </p>
                <p className="text-[11px] text-zinc-400 leading-snug">{r.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* TTS */}
        <div className="pt-2 border-t border-zinc-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[13px] font-semibold text-[#1D1D1F]">Respostas por áudio</p>
              <p className="text-[11px] text-zinc-400 mt-0.5">O agente responde em voz sintética</p>
            </div>
            <button
              type="button"
              onClick={() => setTtsEnabled(v => !v)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                ttsEnabled ? 'bg-[#0ABAB5]' : 'bg-zinc-200'
              }`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                ttsEnabled ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          </div>
          {ttsEnabled && (
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Voz</label>
                <select ref={ttsVoiceRef} className={inputCls} defaultValue={config.media?.tts_voice ?? 'Puck'}>
                  <option value="Kore">Kore (feminino)</option>
                  <option value="Aoede">Aoede (feminino)</option>
                  <option value="Puck">Puck (masculino)</option>
                  <option value="Charon">Charon (masculino)</option>
                  <option value="Fenrir">Fenrir (masculino)</option>
                </select>
              </div>
              <div>
                <label className={labelCls}>Frequência ({Math.round(ttsChance * 100)}% das respostas)</label>
                <input
                  type="range" min={0} max={1} step={0.05}
                  value={ttsChance}
                  onChange={e => setTtsChance(parseFloat(e.target.value))}
                  className="w-full accent-[#0ABAB5] mt-2"
                />
                <div className="flex justify-between text-[10px] text-zinc-400 mt-0.5">
                  <span>Nunca</span><span>Sempre</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={update.isPending}
          className={`flex items-center gap-2 text-white text-[13px] font-semibold px-5 py-2.5 rounded-xl transition-all active:scale-95 disabled:opacity-60 ${
            saved ? 'bg-emerald-500' : 'bg-[#0ABAB5] hover:bg-[#09a8a3]'
          }`}
        >
          {update.isPending ? <SpinnerGap size={14} className="animate-spin" /> : saved ? <CheckCircle size={14} weight="fill" /> : <FloppyDisk size={14} weight="bold" />}
          {update.isPending ? 'Salvando...' : saved ? 'Salvo!' : 'Salvar'}
        </button>
      </div>
    </div>
  )
}

// ─── RAG Tab ──────────────────────────────────────────────────────────────────

function RagTab() {
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const { data: instances = [] } = useQuery({
    queryKey: ['agent-instances'],
    queryFn: agentsApi.listInstances,
  })
  const activeAgentId: string = (instances as any[]).find((i: any) => i.active)?.agent_id ?? ''

  const { data: docs = [], isLoading } = useQuery<RagDocument[]>({
    queryKey: ['rag-docs', activeAgentId],
    queryFn: () => agentsApi.listDocs(activeAgentId || undefined),
    enabled: true,
  })

  const upload = useMutation({
    mutationFn: (file: File) =>
      agentsApi.uploadDoc(file, activeAgentId, file.name),
    onSuccess: () => {
      toast.success('Documento indexado com sucesso')
      qc.invalidateQueries({ queryKey: ['rag-docs'] })
    },
    onError: () => toast.error('Erro ao indexar documento'),
  })

  const deleteDoc = useMutation({
    mutationFn: (name: string) => agentsApi.deleteDoc(name, activeAgentId || undefined),
    onSuccess: () => {
      toast.success('Documento removido')
      qc.invalidateQueries({ queryKey: ['rag-docs'] })
    },
    onError: () => toast.error('Erro ao remover documento'),
  })

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return
    Array.from(files).forEach(f => upload.mutate(f))
  }, [upload])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    handleFiles(e.dataTransfer.files)
  }, [handleFiles])

  return (
    <div className="space-y-4">
      {/* Upload zone */}
      <div
        onClick={() => fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`flex flex-col items-center gap-3 p-8 bg-white rounded-2xl border-2 border-dashed transition-all cursor-pointer ${
          dragging
            ? 'border-[#0ABAB5] bg-[#0ABAB5]/5'
            : 'border-zinc-200 hover:border-[#0ABAB5]/50 hover:bg-[#0ABAB5]/3'
        }`}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.txt,.docx,.md"
          multiple
          className="hidden"
          onChange={e => handleFiles(e.target.files)}
        />
        <div className="w-11 h-11 rounded-2xl bg-zinc-50 border border-zinc-200 flex items-center justify-center">
          {upload.isPending
            ? <SpinnerGap size={22} className="animate-spin text-[#0ABAB5]" />
            : <CloudArrowUp size={22} weight="duotone" className="text-zinc-400" />}
        </div>
        <div className="text-center">
          <p className="text-[13px] font-semibold text-[#1D1D1F]">
            {upload.isPending ? 'Indexando...' : 'Arraste PDFs, TXTs ou DOCXs aqui'}
          </p>
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

        {isLoading ? (
          <div className="flex items-center justify-center py-10">
            <SpinnerGap size={24} className="animate-spin text-[#0ABAB5]" />
          </div>
        ) : docs.length === 0 ? (
          <div className="flex flex-col items-center py-10 text-zinc-300">
            <FileText size={36} weight="duotone" />
            <p className="text-sm mt-2 text-zinc-400">Nenhum documento indexado</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-100">
            {docs.map(doc => (
              <div key={doc.name} className="flex items-center gap-3 px-5 py-3.5 hover:bg-zinc-50/60 transition-colors group">
                <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
                  <FileText size={15} weight="duotone" className="text-blue-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{doc.name}</p>
                  <p className="text-[11px] text-zinc-400">
                    {doc.chunk_count} chunks
                    {doc.ingested_at ? ` · ${new Date(doc.ingested_at).toLocaleDateString('pt-BR')}` : ''}
                  </p>
                </div>
                <button
                  onClick={() => deleteDoc.mutate(doc.name)}
                  disabled={deleteDoc.isPending}
                  className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-50 text-zinc-400 hover:text-red-500 transition-all disabled:opacity-60"
                >
                  <Trash size={14} weight="bold" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <p className="text-[12px] text-zinc-400 px-1">
        Documentos são processados e indexados automaticamente para o agente usar como base de conhecimento.
      </p>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AgentConfigPage() {
  const [tab, setTab] = useState<Tab>('status')

  const { data: numbers = [] } = useQuery<WhatsAppNumber[]>({
    queryKey: ['whatsapp-numbers'],
    queryFn: whatsappApi.listNumbers,
    refetchInterval: 10000,
  })

  const isConnected = numbers.some(n => n.status === 'connected')

  const TABS: { key: Tab; label: string }[] = [
    { key: 'status',        label: 'Status'        },
    { key: 'personalidade', label: 'Personalidade' },
    { key: 'rag',           label: 'Documentos RAG'},
  ]

  return (
    <div className="p-4 md:p-6 space-y-5 pb-6">

      {/* Header */}
      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100 flex items-center gap-3">
        <Robot size={18} weight="duotone" className="text-[#0ABAB5] shrink-0" />
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight flex-1">Agente IA</h1>
        <div className={`flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full ${
          isConnected ? 'bg-emerald-100 text-emerald-700' : 'bg-zinc-100 text-zinc-500'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-zinc-400'}`} />
          {isConnected ? 'Online' : 'Offline'}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-6 border-b border-zinc-100">
        {TABS.map(({ key, label }) => (
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

      {tab === 'status'        && <StatusTab />}
      {tab === 'personalidade' && <PersonalidadeTab />}
      {tab === 'rag'           && <RagTab />}
    </div>
  )
}

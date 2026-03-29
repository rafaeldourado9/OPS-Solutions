import { useState, useRef, useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Robot, FloppyDisk, CloudArrowUp, FileText, Trash, CheckCircle,
  QrCode, ArrowClockwise, SignOut, SpinnerGap, Warning,
  WifiHigh, WifiX, WifiSlash, Plus, Lightning, Star, Chats,
} from '@phosphor-icons/react'
import toast from 'react-hot-toast'
import { agentsApi, type RagDocument, type AgentInstance } from '../../api/agents'
import { whatsappApi, type WhatsAppNumber } from '../../api/whatsapp'

type Tab = 'whatsapp' | 'instancias' | 'personalidade' | 'rag'

const inputCls = 'w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2.5 text-[13px] text-[#1D1D1F] focus:outline-none focus:border-[#0ABAB5]/50 focus:ring-2 focus:ring-[#0ABAB5]/10 transition-all'
const labelCls = 'block text-[12px] font-semibold text-zinc-500 mb-1.5'

// ─── WhatsApp Number Card ────────────────────────────────────────────────────────
function WhatsAppNumberCard({ number, instances }: { number: WhatsAppNumber; instances: AgentInstance[] }) {
  const qc = useQueryClient()

  // Only poll QR if status is 'qr' (not connected)
  const isConnected = number.status === 'connected'
  const isConnecting = number.status === 'connecting' || number.status === 'qr'

  const { data: qrData, isLoading: loadingQr } = useQuery({
    queryKey: ['whatsapp-qr', number.id],
    queryFn: () => whatsappApi.getQr(number.id),
    refetchInterval: (!isConnected && number.status !== 'error') ? 8000 : false,
    enabled: (!isConnected && number.status !== 'error'),
  })

  const restart = useMutation({
    mutationFn: () => whatsappApi.restart(number.id),
    onSuccess: () => {
      toast.success('Gateway reiniciado')
      qc.invalidateQueries({ queryKey: ['whatsapp-numbers'] })
    },
    onError: () => toast.error('Erro ao reiniciar'),
  })

  const logout = useMutation({
    mutationFn: () => whatsappApi.logout(number.id),
    onSuccess: () => {
      toast.success('Sessão encerrada')
      qc.invalidateQueries({ queryKey: ['whatsapp-numbers'] })
    },
    onError: () => toast.error('Erro ao desconectar'),
  })

  const remove = useMutation({
    mutationFn: () => whatsappApi.removeNumber(number.id),
    onSuccess: () => {
      toast.success('Número removido')
      qc.invalidateQueries({ queryKey: ['whatsapp-numbers'] })
    },
    onError: () => toast.error('Erro ao remover número'),
  })

  const update = useMutation({
    mutationFn: (updates: { label?: string; agent_id?: string }) => whatsappApi.updateNumber(number.id, updates),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['whatsapp-numbers'] })
  })

  return (
    <div className="bg-white rounded-2xl border border-zinc-200 overflow-hidden shadow-sm">
      {/* Header / Info */}
      <div className={`p-4 flex items-start sm:items-center gap-4 border-b border-zinc-100 ${
        isConnected ? 'bg-emerald-50/50' : isConnecting ? 'bg-amber-50/50' : 'bg-red-50/50'
      }`}>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 mt-1 sm:mt-0 ${
          isConnected ? 'bg-emerald-100' : isConnecting ? 'bg-amber-100' : 'bg-red-100'
        }`}>
          {isConnected ? (
            <WifiHigh size={18} weight="fill" className="text-emerald-600" />
          ) : isConnecting ? (
            <WifiSlash size={18} weight="fill" className="text-amber-600" />
          ) : (
            <WifiX size={18} weight="fill" className="text-red-500" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <input
              className="text-[14px] font-bold text-[#1D1D1F] bg-transparent border-none focus:ring-2 focus:ring-[#0ABAB5]/50 px-1 -ml-1 rounded transition-colors"
              defaultValue={number.label || 'Meu WhatsApp'}
              onBlur={(e) => {
                if (e.target.value !== number.label) update.mutate({ label: e.target.value })
              }}
            />
            {isConnected && (
              <span className="inline-flex h-2 w-2 shrink-0 self-start sm:self-center">
                <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-emerald-400 opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
            )}
          </div>
          <p className={`text-[12px] mt-0.5 ${
            isConnected ? 'text-emerald-700' : isConnecting ? 'text-amber-700' : 'text-red-600'
          }`}>
            {isConnected ? `Conectado: ${number.phone_number || ''}` : 
             isConnecting ? 'Aguardando QR Code...' : 'Desconectado'}
          </p>
        </div>
        
        {/* Agent Select */}
        <div className="flex flex-col items-end gap-1">
          <select 
            className="text-[12px] bg-white border border-zinc-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#0ABAB5]"
            value={number.agent_id || ''}
            onChange={(e) => update.mutate({ agent_id: e.target.value || undefined })}
          >
            <option value="">Agent: Padrão da Conta</option>
            {instances.map(inst => (
              <option key={inst.agent_id} value={inst.agent_id}>Agent: {inst.name || inst.agent_id}</option>
            ))}
          </select>
          <button
            onClick={() => remove.mutate()}
            disabled={remove.isPending}
            className="text-[12px] text-zinc-400 hover:text-red-500 transition-colors p-1"
            title="Remover número"
          >
            <Trash size={16} />
          </button>
        </div>
      </div>

      {/* QR Code Section */}
      {!isConnected && (
        <div className="p-4 bg-zinc-50 border-b border-zinc-100 flex flex-col items-center gap-3">
          <div className="flex items-center gap-2 text-zinc-500 self-start">
            <QrCode size={16} weight="duotone" />
            <p className="text-[12px] font-medium">Abra o WhatsApp e escaneie o código</p>
          </div>
          
          {loadingQr ? (
            <div className="flex flex-col items-center gap-3 py-6">
              <SpinnerGap size={24} className="animate-spin text-[#0ABAB5]" />
              <p className="text-[12px] text-zinc-400">Verificando...</p>
            </div>
          ) : qrData?.qr ? (
            <div className="p-2 bg-white border border-zinc-200 rounded-xl shadow-sm">
              <img src={qrData.qr} alt="QR Code WhatsApp" className="w-48 h-48" />
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 py-6 text-zinc-300">
              <Warning size={32} weight="duotone" className="text-amber-400" />
              <p className="text-[12px] text-zinc-500">
                Se o bot estiver travado, clique em Reiniciar.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="px-4 py-3 bg-white flex gap-2">
        <button
          onClick={() => restart.mutate()}
          disabled={restart.isPending}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-zinc-200 text-[12px] font-medium text-zinc-600 hover:bg-zinc-50 transition-all disabled:opacity-60"
        >
          {restart.isPending ? <SpinnerGap size={14} className="animate-spin" /> : <ArrowClockwise size={14} />}
          Reiniciar
        </button>
        {isConnected && (
          <button
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-red-200 text-[12px] font-medium text-red-500 hover:bg-red-50 transition-all disabled:opacity-60"
          >
            {logout.isPending ? <SpinnerGap size={14} className="animate-spin" /> : <SignOut size={14} />}
            Desconectar Site
          </button>
        )}
      </div>
    </div>
  )
}

function WhatsAppTab() {
  const qc = useQueryClient()

  const { data: numbers = [], isLoading } = useQuery({
    queryKey: ['whatsapp-numbers'],
    queryFn: whatsappApi.listNumbers,
    refetchInterval: 5000,
  })

  const { data: instances = [] } = useQuery<AgentInstance[]>({
    queryKey: ['agent-instances'],
    queryFn: agentsApi.listInstances,
  })

  const addNumber = useMutation({
    mutationFn: (agent_id?: string) => whatsappApi.addNumber({ label: 'Novo Número', agent_id }),
    onSuccess: () => {
      toast.success('Novo número adicionado')
      qc.invalidateQueries({ queryKey: ['whatsapp-numbers'] })
    },
    onError: () => toast.error('Erro ao adicionar número'),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <SpinnerGap size={28} className="animate-spin text-[#0ABAB5]" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[14px] font-bold text-[#1D1D1F]">Números Conectados</h2>
          <p className="text-[12px] text-zinc-500">
            Associe múltiplos números de WhatsApp à sua conta e direcione para instâncias específicas
          </p>
        </div>
        <button
          onClick={() => addNumber.mutate(undefined)}
          disabled={addNumber.isPending}
          className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#089B97] text-white text-[12px] font-semibold px-4 py-2 rounded-xl transition-all disabled:opacity-60"
        >
          {addNumber.isPending ? <SpinnerGap size={14} className="animate-spin" /> : <Plus size={14} weight="bold" />}
          Adicionar Número
        </button>
      </div>

      {numbers.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-zinc-300 bg-white rounded-2xl border border-zinc-100 shadow-[0_1px_12px_rgba(0,0,0,0.06)]">
          <Chats size={48} weight="duotone" className="text-zinc-200 mb-2" />
          <p className="text-[14px] font-medium text-zinc-500">Nenhum número conectado</p>
          <p className="text-[12px] text-zinc-400 text-center max-w-sm mt-1">
            Clique em "Adicionar Número" para conectar um novo WhatsApp à sua conta.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {numbers.map((n: WhatsAppNumber) => (
            <WhatsAppNumberCard key={n.id} number={n} instances={instances} />
          ))}
        </div>
      )}
    </div>
  )
}


// ─── Personalidade Tab ────────────────────────────────────────────────────────

function PersonalidadeTab() {
  const qc = useQueryClient()
  const [saved, setSaved] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

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

  const nameRef    = useRef<HTMLInputElement>(null)
  const companyRef = useRef<HTMLInputElement>(null)
  const personaRef = useRef<HTMLTextAreaElement>(null)
  const langRef    = useRef<HTMLSelectElement>(null)
  const ttsVoiceRef = useRef<HTMLSelectElement>(null)
  const [ttsEnabled, setTtsEnabled] = useState(false)
  const [ttsChance, setTtsChance] = useState(0.75)

  // Sync TTS state when config loads
  useEffect(() => {
    if (config) {
      setTtsEnabled(!!config.media?.tts_enabled)
      setTtsChance(config.media?.tts_chance ?? 0.75)
    }
  }, [config])

  function handleSave() {
    update.mutate({
      agent: {
        name: nameRef.current?.value,
        company: companyRef.current?.value,
        language: langRef.current?.value,
        persona: personaRef.current?.value,
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
        <p className="text-[13px]">Configuração não encontrada. Verifique se o agente está configurado.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-6 space-y-5">

        {/* Nome + Empresa + Idioma */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Nome do Assistente</label>
            <input
              ref={nameRef}
              type="text"
              defaultValue={config.agent?.name ?? ''}
              placeholder="Sofia, Carlos, Ana..."
              className={inputCls}
            />
            <p className="text-[11px] text-zinc-400 mt-1">Como seus clientes vão chamá-lo</p>
          </div>
          <div>
            <label className={labelCls}>Nome da Empresa</label>
            <input
              ref={companyRef}
              type="text"
              defaultValue={config.agent?.company ?? ''}
              placeholder="Sua Empresa Ltda"
              className={inputCls}
            />
            <p className="text-[11px] text-zinc-400 mt-1">O agente usará este nome ao se apresentar</p>
          </div>
        </div>

        <div>
          <label className={labelCls}>Idioma Principal</label>
          <select ref={langRef} className={`${inputCls} max-w-xs`} defaultValue={config.agent?.language ?? 'pt-BR'}>
            <option value="pt-BR">Português (Brasil)</option>
            <option value="en">English</option>
            <option value="es">Español</option>
          </select>
        </div>

        {/* Personalidade — principal campo */}
        <div>
          <label className={labelCls}>Personalidade e Instruções</label>
          <textarea
            ref={personaRef}
            rows={8}
            defaultValue={config.agent?.persona ?? ''}
            placeholder={`Descreva como o assistente deve se comportar.\n\nExemplos:\n— Tom consultivo, especialista em energia solar, faz perguntas para entender o consumo do cliente\n— Simpático, usa linguagem informal, responde rápido e diretamente\n— Sempre apresenta preços e condições antes de dar qualquer desconto`}
            className={`${inputCls} resize-none leading-relaxed`}
          />
          <p className="text-[11px] text-zinc-400 mt-1">
            Este texto define toda a personalidade, tom e comportamento do assistente. Seja específico.
          </p>
        </div>

        {/* Áudio / TTS — seção opcional */}
        <div className="pt-2 border-t border-zinc-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[13px] font-semibold text-[#1D1D1F]">Respostas por áudio</p>
              <p className="text-[11px] text-zinc-400 mt-0.5">O assistente responde em áudio (voz sintética)</p>
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

        {/* Configurações avançadas — colapsível */}
        <div className="pt-2 border-t border-zinc-100">
          <button
            type="button"
            onClick={() => setShowAdvanced(v => !v)}
            className="flex items-center gap-2 text-[12px] font-semibold text-zinc-400 hover:text-zinc-600 transition-colors"
          >
            <span className={`transition-transform ${showAdvanced ? 'rotate-90' : ''}`}>▶</span>
            Configurações avançadas
          </button>
          {showAdvanced && (
            <div className="mt-4 space-y-4 pl-4 border-l-2 border-zinc-100">
              <p className="text-[11px] text-zinc-400">
                Modelo: <span className="font-mono font-semibold text-zinc-600">{config.llm?.provider}/{config.llm?.model}</span>
                {' '}· Temperatura: <span className="font-semibold text-zinc-600">{config.llm?.temperature}</span>
                {' '}· A chave Gemini é gerenciada em <strong>Configurações → Integrações</strong>.
              </p>
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
          {update.isPending
            ? <SpinnerGap size={14} className="animate-spin" />
            : saved
              ? <CheckCircle size={14} weight="fill" />
              : <FloppyDisk size={14} weight="bold" />}
          {update.isPending ? 'Salvando...' : saved ? 'Salvo!' : 'Salvar Alterações'}
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

  const { data: instances = [] } = useQuery<AgentInstance[]>({
    queryKey: ['agent-instances'],
    queryFn: agentsApi.listInstances,
  })
  const activeAgentId = instances.find(i => i.active)?.agent_id ?? ''

  const { data: docs = [], isLoading } = useQuery<RagDocument[]>({
    queryKey: ['rag-docs'],
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

// ─── Instâncias Tab ───────────────────────────────────────────────────────────

function InstanciasTab() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [newId, setNewId]     = useState('')
  const [newName, setNewName] = useState('')

  const { data: instances = [], isLoading } = useQuery<AgentInstance[]>({
    queryKey: ['agent-instances'],
    queryFn: agentsApi.listInstances,
  })

  const create = useMutation({
    mutationFn: () => agentsApi.createInstance({ agent_id: newId, name: newName || undefined }),
    onSuccess: () => {
      toast.success('Instância criada')
      qc.invalidateQueries({ queryKey: ['agent-instances'] })
      setShowCreate(false)
      setNewId('')
      setNewName('')
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail ?? 'Erro ao criar instância'
      toast.error(typeof msg === 'string' ? msg : 'Erro ao criar instância')
    },
  })

  const activate = useMutation({
    mutationFn: (agent_id: string) => agentsApi.activateInstance(agent_id),
    onSuccess: () => {
      toast.success('Instância ativada')
      qc.invalidateQueries({ queryKey: ['agent-instances'] })
    },
    onError: () => toast.error('Erro ao ativar instância'),
  })

  const remove = useMutation({
    mutationFn: (agent_id: string) => agentsApi.deleteInstance(agent_id),
    onSuccess: () => {
      toast.success('Instância removida')
      qc.invalidateQueries({ queryKey: ['agent-instances'] })
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail ?? 'Erro ao remover instância'
      toast.error(typeof msg === 'string' ? msg : 'Erro ao remover')
    },
  })

  const handleIdInput = (v: string) => {
    setNewId(v.toLowerCase().replace(/[^a-z0-9_-]/g, ''))
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[13px] font-bold text-[#1D1D1F]">Instâncias de agente</p>
          <p className="text-[12px] text-zinc-400 mt-0.5">
            {instances.length} {instances.length === 1 ? 'instância' : 'instâncias'} — cada uma pode ter seu próprio número de WhatsApp
          </p>
        </div>
        <button
          onClick={() => setShowCreate(v => !v)}
          className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#089B97] text-white text-[12px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95"
        >
          <Plus size={13} weight="bold" />
          Nova instância
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="bg-white rounded-2xl border border-zinc-200 p-4 space-y-3 shadow-sm">
          <p className="text-[12px] font-bold text-zinc-600">Nova instância</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>
                ID da instância
                <span className="text-zinc-400 font-normal ml-1">(letras, números, hífens)</span>
              </label>
              <input
                value={newId}
                onChange={e => handleIdInput(e.target.value)}
                placeholder="meu-agente"
                className={inputCls}
              />
            </div>
            <div>
              <label className={labelCls}>Nome de exibição <span className="text-zinc-400 font-normal">(opcional)</span></label>
              <input
                value={newName}
                onChange={e => setNewName(e.target.value)}
                placeholder="Assistente Vendas"
                className={inputCls}
              />
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowCreate(false)}
              className="text-[12px] font-semibold px-4 py-2 rounded-xl border border-zinc-200 text-zinc-500 hover:bg-zinc-50 transition-all"
            >
              Cancelar
            </button>
            <button
              onClick={() => create.mutate()}
              disabled={create.isPending || !newId}
              className="flex items-center gap-2 text-[12px] font-semibold px-4 py-2 rounded-xl bg-[#0ABAB5] text-white hover:bg-[#089B97] transition-all disabled:opacity-60"
            >
              {create.isPending ? <SpinnerGap size={12} className="animate-spin" /> : <Plus size={12} weight="bold" />}
              {create.isPending ? 'Criando...' : 'Criar'}
            </button>
          </div>
        </div>
      )}

      {/* Instances list */}
      <div className="bg-white rounded-2xl border border-zinc-100 shadow-[0_1px_12px_rgba(0,0,0,0.06)] overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-10">
            <SpinnerGap size={24} className="animate-spin text-[#0ABAB5]" />
          </div>
        ) : instances.length === 0 ? (
          <div className="flex flex-col items-center py-10 text-zinc-300">
            <Robot size={36} weight="duotone" />
            <p className="text-sm mt-2 text-zinc-400">Nenhuma instância criada</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-100">
            {instances.map(inst => (
              <div key={inst.agent_id} className="flex items-center gap-3 px-5 py-4 hover:bg-zinc-50/60 transition-colors group">
                {/* Icon */}
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                  inst.active ? 'bg-[#0ABAB5]/10' : 'bg-zinc-100'
                }`}>
                  <Robot size={16} weight="duotone" className={inst.active ? 'text-[#0ABAB5]' : 'text-zinc-400'} />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">
                      {inst.name || inst.agent_id}
                    </p>
                    {inst.active && (
                      <span className="flex items-center gap-1 text-[10px] font-bold text-[#0ABAB5] bg-[#0ABAB5]/10 px-2 py-0.5 rounded-full">
                        <Lightning size={9} weight="fill" />
                        ATIVA
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-zinc-400 font-mono">{inst.agent_id}</p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  {!inst.active && (
                    <button
                      onClick={() => activate.mutate(inst.agent_id)}
                      disabled={activate.isPending}
                      title="Ativar esta instância"
                      className="flex items-center gap-1.5 text-[11px] font-semibold px-3 py-1.5 rounded-lg bg-[#0ABAB5]/10 text-[#0ABAB5] hover:bg-[#0ABAB5]/20 transition-all disabled:opacity-60"
                    >
                      {activate.isPending
                        ? <SpinnerGap size={11} className="animate-spin" />
                        : <Star size={11} weight="fill" />}
                      Ativar
                    </button>
                  )}
                  {!inst.active && (
                    <button
                      onClick={() => remove.mutate(inst.agent_id)}
                      disabled={remove.isPending}
                      title="Excluir instância"
                      className="p-1.5 rounded-lg text-zinc-400 hover:bg-red-50 hover:text-red-500 transition-all disabled:opacity-60"
                    >
                      <Trash size={14} weight="bold" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <p className="text-[12px] text-zinc-400 px-1">
        Cada instância pode ter personalidade, documentos RAG e número de WhatsApp próprios. Ative a instância principal para gerenciar sua configuração na aba Personalidade.
      </p>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AgentConfigPage() {
  const [tab, setTab] = useState<Tab>('whatsapp')

  const { data: numbers = [] } = useQuery<WhatsAppNumber[]>({
    queryKey: ['whatsapp-numbers'],
    queryFn: whatsappApi.listNumbers,
    refetchInterval: 10000,
  })

  // If ANY number is connected, consider the overall system online for the header indicator
  const isConnected = numbers.some(n => n.status === 'connected')

  const TABS: { key: Tab; label: string }[] = [
    { key: 'whatsapp',      label: 'WhatsApp'      },
    { key: 'instancias',    label: 'Instâncias'    },
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

      {tab === 'whatsapp'      && <WhatsAppTab />}
      {tab === 'instancias'    && <InstanciasTab />}
      {tab === 'personalidade' && <PersonalidadeTab />}
      {tab === 'rag'           && <RagTab />}
    </div>
  )
}

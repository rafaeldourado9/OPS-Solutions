import { useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  CloudArrowUp, FileDoc, Trash, SpinnerGap, X,
  DownloadSimple, FilePdf, Plus, Warning, CheckCircle,
} from '@phosphor-icons/react'
import { contractTemplatesApi, type ContractTemplate } from '../../api/contractTemplates'

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const d = Math.floor(diff / 86400000)
  if (d === 0) return 'hoje'
  if (d === 1) return 'há 1 dia'
  if (d < 7) return `há ${d} dias`
  if (d < 14) return 'há 1 semana'
  if (d < 30) return `há ${Math.floor(d / 7)} semanas`
  if (d < 60) return 'há 1 mês'
  return `há ${Math.floor(d / 30)} meses`
}

// ── Upload Area ───────────────────────────────────────────────────────────────

interface UploadAreaProps {
  onUpload: (file: File, name: string) => void
  uploading: boolean
}

function UploadArea({ onUpload, uploading }: UploadAreaProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [nameInput, setNameInput] = useState('')
  const [pendingFile, setPendingFile] = useState<File | null>(null)

  function handleFile(file: File) {
    setPendingFile(file)
    setNameInput(file.name.replace(/\.docx$/i, ''))
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file && file.name.endsWith('.docx')) handleFile(file)
  }

  function handleSubmit() {
    if (!pendingFile || !nameInput.trim()) return
    onUpload(pendingFile, nameInput.trim())
    setPendingFile(null)
    setNameInput('')
  }

  return (
    <div className="space-y-3">
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !pendingFile && inputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all
          ${dragging ? 'border-[#0ABAB5] bg-[#F0FEFE]' : 'border-zinc-200 hover:border-[#0ABAB5]/50 hover:bg-zinc-50'}
          ${pendingFile ? 'cursor-default' : ''}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".docx"
          className="hidden"
          onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
        />
        {pendingFile ? (
          <div className="flex items-center justify-center gap-3">
            <FileDoc size={24} weight="duotone" className="text-[#0ABAB5]" />
            <span className="text-[14px] font-medium text-[#1D1D1F]">{pendingFile.name}</span>
            <button onClick={e => { e.stopPropagation(); setPendingFile(null); setNameInput('') }}
              className="text-zinc-400 hover:text-zinc-600 transition-colors">
              <X size={14} weight="bold" />
            </button>
          </div>
        ) : (
          <>
            <CloudArrowUp size={36} weight="duotone" className="mx-auto text-zinc-300 mb-3" />
            <p className="text-[14px] font-semibold text-zinc-600">Arraste um arquivo DOCX ou clique para selecionar</p>
            <p className="text-[12px] text-zinc-400 mt-1">Templates de contrato com variáveis <code className="bg-zinc-100 px-1 rounded">{'{nome_variavel}'}</code></p>
          </>
        )}
      </div>

      {pendingFile && (
        <div className="flex items-center gap-2">
          <input
            value={nameInput}
            onChange={e => setNameInput(e.target.value)}
            placeholder="Nome do template..."
            className="flex-1 text-[13px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all"
          />
          <button
            onClick={handleSubmit}
            disabled={!nameInput.trim() || uploading}
            className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#09a8a3] disabled:opacity-50 text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95"
          >
            {uploading ? <SpinnerGap size={14} className="animate-spin" /> : <Plus size={14} weight="bold" />}
            Salvar Template
          </button>
        </div>
      )}
    </div>
  )
}

// ── Fill Contract Modal ────────────────────────────────────────────────────────

interface FillModalProps {
  template: ContractTemplate
  onClose: () => void
}

function FillModal({ template, onClose }: FillModalProps) {
  const [values, setValues] = useState<Record<string, string>>(
    () => Object.fromEntries(template.variables.map(v => [v, '']))
  )
  const [customKey, setCustomKey] = useState('')
  const [customVal, setCustomVal] = useState('')
  const [customVars, setCustomVars] = useState<Array<{ key: string; value: string }>>([])
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string>('')

  function setValue(key: string, val: string) {
    setValues(prev => ({ ...prev, [key]: val }))
  }

  function addCustomVar() {
    const k = customKey.trim()
    const v = customVal.trim()
    if (!k) return
    setCustomVars(prev => [...prev, { key: k, value: v }])
    setCustomKey('')
    setCustomVal('')
  }

  async function handleGenerate() {
    setGenerating(true)
    setError('')
    try {
      const allValues: Record<string, string> = { ...values }
      for (const cv of customVars) allValues[cv.key] = cv.value
      const data = await contractTemplatesApi.generate(template.id, allValues)
      const blob = new Blob([data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `contrato-${template.name}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      onClose()
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erro ao gerar contrato.')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100 shrink-0">
          <div>
            <h2 className="text-[15px] font-bold text-[#1D1D1F]">Preencher Contrato</h2>
            <p className="text-[12px] text-zinc-400 mt-0.5">{template.name} · {template.variables.length} variáveis</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-400 transition-colors">
            <X size={16} weight="bold" />
          </button>
        </div>

        <div className="overflow-y-auto p-5 space-y-4 flex-1">
          {template.variables.length === 0 ? (
            <div className="text-center py-4 text-zinc-400">
              <p className="text-[13px]">Este template não possui variáveis detectadas.</p>
              <p className="text-[12px] mt-1">Adicione variáveis customizadas abaixo se necessário.</p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-[12px] font-semibold text-zinc-500 uppercase tracking-wide">Variáveis do Template</p>
              {template.variables.map(v => (
                <div key={v} className="flex items-center gap-3">
                  <div className="w-36 shrink-0">
                    <code className="text-[12px] bg-zinc-100 text-zinc-600 px-2 py-1 rounded-lg block truncate">{'{' + v + '}'}</code>
                  </div>
                  <input
                    value={values[v] ?? ''}
                    onChange={e => setValue(v, e.target.value)}
                    placeholder={`Valor para ${v}...`}
                    className="flex-1 text-[13px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all"
                  />
                </div>
              ))}
            </div>
          )}

          {/* Custom variables */}
          <div className="space-y-3 pt-2">
            <p className="text-[12px] font-semibold text-zinc-500 uppercase tracking-wide">Variáveis Adicionais</p>
            {customVars.map((cv, i) => (
              <div key={i} className="flex items-center gap-2">
                <code className="text-[12px] bg-zinc-100 text-zinc-600 px-2 py-1 rounded-lg w-36 shrink-0 truncate">{'{' + cv.key + '}'}</code>
                <span className="text-[13px] text-zinc-600 flex-1 truncate">{cv.value || <em className="text-zinc-400">vazio</em>}</span>
                <button onClick={() => setCustomVars(prev => prev.filter((_, j) => j !== i))}
                  className="text-zinc-400 hover:text-red-500 transition-colors">
                  <X size={13} weight="bold" />
                </button>
              </div>
            ))}
            <div className="flex items-center gap-2">
              <input
                value={customKey}
                onChange={e => setCustomKey(e.target.value)}
                placeholder="nome_variavel"
                className="w-36 shrink-0 text-[13px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all"
              />
              <input
                value={customVal}
                onChange={e => setCustomVal(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addCustomVar()}
                placeholder="Valor..."
                className="flex-1 text-[13px] border border-zinc-200 rounded-xl px-3 py-2 outline-none focus:border-[#0ABAB5] focus:ring-2 focus:ring-[#0ABAB5]/20 transition-all"
              />
              <button onClick={addCustomVar} disabled={!customKey.trim()}
                className="shrink-0 p-2 bg-zinc-100 hover:bg-zinc-200 disabled:opacity-50 rounded-xl transition-colors">
                <Plus size={14} weight="bold" />
              </button>
            </div>
          </div>

          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 rounded-xl border border-red-100">
              <Warning size={14} className="text-red-500 shrink-0 mt-0.5" />
              <p className="text-[12px] text-red-600">{error}</p>
            </div>
          )}
        </div>

        <div className="px-5 pb-5 pt-3 border-t border-zinc-100 flex items-center gap-2 shrink-0">
          <button onClick={onClose}
            className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
            Cancelar
          </button>
          <button onClick={handleGenerate} disabled={generating}
            className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] disabled:opacity-50 py-2.5 rounded-xl transition-colors">
            {generating ? <SpinnerGap size={14} className="animate-spin" /> : <FilePdf size={14} weight="bold" />}
            Gerar Contrato PDF
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function TemplatesPage() {
  const queryClient = useQueryClient()
  const [fillTarget, setFillTarget] = useState<ContractTemplate | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<ContractTemplate | null>(null)
  const [uploadSuccess, setUploadSuccess] = useState(false)

  const { data: templates = [], isLoading } = useQuery<ContractTemplate[]>({
    queryKey: ['contract-templates'],
    queryFn: () => contractTemplatesApi.list(),
  })

  const uploadMutation = useMutation({
    mutationFn: ({ file, name }: { file: File; name: string }) =>
      contractTemplatesApi.upload(file, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contract-templates'] })
      setUploadSuccess(true)
      setTimeout(() => setUploadSuccess(false), 3000)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => contractTemplatesApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contract-templates'] })
      setDeleteTarget(null)
    },
  })

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-bold text-[#1D1D1F]">Gerador de Contratos</h1>
          <p className="text-[13px] text-zinc-400 mt-0.5">
            Faça upload de templates DOCX com variáveis e gere contratos em PDF
          </p>
        </div>
      </div>

      {/* Upload area */}
      <div className="bg-white rounded-2xl border border-zinc-100 shadow-sm p-5">
        <p className="text-[13px] font-semibold text-zinc-600 mb-3">Novo Template</p>
        <UploadArea
          onUpload={(file, name) => uploadMutation.mutate({ file, name })}
          uploading={uploadMutation.isPending}
        />
        {uploadSuccess && (
          <div className="flex items-center gap-2 mt-3 p-3 bg-emerald-50 rounded-xl border border-emerald-100">
            <CheckCircle size={15} weight="fill" className="text-emerald-500 shrink-0" />
            <p className="text-[13px] font-semibold text-emerald-700">Template salvo com sucesso!</p>
          </div>
        )}
        {uploadMutation.isError && (
          <div className="flex items-start gap-2 mt-3 p-3 bg-red-50 rounded-xl border border-red-100">
            <Warning size={14} className="text-red-500 shrink-0 mt-0.5" />
            <p className="text-[12px] text-red-600">
              {(uploadMutation.error as any)?.response?.data?.detail || 'Erro ao fazer upload.'}
            </p>
          </div>
        )}
      </div>

      {/* Templates list */}
      <div className="bg-white rounded-2xl border border-zinc-100 shadow-sm">
        <div className="px-5 py-4 border-b border-zinc-100">
          <p className="text-[14px] font-semibold text-[#1D1D1F]">
            Templates Salvos
            {templates.length > 0 && (
              <span className="ml-2 text-[12px] font-normal text-zinc-400">{templates.length} template{templates.length !== 1 ? 's' : ''}</span>
            )}
          </p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <SpinnerGap size={24} className="animate-spin text-[#0ABAB5]" />
          </div>
        ) : templates.length === 0 ? (
          <div className="text-center py-12 text-zinc-400">
            <FileDoc size={36} weight="duotone" className="mx-auto mb-3 opacity-50" />
            <p className="text-[13px] font-medium text-zinc-600">Nenhum template cadastrado</p>
            <p className="text-[12px] mt-1">Faça upload de um arquivo DOCX para começar</p>
          </div>
        ) : (
          <ul className="divide-y divide-zinc-100">
            {templates.map(t => (
              <li key={t.id} className="flex items-center gap-4 px-5 py-4 hover:bg-zinc-50/50 transition-colors">
                <div className="w-9 h-9 rounded-xl bg-[#F0FEFE] flex items-center justify-center shrink-0">
                  <FileDoc size={18} weight="duotone" className="text-[#0ABAB5]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[14px] font-semibold text-[#1D1D1F] truncate">{t.name}</p>
                  <p className="text-[12px] text-zinc-400 mt-0.5">
                    {t.variables.length} variáv{t.variables.length !== 1 ? 'eis' : 'el'} · {timeAgo(t.created_at)}
                  </p>
                  {t.variables.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {t.variables.slice(0, 5).map(v => (
                        <code key={v} className="text-[10px] bg-zinc-100 text-zinc-500 px-1.5 py-0.5 rounded">
                          {'{' + v + '}'}
                        </code>
                      ))}
                      {t.variables.length > 5 && (
                        <span className="text-[10px] text-zinc-400">+{t.variables.length - 5}</span>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => setFillTarget(t)}
                    className="flex items-center gap-1.5 text-[12px] font-semibold text-[#0ABAB5] border border-[#0ABAB5]/30 hover:bg-[#0ABAB5]/5 px-3 py-1.5 rounded-xl transition-colors"
                  >
                    <DownloadSimple size={13} weight="bold" /> Gerar PDF
                  </button>
                  <button
                    onClick={() => setDeleteTarget(t)}
                    className="p-2 text-zinc-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-colors"
                  >
                    <Trash size={14} weight="bold" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Fill modal */}
      {fillTarget && (
        <FillModal template={fillTarget} onClose={() => setFillTarget(null)} />
      )}

      {/* Delete confirm */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
          onClick={() => setDeleteTarget(null)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-[15px] font-bold text-[#1D1D1F] mb-1">Excluir Template</h3>
            <p className="text-[13px] text-zinc-500 mb-5">
              Tem certeza que deseja excluir <strong>{deleteTarget.name}</strong>? Esta ação não pode ser desfeita.
            </p>
            <div className="flex gap-2">
              <button onClick={() => setDeleteTarget(null)}
                className="flex-1 text-[13px] font-semibold text-zinc-500 border border-zinc-200 py-2.5 rounded-xl hover:bg-zinc-50 transition-colors">
                Cancelar
              </button>
              <button
                onClick={() => deleteMutation.mutate(deleteTarget.id)}
                disabled={deleteMutation.isPending}
                className="flex-1 flex items-center justify-center gap-2 text-[13px] font-semibold text-white bg-red-500 hover:bg-red-600 disabled:opacity-50 py-2.5 rounded-xl transition-colors"
              >
                {deleteMutation.isPending ? <SpinnerGap size={14} className="animate-spin" /> : <Trash size={13} weight="bold" />}
                Excluir
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

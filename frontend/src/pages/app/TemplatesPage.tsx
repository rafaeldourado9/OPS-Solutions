import { useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CloudArrowUp, FileDoc, Trash, PencilSimple, Play, SpinnerGap, WarningCircle } from '@phosphor-icons/react'
import { templatesApi, type QuoteTemplate } from '../../api/templates'

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

export default function TemplatesPage() {
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [uploadError, setUploadError] = useState('')

  const { data: templates = [], isLoading, isError } = useQuery({
    queryKey: ['templates'],
    queryFn: templatesApi.list,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => templatesApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['templates'] }),
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => templatesApi.upload(file),
    onSuccess: () => {
      setUploadError('')
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
    onError: (err: any) => {
      setUploadError(err?.response?.data?.detail || 'Erro ao fazer upload.')
    },
  })

  function handleFiles(files: FileList | null) {
    if (!files?.length) return
    const file = files[0]
    if (!file.name.endsWith('.docx')) {
      setUploadError('Apenas arquivos .docx são aceitos.')
      return
    }
    setUploadError('')
    uploadMutation.mutate(file)
  }

  const totalPlaceholders = templates.reduce((s: number, t: QuoteTemplate) => s + t.placeholders.length, 0)
  const lastUpload = templates.length
    ? timeAgo(templates.slice().sort((a: QuoteTemplate, b: QuoteTemplate) => b.created_at.localeCompare(a.created_at))[0].created_at)
    : '—'

  return (
    <div className="p-4 md:p-6 space-y-5 pb-6">

      {/* Hidden file input */}
      <input
        ref={fileRef}
        type="file"
        accept=".docx"
        className="hidden"
        onChange={e => handleFiles(e.target.files)}
      />

      {/* Sticky header */}
      <div className="sticky top-0 z-10 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-white/80 backdrop-blur-sm border-b border-zinc-100 flex items-center justify-between">
        <h1 className="text-xl font-bold text-[#1D1D1F] tracking-tight">Templates</h1>
        <button
          onClick={() => fileRef.current?.click()}
          className="flex items-center gap-2 bg-[#0ABAB5] hover:bg-[#09a8a3] text-white text-[13px] font-semibold px-4 py-2 rounded-xl transition-all active:scale-95"
        >
          <CloudArrowUp size={15} weight="bold" />
          <span className="hidden sm:inline">Upload Template</span>
          <span className="sm:hidden">Upload</span>
        </button>
      </div>

      <p className="text-[13px] text-zinc-500 leading-relaxed">
        Faça upload de documentos DOCX com placeholders para gerar propostas automaticamente.
      </p>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-[#0ABAB5]/10 flex items-center justify-center mb-3">
            <FileDoc size={16} weight="duotone" className="text-[#0ABAB5]" />
          </div>
          <p className="text-xl font-bold text-[#1D1D1F] font-mono">{templates.length}</p>
          <p className="text-[11px] text-zinc-400 mt-0.5">Templates Ativos</p>
        </div>
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-violet-50 flex items-center justify-center mb-3">
            <span className="text-[13px] font-bold text-violet-500">{'{}'}</span>
          </div>
          <p className="text-xl font-bold text-[#1D1D1F] font-mono">{totalPlaceholders}</p>
          <p className="text-[11px] text-zinc-400 mt-0.5">Placeholders Detectados</p>
        </div>
        <div className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-4 md:p-5">
          <div className="w-8 h-8 rounded-xl bg-blue-50 flex items-center justify-center mb-3">
            <CloudArrowUp size={16} weight="duotone" className="text-blue-500" />
          </div>
          <p className="text-[15px] font-bold text-[#1D1D1F] font-mono leading-snug">{lastUpload}</p>
          <p className="text-[11px] text-zinc-400 mt-0.5">Último Upload</p>
        </div>
      </div>

      {/* Upload zone */}
      <div
        onClick={() => fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files) }}
        className={`flex flex-col items-center justify-center gap-3 p-8 rounded-2xl border-2 border-dashed cursor-pointer transition-all ${
          dragging
            ? 'border-[#0ABAB5] bg-[#0ABAB5]/5'
            : 'border-zinc-200 bg-zinc-50/60 hover:border-[#0ABAB5]/50 hover:bg-[#0ABAB5]/3'
        }`}
      >
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-colors ${
          dragging ? 'bg-[#0ABAB5]/15' : 'bg-white border border-zinc-200'
        }`}>
          {uploadMutation.isPending
            ? <SpinnerGap size={22} className="text-[#0ABAB5] animate-spin" />
            : <CloudArrowUp size={22} weight="duotone" className={dragging ? 'text-[#0ABAB5]' : 'text-zinc-400'} />
          }
        </div>
        <div className="text-center">
          <p className={`text-[13px] font-semibold ${dragging ? 'text-[#0ABAB5]' : 'text-[#1D1D1F]'}`}>
            {uploadMutation.isPending ? 'Enviando...' : 'Arraste um arquivo .docx aqui ou clique para selecionar'}
          </p>
          <p className="text-[12px] text-zinc-400 mt-1">Suporte a arquivos DOCX até 10 MB</p>
        </div>
        {!uploadMutation.isPending && (
          <span className="text-[12px] font-semibold text-[#0ABAB5] border border-[#0ABAB5]/30 bg-white px-4 py-1.5 rounded-xl">
            Selecionar arquivo
          </span>
        )}
      </div>

      {/* Upload error */}
      {uploadError && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
          <WarningCircle size={15} className="text-red-500 shrink-0" />
          <p className="text-[13px] text-red-600">{uploadError}</p>
        </div>
      )}

      {/* Templates list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <SpinnerGap size={28} className="text-[#0ABAB5] animate-spin" />
        </div>
      ) : isError ? (
        <div className="flex flex-col items-center py-12 text-zinc-400 gap-2">
          <WarningCircle size={32} weight="duotone" className="text-red-400" />
          <p className="text-[13px]">Erro ao carregar templates</p>
        </div>
      ) : templates.length === 0 ? (
        <div className="flex flex-col items-center py-12 text-zinc-300 gap-2">
          <FileDoc size={40} weight="duotone" />
          <p className="text-[13px] text-zinc-400">Nenhum template cadastrado. Faça upload de um arquivo .docx</p>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between px-1">
            <p className="text-[12px] font-semibold text-zinc-400 uppercase tracking-wide">Meus Templates</p>
            <p className="text-[12px] text-zinc-400">{templates.length} arquivo{templates.length !== 1 ? 's' : ''}</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((t: QuoteTemplate) => (
              <div
                key={t.id}
                className="bg-white rounded-2xl shadow-[0_1px_12px_rgba(0,0,0,0.06)] border border-zinc-100/60 p-5 flex flex-col gap-3 group hover:shadow-[0_4px_20px_rgba(10,186,181,0.10)] hover:border-[#0ABAB5]/30 transition-all"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[#0ABAB5]/10 flex items-center justify-center shrink-0">
                    <FileDoc size={20} weight="duotone" className="text-[#0ABAB5]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[14px] font-bold text-[#1D1D1F] leading-snug truncate">{t.name}</p>
                    <p className="text-[11px] text-zinc-400 mt-0.5">{timeAgo(t.created_at)}</p>
                  </div>
                </div>

                <span className="bg-[#0ABAB5]/10 text-[#0ABAB5] text-[11px] font-semibold px-2 py-0.5 rounded-full w-fit">
                  {t.placeholders.length} placeholder{t.placeholders.length !== 1 ? 's' : ''}
                </span>

                {t.placeholders.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {t.placeholders.slice(0, 4).map(p => (
                      <span key={p} className="text-[10px] bg-zinc-100 text-zinc-500 px-1.5 py-0.5 rounded font-mono">{`{${p}}`}</span>
                    ))}
                    {t.placeholders.length > 4 && (
                      <span className="text-[10px] text-zinc-400">+{t.placeholders.length - 4}</span>
                    )}
                  </div>
                )}

                <div className="flex items-center gap-2 pt-1 border-t border-zinc-100">
                  <button className="flex-1 flex items-center justify-center gap-1.5 text-[12px] font-semibold text-white bg-[#0ABAB5] hover:bg-[#09a8a3] py-1.5 rounded-xl transition-colors">
                    <Play size={12} weight="fill" />
                    Usar
                  </button>
                  <button className="p-2 rounded-xl hover:bg-zinc-100 text-zinc-400 transition-colors" title="Editar">
                    <PencilSimple size={14} weight="bold" />
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(t.id)}
                    disabled={deleteMutation.isPending}
                    className="p-2 rounded-xl hover:bg-red-50 text-zinc-400 hover:text-red-500 transition-colors disabled:opacity-50"
                    title="Excluir"
                  >
                    {deleteMutation.isPending
                      ? <SpinnerGap size={14} className="animate-spin" />
                      : <Trash size={14} weight="bold" />
                    }
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

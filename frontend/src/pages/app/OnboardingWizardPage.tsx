import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowRight, ArrowLeft, Check, Robot, Key,
  WhatsappLogo, SpinnerGap, Eye, EyeSlash,
  Buildings, IdentificationBadge,
} from '@phosphor-icons/react'
import { useAuthStore } from '../../store/authStore'
import { settingsApi } from '../../api/settings'
import { agentsApi } from '../../api/agents'
import toast from 'react-hot-toast'

const STEPS = [
  { id: 'profile', label: 'Perfil' },
  { id: 'agent',   label: 'Agente' },
  { id: 'whatsapp', label: 'WhatsApp' },
]

export default function OnboardingWizardPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { tenant } = useAuthStore()

  const [step, setStep] = useState(0)

  // Step 0 — Profile
  const companyNameRef = useRef<HTMLInputElement>(null)
  const companyPhoneRef = useRef<HTMLInputElement>(null)

  // Step 1 — Agent
  const [agentName, setAgentName] = useState('')
  const [persona, setPersona] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [geminiKey, setGeminiKey] = useState('')

  // ── Mutations ──────────────────────────────────────────────────────────────
  const saveCompany = useMutation({
    mutationFn: async () => {
      const name = companyNameRef.current?.value?.trim()
      if (name && name !== tenant?.name) {
        await settingsApi.updateTenant({ name })
      }
      await settingsApi.updateCompany({
        phone: companyPhoneRef.current?.value || '',
      })
    },
    onSuccess: () => advance(),
    onError: () => advance(), // non-blocking: proceed even if phone save fails
  })

  const createAgentAndSaveKey = useMutation({
    mutationFn: async () => {
      // 1. Save Gemini key
      await settingsApi.updateIntegrations({ gemini_api_key: geminiKey })

      // 2. Create agent instance
      const id = (agentName || tenant?.name || 'agente')
        .toLowerCase()
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        .slice(0, 30) || 'agente'

      await agentsApi.createInstance({
        agent_id: id,
        name: agentName || tenant?.name || 'Assistente',
        company: companyNameRef.current?.value || tenant?.name || '',
      })

      // 3. Set persona on the agent config
      if (persona.trim()) {
        await agentsApi.updateConfig({
          agent: {
            persona: persona.trim(),
            company: companyNameRef.current?.value || tenant?.name || '',
          },
        }).catch(() => {}) // non-critical
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agent-instances'] })
      advance()
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail
      toast.error(typeof msg === 'string' ? msg : 'Erro ao criar agente')
    },
  })

  // ── Navigation ─────────────────────────────────────────────────────────────
  function advance() { setStep(s => Math.min(s + 1, STEPS.length - 1)) }
  function back()    { setStep(s => Math.max(s - 1, 0)) }

  function handleNext() {
    if (step === 0) {
      const name = companyNameRef.current?.value?.trim()
      if (!name) { toast.error('Informe o nome da empresa'); return }
      saveCompany.mutate()
    } else if (step === 1) {
      if (!agentName.trim()) { toast.error('Dê um nome ao seu assistente'); return }
      if (!persona.trim()) { toast.error('Descreva como o agente deve se comportar'); return }
      if (!geminiKey.trim()) { toast.error('A chave Gemini é necessária para ativar o assistente'); return }
      createAgentAndSaveKey.mutate()
    } else if (step === 2) {
      if (tenant?.id) localStorage.setItem(`onboarding_${tenant.id}`, 'done')
      navigate('/app/dashboard', { replace: true })
    }
  }

  function skipToApp() {
    if (tenant?.id) localStorage.setItem(`onboarding_${tenant.id}`, 'done')
    navigate('/app/dashboard', { replace: true })
  }

  const stepDone = (i: number) => i < step
  const isPending = saveCompany.isPending || createAgentAndSaveKey.isPending
  const progress = ((step) / (STEPS.length - 1)) * 100

  return (
    <div className="min-h-screen bg-[#FAFAFA] flex flex-col">

      {/* ── Header ───────────────────────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-zinc-100 bg-white">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#0ABAB5] flex items-center justify-center">
            <Robot size={16} weight="fill" className="text-white" />
          </div>
          <span className="text-sm font-semibold text-zinc-800 tracking-tight">Configuração inicial</span>
        </div>

        {/* Step pills */}
        <div className="hidden md:flex items-center gap-1.5">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center gap-1.5">
              <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all ${
                i === step
                  ? 'bg-zinc-900 text-white'
                  : stepDone(i)
                    ? 'bg-[#0ABAB5]/10 text-[#0ABAB5]'
                    : 'text-zinc-400'
              }`}>
                {stepDone(i)
                  ? <Check size={10} weight="bold" />
                  : <span className="w-3.5 h-3.5 rounded-full border border-current flex items-center justify-center text-[9px]">{i + 1}</span>
                }
                {s.label}
              </div>
              {i < STEPS.length - 1 && (
                <div className={`w-4 h-px ${stepDone(i) ? 'bg-[#0ABAB5]/40' : 'bg-zinc-200'}`} />
              )}
            </div>
          ))}
        </div>

        <button
          onClick={skipToApp}
          className="text-xs text-zinc-400 hover:text-zinc-600 transition-colors"
        >
          Pular configuração
        </button>
      </header>

      {/* ── Progress bar ─────────────────────────────────────────────────────── */}
      <div className="h-0.5 bg-zinc-100">
        <div
          className="h-full bg-[#0ABAB5] transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* ── Content ──────────────────────────────────────────────────────────── */}
      <main className="flex-1 flex items-start justify-center px-6 py-12">
        <div className="w-full max-w-2xl">

          {/* STEP 0 — Profile */}
          {step === 0 && (
            <div>
              <div className="mb-8">
                <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-widest mb-2">Passo 1 de 3</p>
                <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Perfil da empresa</h1>
                <p className="text-sm text-zinc-500 mt-1.5">Informações básicas que o assistente usará ao se apresentar.</p>
              </div>

              <div className="bg-white rounded-2xl border border-zinc-200 p-6 space-y-5">
                <div className="flex items-center gap-3 p-3 rounded-xl bg-zinc-50 border border-zinc-100">
                  <div className="w-7 h-7 rounded-lg bg-[#0ABAB5]/10 flex items-center justify-center text-[#0ABAB5] shrink-0">
                    <Buildings size={16} weight="duotone" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-zinc-700">Dados da empresa</p>
                    <p className="text-[11px] text-zinc-400">O assistente se apresentará usando essas informações</p>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-600 mb-1.5">Nome da empresa</label>
                  <input
                    ref={companyNameRef}
                    type="text"
                    defaultValue={tenant?.name ?? ''}
                    placeholder="Minha Empresa Ltda"
                    className="w-full border border-zinc-200 rounded-xl px-4 py-2.5 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/30 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-600 mb-1.5">
                    Telefone <span className="text-zinc-400 font-normal">(opcional)</span>
                  </label>
                  <input
                    ref={companyPhoneRef}
                    type="tel"
                    placeholder="(11) 99999-9999"
                    className="w-full border border-zinc-200 rounded-xl px-4 py-2.5 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/30 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400"
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 1 — Agent + Gemini Key */}
          {step === 1 && (
            <div>
              <div className="mb-8">
                <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-widest mb-2">Passo 2 de 3</p>
                <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Crie seu agente</h1>
                <p className="text-sm text-zinc-500 mt-1.5">Configure a identidade e o comportamento do seu assistente de IA.</p>
              </div>

              <div className="bg-white rounded-2xl border border-zinc-200 p-6 space-y-5">
                <div>
                  <label className="block text-xs font-semibold text-zinc-600 mb-1.5">Nome do assistente</label>
                  <input
                    type="text"
                    value={agentName}
                    onChange={e => setAgentName(e.target.value)}
                    placeholder="Sofia, Carlos, Ana, Max..."
                    className="w-full border border-zinc-200 rounded-xl px-4 py-2.5 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/30 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400"
                  />
                  <p className="text-[11px] text-zinc-400 mt-1.5">Como seus clientes vão chamar o assistente.</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-600 mb-1.5">
                    <div className="flex items-center gap-1.5">
                      <IdentificationBadge size={13} weight="duotone" className="text-[#0ABAB5]" />
                      Personalidade e tipo de empresa
                    </div>
                  </label>
                  <textarea
                    value={persona}
                    onChange={e => setPersona(e.target.value)}
                    rows={6}
                    placeholder={`Descreva o tipo da sua empresa e como o assistente deve se comportar.\n\nExemplos:\n— "Somos uma clínica odontológica. O agente deve agendar consultas, confirmar horários e ser acolhedor."\n— "Vendemos energia solar. O agente deve qualificar leads, perguntar consumo mensal e apresentar propostas."\n— "Loja de roupas online. O agente ajuda com pedidos, trocas e envia promoções."`}
                    className="w-full border border-zinc-200 rounded-xl px-4 py-2.5 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/30 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400 resize-none leading-relaxed"
                  />
                  <p className="text-[11px] text-zinc-400 mt-1.5">
                    Este texto define toda a personalidade, tom e comportamento do assistente. Seja específico — você pode editar depois em <strong className="text-zinc-500">Agente IA → Personalidade</strong>.
                  </p>
                </div>

                {/* Gemini API Key */}
                <div className="pt-3 border-t border-zinc-100">
                  <div className="flex items-start gap-4 p-4 rounded-xl bg-zinc-50 border border-zinc-100 mb-4">
                    <Key size={18} weight="duotone" className="text-zinc-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs font-semibold text-zinc-700 mb-2">Como obter a chave gratuitamente:</p>
                      <ol className="space-y-1.5">
                        {[
                          'Acesse aistudio.google.com',
                          'Faça login com sua conta Google',
                          'Clique em "Get API key" → "Create API key"',
                          'Copie a chave e cole abaixo',
                        ].map((t, i) => (
                          <li key={i} className="flex items-center gap-2 text-xs text-zinc-500">
                            <span className="w-4 h-4 rounded-full bg-white border border-zinc-200 flex items-center justify-center text-[9px] font-bold text-zinc-500 shrink-0">{i + 1}</span>
                            {t}
                          </li>
                        ))}
                      </ol>
                    </div>
                  </div>

                  <label className="block text-xs font-semibold text-zinc-600 mb-1.5">Gemini API Key</label>
                  <div className="relative">
                    <input
                      type={showKey ? 'text' : 'password'}
                      value={geminiKey}
                      onChange={e => setGeminiKey(e.target.value)}
                      placeholder="AIzaSy..."
                      autoComplete="off"
                      className="w-full border border-zinc-200 rounded-xl px-4 py-2.5 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/30 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400 pr-12 font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKey(v => !v)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 transition-colors"
                    >
                      {showKey ? <EyeSlash size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                  <p className="text-[11px] text-zinc-400 mt-1.5">Armazenada com segurança no servidor. Nunca exposta no navegador.</p>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2 — WhatsApp */}
          {step === 2 && (
            <div>
              <div className="mb-8">
                <p className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-widest mb-2">Passo 3 de 3</p>
                <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Conecte o WhatsApp</h1>
                <p className="text-sm text-zinc-500 mt-1.5">Escaneie o QR Code para ativar o assistente no seu número.</p>
              </div>

              <div className="bg-white rounded-2xl border border-zinc-200 p-6 space-y-5">
                <div className="flex items-start gap-4 p-4 rounded-xl bg-emerald-50 border border-emerald-100">
                  <WhatsappLogo size={18} weight="fill" className="text-emerald-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-semibold text-zinc-700 mb-2">Como conectar:</p>
                    <ol className="space-y-1.5">
                      {[
                        'Vá para "Configurações > Agente IA > WhatsApp"',
                        'Clique em "Adicionar Número"',
                        'Abra o WhatsApp no celular e toque em "Aparelhos conectados"',
                        'Aguarde gerar o QR Code e escaneie-o',
                      ].map((t, i) => (
                        <li key={i} className="flex items-center gap-2 text-xs text-zinc-500">
                          <span className="w-4 h-4 rounded-full bg-white border border-emerald-200 flex items-center justify-center text-[9px] font-bold text-emerald-600 shrink-0">{i + 1}</span>
                          {t}
                        </li>
                      ))}
                    </ol>
                  </div>
                </div>

                <p className="text-xs text-zinc-400 text-center">
                  Prefere conectar depois? Vá em <strong className="text-zinc-500">Agente IA → WhatsApp</strong>
                </p>
              </div>
            </div>
          )}

          {/* ── Action buttons ──────────────────────────────────────────────── */}
          <div className="mt-6 flex items-center justify-between">
            {step > 0 ? (
              <button
                onClick={back}
                disabled={isPending}
                className="flex items-center gap-1.5 text-sm font-medium text-zinc-400 hover:text-zinc-700 transition-colors disabled:opacity-40"
              >
                <ArrowLeft size={14} weight="bold" />
                Voltar
              </button>
            ) : <div />}

            <button
              onClick={handleNext}
              disabled={isPending}
              className="flex items-center gap-2 bg-zinc-900 hover:bg-zinc-700 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-all active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? (
                <>
                  <SpinnerGap size={15} className="animate-spin" />
                  {step === 0 ? 'Salvando...' : step === 1 ? 'Criando agente...' : 'Aguarde...'}
                </>
              ) : step === 2 ? (
                <>
                  <Check size={15} weight="bold" />
                  Ir para o painel
                </>
              ) : (
                <>
                  Continuar
                  <ArrowRight size={15} weight="bold" />
                </>
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

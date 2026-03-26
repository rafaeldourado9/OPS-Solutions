import { useState } from 'react'
import { ArrowRight, CheckCircle, SpinnerGap, WarningCircle } from '@phosphor-icons/react'

type FormState = 'idle' | 'loading' | 'success' | 'error' | 'duplicate'

export default function CTA() {
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [formState, setFormState] = useState<FormState>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) return
    setFormState('loading')

    try {
      const res = await fetch('/api/v1/public/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, plan: '', source: 'landing_cta' }),
      })

      if (res.ok) {
        setFormState('success')
      } else if (res.status === 409) {
        setFormState('duplicate')
      } else {
        const data = await res.json().catch(() => ({}))
        setErrorMsg(data.detail ?? 'Erro ao cadastrar. Tente novamente.')
        setFormState('error')
      }
    } catch {
      setErrorMsg('Sem conexão. Verifique sua internet e tente novamente.')
      setFormState('error')
    }
  }

  return (
    <section className="relative bg-[#0A1628] py-32 px-6 overflow-hidden">
      {/* Background orbs */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full opacity-30 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse, rgba(10,186,181,0.25) 0%, transparent 70%)', filter: 'blur(60px)' }}
      />
      <div
        className="absolute bottom-0 right-10 w-[400px] h-[300px] rounded-full opacity-20 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse, rgba(10,186,181,0.3) 0%, transparent 70%)', filter: 'blur(40px)' }}
      />

      <div className="max-w-2xl mx-auto text-center relative">
        <div className="fade-in">
          {/* Beta badge */}
          <div className="inline-flex items-center gap-2 bg-[#0ABAB5]/10 border border-[#0ABAB5]/30 rounded-full px-4 py-1.5 mb-8">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#0ABAB5] opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[#0ABAB5]" />
            </span>
            <span className="text-xs font-semibold text-[#0ABAB5] uppercase tracking-wide">Acesso beta aberto</span>
          </div>

          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white leading-tight mb-4">
            14 dias grátis.<br />
            <span className="text-[#0ABAB5]">Sem cartão de crédito.</span>
          </h2>
          <p className="text-lg text-zinc-400 mb-10">
            Entre na lista de beta testers e receba acesso antecipado à plataforma completa — CRM, agentes de IA e automações.
          </p>

          {/* Form */}
          {formState === 'success' ? (
            <div className="bg-[#0ABAB5]/10 border border-[#0ABAB5]/30 rounded-2xl p-8 text-center">
              <CheckCircle size={48} weight="fill" className="text-[#0ABAB5] mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">Você está na lista! 🎉</h3>
              <p className="text-zinc-400 text-sm">
                Enviamos um e-mail de confirmação para <strong className="text-white">{email}</strong>.
                <br />Entraremos em contato em até 24 horas com seu acesso.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  placeholder="Seu nome"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder:text-zinc-500 text-sm focus:outline-none focus:border-[#0ABAB5]/50 focus:ring-2 focus:ring-[#0ABAB5]/10 transition-all"
                />
                <input
                  type="email"
                  placeholder="seu@email.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder:text-zinc-500 text-sm focus:outline-none focus:border-[#0ABAB5]/50 focus:ring-2 focus:ring-[#0ABAB5]/10 transition-all"
                />
              </div>

              <button
                type="submit"
                disabled={formState === 'loading' || !email}
                className="w-full group inline-flex items-center justify-center gap-2 bg-[#0ABAB5] hover:bg-[#089B97] disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold px-8 py-4 rounded-xl text-base transition-all hover:shadow-[0_16px_48px_rgba(10,186,181,0.4)] hover:scale-[1.01] active:scale-[0.98]"
              >
                {formState === 'loading' ? (
                  <>
                    <SpinnerGap size={18} className="animate-spin" />
                    Cadastrando...
                  </>
                ) : (
                  <>
                    Quero meu acesso beta gratuito
                    <ArrowRight size={16} weight="bold" className="group-hover:translate-x-0.5 transition-transform" />
                  </>
                )}
              </button>

              {(formState === 'error' || formState === 'duplicate') && (
                <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
                  <WarningCircle size={16} className="text-red-400 shrink-0" />
                  <p className="text-sm text-red-300">
                    {formState === 'duplicate'
                      ? 'Este e-mail já está na lista de espera. 👍'
                      : errorMsg}
                  </p>
                </div>
              )}
            </form>
          )}

          <p className="text-sm text-zinc-600 mt-6">
            Sem cartão de crédito &bull; 14 dias grátis &bull; Suporte em português
          </p>
        </div>
      </div>
    </section>
  )
}

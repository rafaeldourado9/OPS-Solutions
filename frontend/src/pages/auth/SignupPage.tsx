import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { Eye, EyeSlash, ArrowLeft, Check } from '@phosphor-icons/react'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

const schema = z.object({
  user_name: z.string().min(2, 'Nome obrigatório'),
  email: z.string().email('E-mail inválido'),
  password: z.string().min(8, 'Mínimo 8 caracteres'),
  tenant_name: z.string().min(2, 'Nome da empresa obrigatório'),
  tenant_slug: z.string().min(2, 'Identificador obrigatório').regex(/^[a-z0-9-]+$/, 'Use apenas letras minúsculas, números e hífens'),
})
type FormData = z.infer<typeof schema>

const PLAN_LABELS: Record<string, string> = {
  starter: 'Starter — Grátis',
  professional: 'Professional — R$ 197/mês',
  enterprise: 'Enterprise — Sob consulta',
}

export default function SignupPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const plan = searchParams.get('plan') ?? 'starter'
  const isDemo = searchParams.get('demo') === 'true'
  const setAuth = useAuthStore(s => s.setAuth)
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { tenant_slug: '' },
  })

  // Auto-generate slug from company name
  const handleCompanyName = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setValue('tenant_name', val)
    const slug = val.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
    setValue('tenant_slug', slug)
  }

  const onSubmit = async (data: FormData) => {
    setLoading(true)
    try {
      const res = await authApi.register({ ...data, plan })
      setAuth(res.access_token, res.user, res.tenant)
      toast.success(`Conta criada! Bem-vindo, ${res.user.name.split(' ')[0]}!`)
      navigate('/app/dashboard', { replace: true })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      const msg = axiosErr.response?.data?.detail ?? 'Erro ao criar conta. Tente novamente.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[100dvh] grid grid-cols-1 lg:grid-cols-2">
      {/* Left — brand panel */}
      <div className="hidden lg:flex flex-col justify-between bg-[#0A1628] p-12">
        <Link to="/" className="flex items-center gap-2.5">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <polygon points="16,2 28,9 28,23 16,30 4,23 4,9" stroke="#0ABAB5" strokeWidth="2" fill="none"/>
            <circle cx="16" cy="16" r="3" fill="#0ABAB5"/>
            <line x1="16" y1="13" x2="16" y2="5" stroke="#0ABAB5" strokeWidth="1.5"/>
            <line x1="18.6" y1="14.5" x2="25.4" y2="10.5" stroke="#0ABAB5" strokeWidth="1.5"/>
            <line x1="18.6" y1="17.5" x2="25.4" y2="21.5" stroke="#0ABAB5" strokeWidth="1.5"/>
            <circle cx="16" cy="4.5" r="1.5" fill="#0ABAB5"/>
            <circle cx="26.5" cy="10.5" r="1.5" fill="#0ABAB5"/>
            <circle cx="26.5" cy="21.5" r="1.5" fill="#0ABAB5"/>
          </svg>
          <span className="font-semibold text-white">OPS Solutions</span>
        </Link>

        <div>
          {isDemo && (
            <div className="inline-flex items-center gap-2 bg-amber-400/15 border border-amber-400/30 rounded-full px-4 py-1.5 mb-6">
              <span className="text-xs font-medium text-amber-400">Demo agendada após o cadastro</span>
            </div>
          )}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5 mb-8">
            <p className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">Plano selecionado</p>
            <p className="text-lg font-bold text-white">{PLAN_LABELS[plan] ?? PLAN_LABELS.starter}</p>
          </div>
          <h1 className="text-4xl font-bold text-white tracking-tight leading-tight mb-4">
            Sua operação começa agora.
          </h1>
          <p className="text-zinc-400 leading-relaxed mb-8">
            Crie sua conta e tenha acesso imediato ao CRM, agentes de WhatsApp e automações.
          </p>
          <ul className="space-y-3">
            {['Setup em menos de 5 minutos', 'Sem cartão de crédito no plano Starter', 'Suporte em português incluído', 'Cancele quando quiser'].map(f => (
              <li key={f} className="flex items-center gap-2.5 text-sm text-zinc-300">
                <span className="w-5 h-5 rounded-full bg-[#0ABAB5]/20 flex items-center justify-center shrink-0">
                  <Check size={11} weight="bold" className="text-[#0ABAB5]" />
                </span>
                {f}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs text-zinc-600">© 2026 OPS Solutions. Todos os direitos reservados.</p>
      </div>

      {/* Right — form */}
      <div className="flex flex-col justify-center px-6 py-12 lg:px-16 bg-white overflow-y-auto">
        <div className="max-w-sm w-full mx-auto">
          <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-800 transition-colors mb-8 group">
            <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
            Voltar ao site
          </Link>

          <div className="mb-6">
            <h2 className="text-2xl font-bold text-[#1D1D1F] tracking-tight mb-1.5">
              {isDemo ? 'Agendar demonstração' : 'Criar conta grátis'}
            </h2>
            <p className="text-sm text-zinc-500">Preencha os dados para começar.</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">Nome completo</label>
              <input
                {...register('user_name')}
                placeholder="João Silva"
                className="w-full px-4 py-3 rounded-xl border border-zinc-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/40 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400"
              />
              {errors.user_name && <p className="text-xs text-red-500 mt-1">{errors.user_name.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">Nome da empresa</label>
              <input
                placeholder="Minha Empresa Ltda"
                onChange={handleCompanyName}
                className="w-full px-4 py-3 rounded-xl border border-zinc-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/40 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400"
              />
              {errors.tenant_name && <p className="text-xs text-red-500 mt-1">{errors.tenant_name.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                Identificador único
                <span className="text-zinc-400 font-normal ml-1">(URL do CRM)</span>
              </label>
              <div className="flex items-center border border-zinc-200 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-[#0ABAB5]/40 focus-within:border-[#0ABAB5] transition-all">
                <span className="px-3 py-3 bg-zinc-50 text-xs text-zinc-400 border-r border-zinc-200 shrink-0">ops.app/</span>
                <input
                  {...register('tenant_slug')}
                  className="flex-1 px-3 py-3 text-sm focus:outline-none placeholder:text-zinc-400"
                  placeholder="minha-empresa"
                />
              </div>
              {errors.tenant_slug && <p className="text-xs text-red-500 mt-1">{errors.tenant_slug.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">E-mail profissional</label>
              <input
                {...register('email')}
                type="email"
                placeholder="joao@empresa.com"
                className="w-full px-4 py-3 rounded-xl border border-zinc-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/40 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400"
              />
              {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">Senha</label>
              <div className="relative">
                <input
                  {...register('password')}
                  type={showPass ? 'text' : 'password'}
                  placeholder="Mínimo 8 caracteres"
                  className="w-full px-4 py-3 rounded-xl border border-zinc-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/40 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400 pr-12"
                />
                <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600">
                  {showPass ? <EyeSlash size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#0ABAB5] hover:bg-[#089B97] text-white font-semibold py-3.5 rounded-xl transition-all hover:shadow-[0_6px_24px_rgba(10,186,181,0.4)] active:scale-[0.98] disabled:opacity-60 mt-1"
            >
              {loading ? 'Criando conta...' : isDemo ? 'Criar conta e agendar demo' : 'Criar conta grátis'}
            </button>
          </form>

          <p className="text-center text-sm text-zinc-500 mt-5">
            Já tem uma conta?{' '}
            <Link to="/auth/login" className="text-[#0ABAB5] font-semibold hover:underline">Entrar</Link>
          </p>
          <p className="text-center text-xs text-zinc-400 mt-4 leading-relaxed">
            Ao criar sua conta, você concorda com os{' '}
            <a href="#" className="underline">Termos de Uso</a> e a{' '}
            <a href="#" className="underline">Política de Privacidade</a>.
          </p>
        </div>
      </div>
    </div>
  )
}

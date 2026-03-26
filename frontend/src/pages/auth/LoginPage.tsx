import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { Eye, EyeSlash, ArrowLeft } from '@phosphor-icons/react'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

const schema = z.object({
  email: z.string().email('E-mail inválido'),
  password: z.string().min(6, 'Mínimo 6 caracteres'),
})
type FormData = z.infer<typeof schema>

export default function LoginPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore(s => s.setAuth)
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setLoading(true)
    try {
      const res = await authApi.login(data)
      setAuth(res.access_token, res.user, res.tenant)
      toast.success(`Bem-vindo, ${res.user.name.split(' ')[0]}!`)
      navigate('/app/dashboard', { replace: true })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      const msg = axiosErr.response?.data?.detail ?? 'Credenciais inválidas'
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
          <div className="inline-flex items-center gap-2 bg-[#0ABAB5]/15 border border-[#0ABAB5]/30 rounded-full px-4 py-1.5 mb-8">
            <span className="w-1.5 h-1.5 bg-[#0ABAB5] rounded-full" />
            <span className="text-xs font-medium text-[#0ABAB5]">Plataforma B2B</span>
          </div>
          <h1 className="text-4xl font-bold text-white tracking-tight leading-tight mb-4">
            Bem-vindo de volta à sua operação.
          </h1>
          <p className="text-zinc-400 leading-relaxed">
            Acesse seu CRM, acompanhe leads, gerencie conversas e automatize seu negócio.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {[
            { v: '+6.000', l: 'empresas ativas' },
            { v: '99,97%', l: 'uptime' },
            { v: '+1,5bi', l: 'msgs processadas' },
            { v: '<5min', l: 'tempo de setup' },
          ].map(m => (
            <div key={m.l} className="bg-white/5 rounded-2xl p-4">
              <p className="text-xl font-bold text-white font-mono">{m.v}</p>
              <p className="text-xs text-zinc-500 mt-1">{m.l}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Right — form */}
      <div className="flex flex-col justify-center px-6 py-12 lg:px-16 bg-white">
        <div className="max-w-sm w-full mx-auto">
          <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-800 transition-colors mb-10 group">
            <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
            Voltar ao site
          </Link>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-[#1D1D1F] tracking-tight mb-1.5">Entrar na plataforma</h2>
            <p className="text-sm text-zinc-500">Digite seu e-mail e senha para continuar.</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">E-mail</label>
              <input
                {...register('email')}
                type="email"
                placeholder="voce@empresa.com"
                className="w-full px-4 py-3 rounded-xl border border-zinc-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/40 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400"
              />
              {errors.email && <p className="text-xs text-red-500 mt-1.5">{errors.email.message}</p>}
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-medium text-zinc-700">Senha</label>
                <Link to="/auth/forgot-password" className="text-xs text-[#0ABAB5] hover:underline">
                  Esqueci minha senha
                </Link>
              </div>
              <div className="relative">
                <input
                  {...register('password')}
                  type={showPass ? 'text' : 'password'}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 rounded-xl border border-zinc-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/40 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400 pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
                >
                  {showPass ? <EyeSlash size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <p className="text-xs text-red-500 mt-1.5">{errors.password.message}</p>}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#0ABAB5] hover:bg-[#089B97] text-white font-semibold py-3.5 rounded-xl transition-all hover:shadow-[0_6px_24px_rgba(10,186,181,0.4)] active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed mt-2"
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>

          <p className="text-center text-sm text-zinc-500 mt-6">
            Não tem uma conta?{' '}
            <Link to="/auth/signup" className="text-[#0ABAB5] font-semibold hover:underline">
              Criar conta grátis
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

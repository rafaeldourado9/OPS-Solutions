import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Eye, EyeSlash } from '@phosphor-icons/react'
import { authApi } from '../../api/auth'
import toast from 'react-hot-toast'

const schema = z
  .object({
    new_password: z.string().min(6, 'Mínimo 6 caracteres'),
    confirm_password: z.string(),
  })
  .refine(d => d.new_password === d.confirm_password, {
    message: 'As senhas não coincidem',
    path: ['confirm_password'],
  })
type FormData = z.infer<typeof schema>

export default function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''

  const [loading, setLoading] = useState(false)
  const [showPass, setShowPass] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  if (!token) {
    return (
      <div className="min-h-[100dvh] flex items-center justify-center bg-white px-6">
        <div className="max-w-sm w-full text-center">
          <h1 className="text-2xl font-bold text-[#1D1D1F] mb-2">Link inválido</h1>
          <p className="text-sm text-zinc-500 mb-6">Este link de recuperação é inválido ou expirou.</p>
          <Link
            to="/auth/forgot-password"
            className="inline-flex items-center justify-center w-full bg-[#0ABAB5] text-white font-semibold py-3.5 rounded-xl hover:bg-[#089B97] transition-all"
          >
            Solicitar novo link
          </Link>
        </div>
      </div>
    )
  }

  const onSubmit = async (data: FormData) => {
    setLoading(true)
    try {
      await authApi.resetPassword(token, data.new_password)
      toast.success('Senha redefinida com sucesso!')
      navigate('/auth/login', { replace: true })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: unknown } } }
      const raw = axiosErr.response?.data?.detail
      const msg = typeof raw === 'string' ? raw : 'Link inválido ou expirado.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[100dvh] flex items-center justify-center bg-white px-6">
      <div className="max-w-sm w-full">
        <h1 className="text-2xl font-bold text-[#1D1D1F] mb-1.5">Nova senha</h1>
        <p className="text-sm text-zinc-500 mb-6">Digite e confirme sua nova senha.</p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Nova senha</label>
            <div className="relative">
              <input
                {...register('new_password')}
                type={showPass ? 'text' : 'password'}
                placeholder="••••••••"
                className="w-full px-4 py-3 rounded-xl border border-zinc-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/40 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400 pr-12"
              />
              <button
                type="button"
                onClick={() => setShowPass(v => !v)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
              >
                {showPass ? <EyeSlash size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.new_password && (
              <p className="text-xs text-red-500 mt-1.5">{errors.new_password.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Confirmar senha</label>
            <div className="relative">
              <input
                {...register('confirm_password')}
                type={showConfirm ? 'text' : 'password'}
                placeholder="••••••••"
                className="w-full px-4 py-3 rounded-xl border border-zinc-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#0ABAB5]/40 focus:border-[#0ABAB5] transition-all placeholder:text-zinc-400 pr-12"
              />
              <button
                type="button"
                onClick={() => setShowConfirm(v => !v)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
              >
                {showConfirm ? <EyeSlash size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.confirm_password && (
              <p className="text-xs text-red-500 mt-1.5">{errors.confirm_password.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#0ABAB5] hover:bg-[#089B97] text-white font-semibold py-3.5 rounded-xl transition-all hover:shadow-[0_6px_24px_rgba(10,186,181,0.4)] active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed mt-2"
          >
            {loading ? 'Salvando...' : 'Redefinir senha'}
          </button>
        </form>

        <p className="text-center text-sm text-zinc-500 mt-6">
          Lembrou a senha?{' '}
          <Link to="/auth/login" className="text-[#0ABAB5] font-semibold hover:underline">
            Fazer login
          </Link>
        </p>
      </div>
    </div>
  )
}

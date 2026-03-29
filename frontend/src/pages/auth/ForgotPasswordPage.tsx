import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link } from 'react-router-dom'
import { ArrowLeft } from '@phosphor-icons/react'
import { authApi } from '../../api/auth'

const schema = z.object({
  email: z.string().email('E-mail inválido'),
})
type FormData = z.infer<typeof schema>

export default function ForgotPasswordPage() {
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setLoading(true)
    try {
      await authApi.forgotPassword(data.email)
      setSent(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[100dvh] flex items-center justify-center bg-white px-6">
      <div className="max-w-sm w-full">
        <Link
          to="/auth/login"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-800 mb-8 group"
        >
          <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
          Voltar ao login
        </Link>

        {sent ? (
          <div className="text-center">
            <div className="w-12 h-12 bg-[#0ABAB5]/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z" stroke="#0ABAB5" strokeWidth="1.5"/>
                <path d="M2 8l10 7 10-7" stroke="#0ABAB5" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-[#1D1D1F] mb-2">Verifique seu e-mail</h1>
            <p className="text-sm text-zinc-500 mb-6">
              Se o e-mail informado estiver cadastrado, você receberá um link para redefinir sua senha em breve.
            </p>
            <Link
              to="/auth/login"
              className="inline-flex items-center justify-center w-full bg-[#0ABAB5] text-white font-semibold py-3.5 rounded-xl hover:bg-[#089B97] transition-all"
            >
              Voltar ao login
            </Link>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-bold text-[#1D1D1F] mb-1.5">Recuperar senha</h1>
            <p className="text-sm text-zinc-500 mb-6">
              Informe seu e-mail e enviaremos um link para redefinir sua senha.
            </p>

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

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#0ABAB5] hover:bg-[#089B97] text-white font-semibold py-3.5 rounded-xl transition-all hover:shadow-[0_6px_24px_rgba(10,186,181,0.4)] active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loading ? 'Enviando...' : 'Enviar link'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}

import { Link } from 'react-router-dom'
import { ArrowLeft } from '@phosphor-icons/react'

export default function ForgotPasswordPage() {
  return (
    <div className="min-h-[100dvh] flex items-center justify-center bg-white px-6">
      <div className="max-w-sm w-full text-center">
        <Link to="/auth/login" className="inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-800 mb-8 group">
          <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
          Voltar ao login
        </Link>
        <h1 className="text-2xl font-bold text-[#1D1D1F] mb-2">Recuperar senha</h1>
        <p className="text-sm text-zinc-500 mb-6">Em breve disponível. Entre em contato com o suporte.</p>
        <Link to="/auth/login" className="inline-flex items-center justify-center w-full bg-[#0ABAB5] text-white font-semibold py-3.5 rounded-xl hover:bg-[#089B97] transition-all">
          Voltar ao login
        </Link>
      </div>
    </div>
  )
}

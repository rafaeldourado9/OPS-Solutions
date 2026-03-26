import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { List, X } from '@phosphor-icons/react'

export default function Header() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [scrollProgress, setScrollProgress] = useState(0)

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 20)
      const docHeight = document.body.scrollHeight - window.innerHeight
      setScrollProgress(docHeight > 0 ? (window.scrollY / docHeight) * 100 : 0)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const navLinks = ['Plataforma', 'Produtos', 'Desenvolvedores', 'Planos', 'Recursos']

  return (
    <header
      className={`fixed top-0 w-full z-50 transition-all duration-500 ease-out ${
        scrolled
          ? 'bg-white/80 backdrop-blur-2xl shadow-[0_1px_0_rgba(0,0,0,0.06),0_4px_20px_rgba(0,0,0,0.04)]'
          : 'bg-transparent'
      }`}
    >
      {/* Scroll progress line */}
      <div
        className="absolute bottom-0 left-0 h-[1.5px] bg-gradient-to-r from-[#0ABAB5] to-[#06d4ce] transition-all duration-100 ease-out"
        style={{ width: `${scrollProgress}%`, opacity: scrolled ? 1 : 0 }}
      />

      <div className="max-w-7xl mx-auto px-6 lg:px-8 h-[52px] flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="flex items-center gap-2.5 shrink-0 group">
          <img
            src="/logoo.png"
            alt="Logo"
            className="w-7 h-7 object-contain transition-transform duration-300 group-hover:scale-110"
          />
          <span className="font-semibold text-[15px] tracking-tight text-[#1D1D1F]">
            OPS Solutions
          </span>
        </a>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-0.5">
          {navLinks.map(link => (
            <a
              key={link}
              href="#"
              className="relative px-3.5 py-2 text-[13px] font-medium text-zinc-600 hover:text-[#1D1D1F] rounded-lg transition-colors duration-200 group"
            >
              {link}
              <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-0 group-hover:w-3.5 h-[1.5px] bg-[#0ABAB5] rounded-full transition-all duration-300 ease-out" />
            </a>
          ))}
        </nav>

        {/* Right actions */}
        <div className="hidden md:flex items-center gap-2.5">
          <Link
            to="/auth/login"
            className="text-[13px] font-medium text-zinc-600 hover:text-[#1D1D1F] transition-colors px-3 py-2 rounded-lg hover:bg-zinc-50"
          >
            Entrar
          </Link>
          <Link
            to="/auth/signup"
            className="btn-liquid bg-[#0ABAB5] hover:bg-[#089B97] text-white text-[13px] font-semibold px-5 py-2 rounded-full"
          >
            Teste Grátis
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 rounded-xl hover:bg-zinc-100 transition-colors"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Menu"
        >
          {mobileOpen ? <X size={19} weight="bold" /> : <List size={19} weight="bold" />}
        </button>
      </div>

      {/* Mobile panel */}
      <div
        className={`md:hidden transition-all duration-300 ease-out overflow-hidden bg-white/95 backdrop-blur-2xl border-b border-zinc-100 ${
          mobileOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-6 py-4 flex flex-col gap-1">
          {navLinks.map(link => (
            <a
              key={link}
              href="#"
              className="py-2.5 text-sm font-medium text-zinc-700 hover:text-[#0ABAB5] transition-colors"
            >
              {link}
            </a>
          ))}
          <div className="pt-3 border-t border-zinc-100 mt-2 flex flex-col gap-2">
            <Link to="/auth/login" className="text-sm font-medium text-zinc-600 py-2">Entrar</Link>
            <Link
              to="/auth/signup"
              className="bg-[#0ABAB5] text-white text-sm font-semibold px-5 py-3 rounded-full text-center"
            >
              Teste Grátis
            </Link>
          </div>
        </div>
      </div>
    </header>
  )
}

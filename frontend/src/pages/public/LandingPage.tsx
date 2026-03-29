import { useEffect } from 'react'
import Header from '../../components/layout/Header'
import Footer from '../../components/layout/Footer'
import Hero from '../../components/sections/Hero'
import TrustBar from '../../components/sections/TrustBar'
import CRMShowcase from '../../components/sections/CRMShowcase'
import WhatsAppAgents from '../../components/sections/WhatsAppAgents'
import AgentCatalog from '../../components/sections/AgentCatalog'
import Numbers from '../../components/sections/Numbers'
import Developers from '../../components/sections/Developers'
import Services from '../../components/sections/Services'
import Pricing from '../../components/sections/Pricing'
import Testimonials from '../../components/sections/Testimonials'
import CTA from '../../components/sections/CTA'

export default function LandingPage() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible') }),
      { threshold: 0.06, rootMargin: '0px 0px -40px 0px' }
    )
    const attach = () =>
      document.querySelectorAll('.fade-in:not(.visible)').forEach(el => observer.observe(el))

    attach()
    // Re-scan after images / lazy components settle
    const t = setTimeout(attach, 800)

    const handleMouseMove = (e: MouseEvent) => {
      document.querySelectorAll<HTMLElement>('.spotlight-card').forEach(card => {
        const rect = card.getBoundingClientRect()
        card.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`)
        card.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`)
      })
    }
    window.addEventListener('mousemove', handleMouseMove, { passive: true })

    return () => {
      observer.disconnect()
      clearTimeout(t)
      window.removeEventListener('mousemove', handleMouseMove)
    }
  }, [])

  return (
    <div className="min-h-[100dvh]">
      <Header />
      <main>
        <Hero />
        <TrustBar />
        <CRMShowcase />
        <WhatsAppAgents />
        <AgentCatalog />
        <Numbers />
        <Developers />
        <Services />
        <Pricing />
        <Testimonials />
        <CTA />
      </main>
      <Footer />
    </div>
  )
}

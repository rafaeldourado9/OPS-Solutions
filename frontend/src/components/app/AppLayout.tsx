import { useState, useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import BottomNav from './BottomNav'

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname])

  // Prevent body scroll when sidebar open on mobile
  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [sidebarOpen])

  return (
    <div
      className="flex min-h-[100dvh]"
      style={{ background: 'linear-gradient(145deg, #F8F9FB 0%, #F3F4F7 50%, #F7F8FA 100%)' }}
    >
      {/* Mobile overlay */}
      <div
        className={`fixed inset-0 z-40 lg:hidden transition-all duration-300 ${
          sidebarOpen
            ? 'bg-black/40 backdrop-blur-sm pointer-events-auto'
            : 'bg-transparent pointer-events-none'
        }`}
        onClick={() => setSidebarOpen(false)}
      />

      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 flex flex-col min-w-0 lg:ml-0">
        <TopBar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto page-enter pb-20 lg:pb-0">
          <Outlet />
        </main>
        {/* Mobile bottom navigation */}
        <BottomNav />
      </div>
    </div>
  )
}

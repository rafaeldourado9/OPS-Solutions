import { createBrowserRouter, Navigate } from 'react-router-dom'
import LandingPage from './pages/public/LandingPage'
import LoginPage from './pages/auth/LoginPage'
import SignupPage from './pages/auth/SignupPage'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import AppLayout from './components/app/AppLayout'
import ProtectedRoute from './components/auth/ProtectedRoute'
import DashboardPage from './pages/app/DashboardPage'
import CustomersPage from './pages/app/CustomersPage'
import LeadsPage from './pages/app/LeadsPage'
import ConversationsPage from './pages/app/ConversationsPage'
import QuotesPage from './pages/app/QuotesPage'
import PremisesPage from './pages/app/PremisesPage'
import ContractsPage from './pages/app/ContractsPage'
import InventoryPage from './pages/app/InventoryPage'
import TemplatesPage from './pages/app/TemplatesPage'
import AgentConfigPage from './pages/app/AgentConfigPage'
import SettingsPage from './pages/app/SettingsPage'

export const router = createBrowserRouter([
  // Public — landing page
  { path: '/', element: <LandingPage /> },

  // Auth
  { path: '/auth/login', element: <LoginPage /> },
  { path: '/auth/signup', element: <SignupPage /> },
  { path: '/auth/forgot-password', element: <ForgotPasswordPage /> },

  // Protected CRM app
  {
    path: '/app',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/app/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'customers', element: <CustomersPage /> },
      { path: 'leads', element: <LeadsPage /> },
      { path: 'conversations', element: <ConversationsPage /> },
      { path: 'quotes', element: <QuotesPage /> },
      { path: 'premises', element: <PremisesPage /> },
      { path: 'contracts', element: <ContractsPage /> },
      { path: 'inventory', element: <InventoryPage /> },
      { path: 'templates', element: <TemplatesPage /> },
      { path: 'agents', element: <AgentConfigPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },

  // Fallback
  { path: '*', element: <Navigate to="/" replace /> },
])

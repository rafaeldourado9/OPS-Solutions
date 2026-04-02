import { createBrowserRouter, Navigate } from 'react-router-dom'
import LoginPage from './pages/auth/LoginPage'
import SignupPage from './pages/auth/SignupPage'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import ResetPasswordPage from './pages/auth/ResetPasswordPage'
import AppLayout from './components/app/AppLayout'
import ProtectedRoute from './components/auth/ProtectedRoute'
import DashboardPage from './pages/app/DashboardPage'
import CustomersPage from './pages/app/CustomersPage'
import LeadsPage from './pages/app/LeadsPage'
import ConversationsPage from './pages/app/ConversationsPage'
import AgentConfigPage from './pages/app/AgentConfigPage'
import SettingsPage from './pages/app/SettingsPage'
import TrialExpiredPage from './pages/app/TrialExpiredPage'
import OnboardingWizardPage from './pages/app/OnboardingWizardPage'

export const router = createBrowserRouter([
  // Auth
  { path: '/', element: <Navigate to="/auth/login" replace /> },
  { path: '/auth/login', element: <LoginPage /> },
  { path: '/auth/signup', element: <SignupPage /> },
  { path: '/auth/forgot-password', element: <ForgotPasswordPage /> },
  { path: '/auth/reset-password', element: <ResetPasswordPage /> },

  // Trial expired paywall — outside ProtectedRoute so expired users can reach it
  { path: '/app/trial-expired', element: <TrialExpiredPage /> },

  // Onboarding wizard — protected but outside AppLayout (full-screen dark design)
  {
    path: '/app/onboarding',
    element: (
      <ProtectedRoute>
        <OnboardingWizardPage />
      </ProtectedRoute>
    ),
  },

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
      { path: 'agents', element: <AgentConfigPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },

  // Fallback
  { path: '*', element: <Navigate to="/auth/login" replace /> },
])

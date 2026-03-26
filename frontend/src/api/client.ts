import axios from 'axios'

// Vazio → URL relativa (passa pelo nginx reverse proxy na porta 80)
// Preenchido → direto para a API (útil em dev local sem nginx)
const BASE = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Inject JWT on every request
api.interceptors.request.use(cfg => {
  const raw = localStorage.getItem('ops-auth')
  if (raw) {
    const { state } = JSON.parse(raw)
    if (state?.token) cfg.headers.Authorization = `Bearer ${state.token}`
  }
  return cfg
})

// On 401 → clear auth and redirect to login
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('ops-auth')
      window.location.href = '/auth/login'
    }
    return Promise.reject(err)
  }
)

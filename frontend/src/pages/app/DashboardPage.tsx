import { useQueries } from '@tanstack/react-query'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import {
  Users, Lightning, CurrencyDollar, ChatCircle,
  ArrowsClockwise, Package, Warning
} from '@phosphor-icons/react'
import { useAuthStore } from '../../store/authStore'
import StatsCard from '../../components/ui/StatsCard'
import { dashboardApi, type KPIs, type SalesFunnelItem, type RevenuePoint, type ConversationMetrics, type InventoryAlert } from '../../api/dashboard'

// ── Fallback / mock data when API is unavailable ────────────────────────────
const MOCK_KPIS: KPIs = {
  total_customers: 847,
  active_leads: 124,
  monthly_revenue: 198340,
  conversion_rate: 23.4,
  active_conversations: 38,
  uptime_percent: 99.97,
}

const MOCK_FUNNEL: SalesFunnelItem[] = [
  { stage: 'new', label: 'Novos', count: 48, value: 234000 },
  { stage: 'contacted', label: 'Contatados', count: 36, value: 180000 },
  { stage: 'qualified', label: 'Qualificados', count: 28, value: 142000 },
  { stage: 'proposal', label: 'Proposta', count: 19, value: 98000 },
  { stage: 'negotiation', label: 'Negociação', count: 11, value: 67000 },
  { stage: 'won', label: 'Ganhos', count: 7, value: 41000 },
]

const MOCK_REVENUE: RevenuePoint[] = [
  { month: 'Set', revenue: 124000, target: 120000 },
  { month: 'Out', revenue: 138500, target: 135000 },
  { month: 'Nov', revenue: 152000, target: 145000 },
  { month: 'Dez', revenue: 165000, target: 158000 },
  { month: 'Jan', revenue: 178000, target: 170000 },
  { month: 'Fev', revenue: 183500, target: 180000 },
  { month: 'Mar', revenue: 198340, target: 190000 },
]

const MOCK_CONV: ConversationMetrics = {
  messages_sent: 4312,
  takeovers: 87,
  avg_response_seconds: 18,
}

const MOCK_ALERTS: InventoryAlert[] = [
  { id: '1', name: 'Cabo UTP Cat6 (100m)', sku: 'CAB-UTP-100', stock: 3, min_stock: 10 },
  { id: '2', name: 'Switch 24p Gerenciável', sku: 'SW-24G-MGT', stock: 1, min_stock: 5 },
]

// ── Helpers ─────────────────────────────────────────────────────────────────
function fmt(n: number) {
  if (n >= 1_000_000) return `R$ ${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `R$ ${(n / 1_000).toFixed(0)}k`
  return `R$ ${n.toLocaleString('pt-BR')}`
}

function fmtTime(s: number) {
  if (s < 60) return `${s}s`
  return `${Math.round(s / 60)}min`
}

// ── Tooltip personalizado ────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-zinc-100 rounded-xl shadow-lg px-4 py-3 text-xs">
      <p className="font-semibold text-[#1D1D1F] mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }} className="font-medium">
          {p.name}: {p.name.includes('R$') || p.dataKey === 'revenue' || p.dataKey === 'target'
            ? fmt(p.value)
            : p.value}
        </p>
      ))}
    </div>
  )
}

function FunnelTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-zinc-100 rounded-xl shadow-lg px-4 py-3 text-xs">
      <p className="font-semibold text-[#1D1D1F] mb-1">{label}</p>
      <p className="text-zinc-500">Leads: <span className="text-[#1D1D1F] font-semibold">{payload[0]?.value}</span></p>
      <p className="text-zinc-500">Valor: <span className="text-[#0ABAB5] font-semibold">{fmt(payload[0]?.payload?.value)}</span></p>
    </div>
  )
}

// ── Component ────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const user = useAuthStore(s => s.user)
  const tenant = useAuthStore(s => s.tenant)

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite'

  const results = useQueries({
    queries: [
      { queryKey: ['dashboard', 'kpis'], queryFn: dashboardApi.getKpis, retry: false },
      { queryKey: ['dashboard', 'funnel'], queryFn: dashboardApi.getSalesFunnel, retry: false },
      { queryKey: ['dashboard', 'revenue'], queryFn: dashboardApi.getRevenueChart, retry: false },
      { queryKey: ['dashboard', 'conv'], queryFn: dashboardApi.getConvMetrics, retry: false },
      { queryKey: ['dashboard', 'alerts'], queryFn: dashboardApi.getInventoryAlerts, retry: false },
    ],
  })

  const [kpisQ, funnelQ, revenueQ, convQ, alertsQ] = results

  // Use API data if available, else fall back to mocks
  const kpis: KPIs = kpisQ.data ?? MOCK_KPIS
  const funnel: SalesFunnelItem[] = funnelQ.data ?? MOCK_FUNNEL
  const revenue: RevenuePoint[] = revenueQ.data ?? MOCK_REVENUE
  const conv: ConversationMetrics = convQ.data ?? MOCK_CONV
  const alerts: InventoryAlert[] = alertsQ.data ?? MOCK_ALERTS

  const loading = kpisQ.isLoading

  return (
    <div className="p-6 lg:p-8 space-y-8">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1D1D1F] tracking-tight">
            {greeting}, {user?.name?.split(' ')[0]}
          </h1>
          <p className="text-zinc-500 mt-1 text-sm">
            Aqui está o resumo de <span className="font-semibold text-[#1D1D1F]">{tenant?.name}</span> hoje.
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-2 text-xs text-zinc-400 bg-white border border-zinc-100 rounded-xl px-3 py-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
          </span>
          Ao vivo · {new Date().toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' })}
        </div>
      </div>

      {/* KPI Cards — row 1 */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatsCard
          label="Clientes"
          value={loading ? '—' : kpis.total_customers.toLocaleString('pt-BR')}
          icon={<Users size={18} weight="duotone" />}
          trend={8.2}
          loading={loading}
        />
        <StatsCard
          label="Leads Ativos"
          value={loading ? '—' : kpis.active_leads}
          icon={<Lightning size={18} weight="duotone" />}
          trend={12.5}
          loading={loading}
        />
        <StatsCard
          label="Receita Mensal"
          value={loading ? '—' : fmt(kpis.monthly_revenue)}
          icon={<CurrencyDollar size={18} weight="duotone" />}
          trend={6.8}
          highlight
          loading={loading}
        />
        <StatsCard
          label="Conversão"
          value={loading ? '—' : `${kpis.conversion_rate}%`}
          icon={<ArrowsClockwise size={18} weight="duotone" />}
          trend={2.1}
          loading={loading}
        />
        <StatsCard
          label="Conversas Ativas"
          value={loading ? '—' : kpis.active_conversations}
          icon={<ChatCircle size={18} weight="duotone" />}
          loading={loading}
        />
        <StatsCard
          label="Uptime"
          value={loading ? '—' : `${kpis.uptime_percent}%`}
          icon={<Lightning size={18} weight="duotone" />}
          loading={loading}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">

        {/* Revenue chart — 2/3 */}
        <div className="xl:col-span-2 bg-white rounded-2xl border border-zinc-100 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="text-sm font-semibold text-[#1D1D1F]">Receita Mensal</p>
              <p className="text-xs text-zinc-400 mt-0.5">Real vs Meta — últimos 7 meses</p>
            </div>
            <span className="text-xs font-mono font-semibold text-[#0ABAB5] bg-[#0ABAB5]/8 px-2.5 py-1 rounded-full">
              {fmt(kpis.monthly_revenue)}
            </span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={revenue} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#a1a1aa' }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={v => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11, fill: '#a1a1aa' }} axisLine={false} tickLine={false} width={42} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: '#71717a' }} />
              <Line type="monotone" dataKey="target" name="Meta" stroke="#e4e4e7" strokeWidth={1.5} dot={false} strokeDasharray="4 4" />
              <Line type="monotone" dataKey="revenue" name="Receita" stroke="#0ABAB5" strokeWidth={2.5} dot={{ r: 3, fill: '#0ABAB5', strokeWidth: 0 }} activeDot={{ r: 5, fill: '#0ABAB5' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Sales funnel — 1/3 */}
        <div className="bg-white rounded-2xl border border-zinc-100 p-6">
          <div className="mb-6">
            <p className="text-sm font-semibold text-[#1D1D1F]">Funil de Vendas</p>
            <p className="text-xs text-zinc-400 mt-0.5">Leads por etapa</p>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={funnel} layout="vertical" margin={{ top: 0, right: 4, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#a1a1aa' }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="label" tick={{ fontSize: 11, fill: '#71717a' }} axisLine={false} tickLine={false} width={72} />
              <Tooltip content={<FunnelTooltip />} />
              <Bar dataKey="count" fill="#0ABAB5" radius={[0, 6, 6, 0]} maxBarSize={16} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        {/* Conversation metrics */}
        <div className="bg-white rounded-2xl border border-zinc-100 p-6">
          <p className="text-sm font-semibold text-[#1D1D1F] mb-5">Métricas de Conversas</p>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Mensagens enviadas', value: conv.messages_sent.toLocaleString('pt-BR'), icon: <ChatCircle size={16} weight="duotone" /> },
              { label: 'Takeovers humanos', value: conv.takeovers, icon: <Users size={16} weight="duotone" /> },
              { label: 'Tempo médio resp.', value: fmtTime(conv.avg_response_seconds), icon: <Lightning size={16} weight="duotone" /> },
            ].map(({ label, value, icon }) => (
              <div key={label} className="text-center">
                <div className="w-10 h-10 rounded-xl bg-zinc-50 flex items-center justify-center text-zinc-400 mx-auto mb-2">
                  {icon}
                </div>
                <p className="text-xl font-bold text-[#1D1D1F] font-mono tracking-tight">{value}</p>
                <p className="text-[11px] text-zinc-400 mt-0.5 leading-tight">{label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Inventory alerts */}
        <div className="bg-white rounded-2xl border border-zinc-100 p-6">
          <div className="flex items-center justify-between mb-5">
            <p className="text-sm font-semibold text-[#1D1D1F]">Alertas de Estoque</p>
            {alerts.length > 0 && (
              <span className="flex items-center gap-1 text-xs font-semibold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full">
                <Warning size={12} weight="bold" />
                {alerts.length} item{alerts.length > 1 ? 'ns' : ''}
              </span>
            )}
          </div>
          {alerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-6 text-zinc-300">
              <Package size={32} weight="duotone" />
              <p className="text-xs mt-2">Nenhum alerta de estoque</p>
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map(item => (
                <div key={item.id} className="flex items-center gap-3 p-3 bg-amber-50/60 rounded-xl border border-amber-100">
                  <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center shrink-0">
                    <Package size={15} weight="duotone" className="text-amber-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-[#1D1D1F] truncate">{item.name}</p>
                    <p className="text-[11px] text-zinc-400 font-mono">{item.sku}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-bold text-red-600 font-mono">{item.stock}</p>
                    <p className="text-[10px] text-zinc-400">mín {item.min_stock}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

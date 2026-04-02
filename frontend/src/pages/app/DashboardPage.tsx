import { useQueries } from '@tanstack/react-query'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts'
import {
  Users, Lightning, CurrencyDollar, ChatCircle,
  ArrowsClockwise
} from '@phosphor-icons/react'
import { useAuthStore } from '../../store/authStore'
import StatsCard from '../../components/ui/StatsCard'
import { dashboardApi, type KPIs, type SalesFunnelItem, type RevenuePoint, type ConversationMetrics } from '../../api/dashboard'

// ── Helpers ─────────────────────────────────────────────────────────────────
function fmt(n: number | undefined | null) {
  const v = n ?? 0
  if (v >= 1_000_000) return `R$ ${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `R$ ${(v / 1_000).toFixed(0)}k`
  return `R$ ${v.toLocaleString('pt-BR')}`
}

// ── Tooltip personalizado ────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-zinc-100 rounded-xl shadow-lg px-4 py-3 text-xs">
      <p className="font-semibold text-[#1D1D1F] mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }} className="font-medium">
          {p.name}: {p.dataKey === 'revenue' ? fmt(p.value) : p.value}
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
      <p className="text-zinc-500">Valor: <span className="text-[#0ABAB5] font-semibold">{fmt(payload[0]?.payload?.total_value)}</span></p>
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
      { queryKey: ['dashboard', 'kpis'],    queryFn: dashboardApi.getKpis },
      { queryKey: ['dashboard', 'funnel'],  queryFn: dashboardApi.getSalesFunnel },
      { queryKey: ['dashboard', 'revenue'], queryFn: dashboardApi.getRevenueChart },
      { queryKey: ['dashboard', 'conv'],    queryFn: dashboardApi.getConvMetrics },
    ],
  })

  const [kpisQ, funnelQ, revenueQ, convQ] = results

  const kpis: KPIs | undefined = kpisQ.data
  const funnel: SalesFunnelItem[] = funnelQ.data ?? []
  const revenue: RevenuePoint[] = revenueQ.data ?? []
  const conv: ConversationMetrics | undefined = convQ.data

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

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        <StatsCard
          label="Clientes"
          value={loading ? '—' : (kpis?.total_customers ?? 0).toLocaleString('pt-BR')}
          icon={<Users size={18} weight="duotone" />}
          loading={loading}
        />
        <StatsCard
          label="Leads Abertos"
          value={loading ? '—' : (kpis?.open_leads ?? 0)}
          icon={<Lightning size={18} weight="duotone" />}
          loading={loading}
        />
        <StatsCard
          label="Receita Total"
          value={loading ? '—' : fmt(kpis?.total_revenue)}
          icon={<CurrencyDollar size={18} weight="duotone" />}
          highlight
          loading={loading}
        />
        <StatsCard
          label="Taxa de Vitória"
          value={loading ? '—' : `${((kpis?.win_rate ?? 0) * 100).toFixed(1)}%`}
          icon={<ArrowsClockwise size={18} weight="duotone" />}
          loading={loading}
        />
        <StatsCard
          label="Conversas Ativas"
          value={loading ? '—' : (kpis?.active_conversations ?? 0)}
          icon={<ChatCircle size={18} weight="duotone" />}
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
              <p className="text-xs text-zinc-400 mt-0.5">Aprovados nos últimos {revenue.length} meses</p>
            </div>
            <span className="text-xs font-mono font-semibold text-[#0ABAB5] bg-[#0ABAB5]/8 px-2.5 py-1 rounded-full">
              {fmt(kpis?.total_revenue)}
            </span>
          </div>
          {revenue.length === 0 && !revenueQ.isLoading ? (
            <div className="flex items-center justify-center h-[220px] text-zinc-300 text-sm">Sem dados de receita</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={revenue} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#a1a1aa' }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={v => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11, fill: '#a1a1aa' }} axisLine={false} tickLine={false} width={42} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="revenue" name="Receita" stroke="#0ABAB5" strokeWidth={2.5} dot={{ r: 3, fill: '#0ABAB5', strokeWidth: 0 }} activeDot={{ r: 5, fill: '#0ABAB5' }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Sales funnel — 1/3 */}
        <div className="bg-white rounded-2xl border border-zinc-100 p-6">
          <div className="mb-6">
            <p className="text-sm font-semibold text-[#1D1D1F]">Funil de Vendas</p>
            <p className="text-xs text-zinc-400 mt-0.5">Leads por etapa</p>
          </div>
          {funnel.length === 0 && !funnelQ.isLoading ? (
            <div className="flex items-center justify-center h-[220px] text-zinc-300 text-sm">Nenhum lead</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={funnel} layout="vertical" margin={{ top: 0, right: 4, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#a1a1aa' }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="label" tick={{ fontSize: 11, fill: '#71717a' }} axisLine={false} tickLine={false} width={72} />
                <Tooltip content={<FunnelTooltip />} />
                <Bar dataKey="count" fill="#0ABAB5" radius={[0, 6, 6, 0]} maxBarSize={16} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Conversation metrics */}
      <div className="bg-white rounded-2xl border border-zinc-100 p-6">
        <p className="text-sm font-semibold text-[#1D1D1F] mb-5">Métricas de Conversas</p>
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Total de Conversas',  value: (conv?.total_conversations ?? 0).toLocaleString('pt-BR'), icon: <ChatCircle size={16} weight="duotone" /> },
            { label: 'Takeovers humanos',   value: conv?.takeover_sessions_period ?? 0,                       icon: <Users size={16} weight="duotone" /> },
            { label: 'Média msgs/conv.',    value: (conv?.avg_messages_per_conversation ?? 0).toFixed(1),     icon: <Lightning size={16} weight="duotone" /> },
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
    </div>
  )
}

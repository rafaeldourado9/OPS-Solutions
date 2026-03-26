import { type ReactNode } from 'react'
import { TrendUp, TrendDown } from '@phosphor-icons/react'

interface StatsCardProps {
  label: string
  value: string | number
  icon: ReactNode
  trend?: number        // positive = up, negative = down
  trendLabel?: string
  highlight?: boolean   // teal accent
  loading?: boolean
}

export default function StatsCard({ label, value, icon, trend, trendLabel, highlight, loading }: StatsCardProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-zinc-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="h-4 w-24 bg-zinc-100 rounded animate-pulse" />
          <div className="w-10 h-10 bg-zinc-100 rounded-xl animate-pulse" />
        </div>
        <div className="h-8 w-32 bg-zinc-100 rounded-lg animate-pulse mb-2" />
        <div className="h-3 w-20 bg-zinc-50 rounded animate-pulse" />
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-2xl border p-6 transition-all hover:shadow-md ${highlight ? 'border-[#0ABAB5]/30 ring-1 ring-[#0ABAB5]/10' : 'border-zinc-100'}`}>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-medium text-zinc-500">{label}</p>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${highlight ? 'bg-[#0ABAB5]/10 text-[#0ABAB5]' : 'bg-zinc-50 text-zinc-500'}`}>
          {icon}
        </div>
      </div>
      <p className={`text-2xl font-bold tracking-tight mb-1 ${highlight ? 'text-[#0ABAB5]' : 'text-[#1D1D1F]'}`}>
        {value}
      </p>
      {trend !== undefined && (
        <div className={`flex items-center gap-1 text-xs font-medium ${trend >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
          {trend >= 0 ? <TrendUp size={12} weight="bold" /> : <TrendDown size={12} weight="bold" />}
          <span>{Math.abs(trend)}% {trendLabel ?? 'vs mês anterior'}</span>
        </div>
      )}
    </div>
  )
}

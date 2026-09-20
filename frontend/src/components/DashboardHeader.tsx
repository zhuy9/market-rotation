import { formatTimestamp } from '../lib/format'
import { RefreshButton } from './RefreshButton'

interface DashboardHeaderProps {
  provider: string
  dataTimestamp: string | null
  onRefresh: () => void
  isRefreshing: boolean
}

export function DashboardHeader({
  provider,
  dataTimestamp,
  onRefresh,
  isRefreshing,
}: DashboardHeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-neutral-800 pb-4">
      <div>
        <h1 className="text-lg font-semibold tracking-tight text-neutral-50">
          Market Rotation Dashboard
        </h1>
        <p className="text-xs text-neutral-500">
          Last updated: {formatTimestamp(dataTimestamp)} · Source: {provider}
        </p>
      </div>
      <RefreshButton onRefresh={onRefresh} isRefreshing={isRefreshing} />
    </header>
  )
}

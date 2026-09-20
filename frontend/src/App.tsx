import type { ReactNode } from 'react'

import { CrossAssetPanel } from './components/CrossAssetPanel'
import { DashboardHeader } from './components/DashboardHeader'
import { DataQualityBanner } from './components/DataQualityBanner'
import { MarketInternalsPanel } from './components/MarketInternalsPanel'
import { RegimeCard } from './components/RegimeCard'
import { RelativeRotationChart } from './components/RelativeRotationChart'
import { SectorHeatmap } from './components/SectorHeatmap'
import { useDashboard } from './hooks/useDashboard'

function CenteredMessage({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950 px-4 text-center text-sm text-neutral-400">
      {children}
    </div>
  )
}

function App() {
  const { dashboard, isLoading, error, isRefreshing, refresh } = useDashboard()

  if (isLoading) {
    return <CenteredMessage>Loading dashboard…</CenteredMessage>
  }

  if (!dashboard) {
    return (
      <CenteredMessage>
        Could not reach the backend{error ? `: ${error}` : ''}. Is the API running?
      </CenteredMessage>
    )
  }

  return (
    <div className="min-h-screen bg-neutral-950 px-4 py-6 text-neutral-100 sm:px-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-4">
        <DashboardHeader
          provider={dashboard.provider}
          dataTimestamp={dashboard.data_timestamp}
          retrievedAt={dashboard.retrieved_at}
          onRefresh={refresh}
          isRefreshing={isRefreshing}
        />
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <DataQualityBanner isStale={dashboard.is_stale} warnings={dashboard.warnings} />
        <RegimeCard regime={dashboard.regime} />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <SectorHeatmap sectors={dashboard.sectors} />
          <RelativeRotationChart sectors={dashboard.sectors} />
        </div>
        <CrossAssetPanel rows={dashboard.cross_asset} />
        <MarketInternalsPanel
          breadth5d={dashboard.breadth_5d}
          dispersion5d={dashboard.dispersion_5d}
          rsp5d={dashboard.ratios.rsp_spy.return_5d}
          hygLqd5d={dashboard.ratios.hyg_lqd.return_5d}
          defensiveSpread5d={dashboard.defensive_spread_5d}
        />
      </div>
    </div>
  )
}

export default App

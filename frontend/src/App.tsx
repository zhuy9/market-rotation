import type { ReactNode } from 'react'

import { CrossAssetPanel } from './components/CrossAssetPanel'
import { DashboardFooter } from './components/DashboardFooter'
import { DashboardHeader } from './components/DashboardHeader'
import { DataQualityBanner } from './components/DataQualityBanner'
import { MarketInternalsPanel } from './components/MarketInternalsPanel'
import { RegimeCard } from './components/RegimeCard'
import { RelativeRotationChart } from './components/RelativeRotationChart'
import { SectorFlowChart } from './components/SectorFlowChart'
import { SectorHeatmap } from './components/SectorHeatmap'
import { useDashboard } from './hooks/useDashboard'
import { useFlows } from './hooks/useFlows'

function CenteredMessage({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950 px-4 text-center text-sm text-neutral-400">
      {children}
    </div>
  )
}

function App() {
  const { dashboard, isLoading, error, isRefreshing, refresh } = useDashboard()
  const { flows, error: flowError } = useFlows()

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
        {(error || flowError) && <p className="text-sm text-rose-400">{error ?? flowError}</p>}
        <DataQualityBanner isStale={dashboard.is_stale} warnings={dashboard.warnings} />
        <RegimeCard regime={dashboard.regime} />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <SectorHeatmap sectors={dashboard.sectors} />
          <RelativeRotationChart sectors={dashboard.sectors} />
        </div>
        {/* Flows are cached separately and are often absent, so the panel
            appears only once there is something to draw. */}
        {flows && flows.sectors.length > 0 && <SectorFlowChart flows={flows} />}
        <CrossAssetPanel rows={dashboard.cross_asset} />
        <MarketInternalsPanel
          breadth5d={dashboard.breadth_5d}
          dispersion5d={dashboard.dispersion_5d}
          rsp5d={dashboard.ratios.rsp_spy.return_5d}
          hygLqd5d={dashboard.ratios.hyg_lqd.return_5d}
          growthValue5d={dashboard.ratios.ivw_ive.return_5d}
          defensiveSpread5d={dashboard.defensive_spread_5d}
        />
        <DashboardFooter />
      </div>
    </div>
  )
}

export default App

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as client from './api/client'
import type { Dashboard, Flows } from './api/types'
import App from './App'

function buildDashboard(overrides: Partial<Dashboard> = {}): Dashboard {
  return {
    as_of: '2026-09-19T20:00:00Z',
    provider: 'yfinance',
    data_timestamp: '2026-09-19T20:00:00Z',
    retrieved_at: '2026-09-20T12:30:00Z',
    is_stale: false,
    regime: { name: 'INTERNAL_ROTATION', confidence: 'medium', reasons: ['SPY was flat.'] },
    sectors: [],
    cross_asset: [],
    breadth_1d: { positive: 6, total: 11, ratio: 0.545 },
    breadth_5d: { positive: 6, total: 11, ratio: 0.545 },
    dispersion_1d: 0.01,
    dispersion_5d: 0.02,
    defensive_spread_5d: 0.005,
    ratios: {
      rsp_spy: { return_1d: 0.001, return_5d: 0.002, return_20d: 0.003 },
      hyg_lqd: { return_1d: -0.001, return_5d: -0.002, return_20d: -0.003 },
    },
    warnings: [],
    ...overrides,
  }
}

function buildFlows(overrides: Partial<Flows> = {}): Flows {
  return {
    as_of: '2026-09-17T00:00:00',
    windows: [1, 5, 20],
    sectors: [
      { symbol: 'XLK', name: 'Technology', flows: { '1D': -103e6, '5D': -282e6, '20D': -692e6 } },
    ],
    ...overrides,
  }
}

function renderApp() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  )
}

describe('App', () => {
  // Flows are a separate query. Default them to empty so every other test
  // exercises the common case of an unpopulated flow cache.
  beforeEach(() => {
    vi.spyOn(client, 'fetchFlows').mockResolvedValue(buildFlows({ as_of: null, sectors: [] }))
  })

  it('shows a loading state before the dashboard resolves', () => {
    vi.spyOn(client, 'fetchDashboard').mockReturnValue(new Promise(() => {}))

    renderApp()

    expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument()
  })

  it('renders the regime once the dashboard loads', async () => {
    vi.spyOn(client, 'fetchDashboard').mockResolvedValue(buildDashboard())

    renderApp()

    await waitFor(() => {
      expect(screen.getByText('Market Rotation Dashboard')).toBeInTheDocument()
    })
    expect(screen.getByText('Internal Rotation')).toBeInTheDocument()
    expect(screen.getByText('SPY was flat.')).toBeInTheDocument()
  })

  it('shows a stale-data warning when the backend flags it', async () => {
    vi.spyOn(client, 'fetchDashboard').mockResolvedValue(buildDashboard({ is_stale: true }))

    renderApp()

    expect(await screen.findByText(/stale data/i)).toBeInTheDocument()
  })

  it('shows an unreachable-backend message when the fetch fails', async () => {
    vi.spyOn(client, 'fetchDashboard').mockRejectedValue(new Error('network down'))

    renderApp()

    expect(await screen.findByText(/could not reach the backend/i)).toBeInTheDocument()
  })

  it('triggers a backend refresh and shows a loading state while it runs', async () => {
    vi.spyOn(client, 'fetchDashboard').mockResolvedValue(buildDashboard())
    // Never resolves, so the pending state stays observable.
    const refresh = vi.spyOn(client, 'refreshData').mockReturnValue(new Promise(() => {}))

    renderApp()
    fireEvent.click(await screen.findByRole('button', { name: /refresh data/i }))

    // The mutation dispatches asynchronously, so wait for the pending state
    // before asserting the call happened.
    expect(await screen.findByRole('button', { name: /refreshing/i })).toBeDisabled()
    expect(refresh).toHaveBeenCalledTimes(1)
  })

  it('surfaces a failed refresh without discarding the dashboard already on screen', async () => {
    vi.spyOn(client, 'fetchDashboard').mockResolvedValue(buildDashboard())
    vi.spyOn(client, 'refreshData').mockRejectedValue(new Error('refresh failed with status 503'))

    renderApp()
    fireEvent.click(await screen.findByRole('button', { name: /refresh data/i }))

    expect(await screen.findByText(/refresh failed with status 503/i)).toBeInTheDocument()
    expect(screen.getByText('Internal Rotation')).toBeInTheDocument()
  })

  it('omits the flow panel entirely when no flows are cached', async () => {
    vi.spyOn(client, 'fetchDashboard').mockResolvedValue(buildDashboard())

    renderApp()
    await screen.findByText(/Sector Heatmap/i)

    // An unpopulated flow cache is the normal state, not an error to report.
    expect(screen.queryByText(/Sector Fund Flows/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/failed/i)).not.toBeInTheDocument()
  })

  it('renders the flow panel once flows are cached', async () => {
    vi.spyOn(client, 'fetchDashboard').mockResolvedValue(buildDashboard())
    vi.spyOn(client, 'fetchFlows').mockResolvedValue(buildFlows())

    renderApp()

    expect(await screen.findByText(/Sector Fund Flows/i)).toBeInTheDocument()
  })

  it('surfaces a flow fetch failure rather than passing it off as no data', async () => {
    vi.spyOn(client, 'fetchDashboard').mockResolvedValue(buildDashboard())
    vi.spyOn(client, 'fetchFlows').mockRejectedValue(new Error('/api/flows failed with status 500'))

    renderApp()

    expect(await screen.findByText(/\/api\/flows failed with status 500/)).toBeInTheDocument()
  })
})

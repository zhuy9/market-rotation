import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import * as client from './api/client'
import type { Dashboard } from './api/types'
import App from './App'

function buildDashboard(overrides: Partial<Dashboard> = {}): Dashboard {
  return {
    as_of: '2026-09-19T20:00:00Z',
    provider: 'yfinance',
    data_timestamp: '2026-09-19T20:00:00Z',
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

function renderApp() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  )
}

describe('App', () => {
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
})

import { afterEach, describe, expect, it, vi } from 'vitest'

import { fetchDashboard, refreshData } from './client'

function mockFetch(response: Partial<Response>) {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, ...response })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('fetchDashboard', () => {
  it('requests the dashboard endpoint and returns the parsed payload', async () => {
    const fetchMock = mockFetch({ json: () => Promise.resolve({ provider: 'yfinance' }) })

    await expect(fetchDashboard()).resolves.toEqual({ provider: 'yfinance' })
    expect(fetchMock.mock.calls[0][0]).toContain('/api/dashboard')
  })

  it('throws a message naming the path and status when the backend errors', async () => {
    mockFetch({ ok: false, status: 503 })

    await expect(fetchDashboard()).rejects.toThrow('/api/dashboard failed with status 503')
  })
})

describe('refreshData', () => {
  it('POSTs to the refresh endpoint', async () => {
    const fetchMock = mockFetch({ json: () => Promise.resolve({ status: 'success' }) })

    await expect(refreshData()).resolves.toEqual({ status: 'success' })
    expect(fetchMock.mock.calls[0][0]).toContain('/api/data/refresh')
    expect(fetchMock.mock.calls[0][1]).toEqual({ method: 'POST' })
  })

  it('throws when the refresh endpoint fails', async () => {
    mockFetch({ ok: false, status: 429 })

    await expect(refreshData()).rejects.toThrow('/api/data/refresh failed with status 429')
  })
})

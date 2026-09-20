import type { Dashboard, RefreshResult } from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, init)
  if (!response.ok) {
    throw new Error(`${path} failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function fetchDashboard(): Promise<Dashboard> {
  return request<Dashboard>('/api/dashboard')
}

export function refreshData(): Promise<RefreshResult> {
  return request<RefreshResult>('/api/data/refresh', { method: 'POST' })
}

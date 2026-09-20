import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { fetchDashboard, refreshData } from '../api/client'

const DASHBOARD_QUERY_KEY = ['dashboard']

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback
}

export function useDashboard() {
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: DASHBOARD_QUERY_KEY, queryFn: fetchDashboard })
  const refreshMutation = useMutation({
    mutationFn: refreshData,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: DASHBOARD_QUERY_KEY }),
  })

  const activeError = query.error ?? refreshMutation.error

  return {
    dashboard: query.data ?? null,
    isLoading: query.isLoading,
    error: activeError ? errorMessage(activeError, 'Failed to load dashboard') : null,
    isRefreshing: refreshMutation.isPending,
    refresh: () => refreshMutation.mutate(),
  }
}

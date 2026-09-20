import { useQuery } from '@tanstack/react-query'

import { fetchFlows } from '../api/client'

/** Flows are optional: the cache is populated by scripts/spdr_flows_report.py,
 *  so an empty result is expected rather than a failure. A real fetch error is
 *  still surfaced, so a broken endpoint is not mistaken for "no data yet". */
export function useFlows() {
  const query = useQuery({ queryKey: ['flows'], queryFn: fetchFlows })

  return {
    flows: query.data ?? null,
    error: query.error ? query.error.message : null,
  }
}

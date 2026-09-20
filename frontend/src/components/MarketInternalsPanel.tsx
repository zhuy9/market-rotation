import type { Breadth } from '../api/types'
import { formatPercent } from '../lib/format'
import { Panel } from './Panel'

interface MarketInternalsPanelProps {
  breadth5d: Breadth
  dispersion5d: number | null
  rsp5d: number | null
  hygLqd5d: number | null
  defensiveSpread5d: number | null
}

export function MarketInternalsPanel({
  breadth5d,
  dispersion5d,
  rsp5d,
  hygLqd5d,
  defensiveSpread5d,
}: MarketInternalsPanelProps) {
  const stats = [
    { label: 'Sector Breadth (5D)', value: `${breadth5d.positive} / ${breadth5d.total}` },
    { label: 'Sector Dispersion (5D)', value: formatPercent(dispersion5d) },
    { label: 'RSP vs SPY (5D)', value: formatPercent(rsp5d) },
    { label: 'HYG vs LQD (5D)', value: formatPercent(hygLqd5d) },
    { label: 'Defensive Spread (5D)', value: formatPercent(defensiveSpread5d) },
  ]

  return (
    <Panel title="Market Internals">
      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        {stats.map((stat) => (
          <div key={stat.label}>
            <dt className="text-xs text-neutral-500">{stat.label}</dt>
            <dd className="mt-1 font-mono text-lg tabular-nums text-neutral-100">{stat.value}</dd>
          </div>
        ))}
      </dl>
    </Panel>
  )
}

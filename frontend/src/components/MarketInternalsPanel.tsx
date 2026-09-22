import type { Breadth } from '../api/types'
import { formatPercent } from '../lib/format'
import { InfoTooltip } from './InfoTooltip'
import { Panel } from './Panel'

interface MarketInternalsPanelProps {
  breadth5d: Breadth
  dispersion5d: number | null
  rsp5d: number | null
  hygLqd5d: number | null
  growthValue5d: number | null
  defensiveSpread5d: number | null
}

export function MarketInternalsPanel({
  breadth5d,
  dispersion5d,
  rsp5d,
  hygLqd5d,
  growthValue5d,
  defensiveSpread5d,
}: MarketInternalsPanelProps) {
  const stats = [
    {
      label: 'Sector Breadth (5D)',
      value: `${breadth5d.positive} / ${breadth5d.total}`,
      description: 'How many of the 11 tracked sector ETFs had a positive 5-day return.',
    },
    {
      label: 'Sector Dispersion (5D)',
      value: formatPercent(dispersion5d),
      description:
        'How spread out sector returns are (standard deviation of 5-day sector returns). Higher means more internal rotation between sectors rather than a uniform market move.',
    },
    {
      label: 'RSP vs SPY (5D)',
      value: formatPercent(rsp5d),
      description:
        'Equal-weight S&P (RSP) minus cap-weighted S&P (SPY), 5-day return. Positive means broader participation beyond the largest stocks; negative means mega-caps are driving the index.',
    },
    {
      label: 'HYG vs LQD (5D)',
      value: formatPercent(hygLqd5d),
      description:
        'High-yield credit (HYG) minus investment-grade credit (LQD), 5-day return. Positive means credit markets are leaning risk-on; negative means credit risk appetite is weakening.',
    },
    {
      label: 'IVW vs IVE (5D)',
      value: formatPercent(growthValue5d),
      description:
        'S&P 500 Growth (IVW) minus S&P 500 Value (IVE), 5-day return. Positive means growth stocks are leading; negative means leadership is rotating toward value.',
    },
    {
      label: 'Defensive Spread (5D)',
      value: formatPercent(defensiveSpread5d),
      description:
        'Mean 5-day return of defensive sectors (XLV, XLP, XLU) minus cyclical sectors (XLK, XLY, XLI, XLF, XLE, XLB). Positive means defensive sectors are leading.',
    },
  ]

  return (
    <Panel title="Market Internals">
      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {stats.map((stat) => (
          <div key={stat.label}>
            <dt className="flex items-center text-xs text-neutral-500">
              {stat.label}
              <InfoTooltip text={stat.description} />
            </dt>
            <dd className="mt-1 font-mono text-lg tabular-nums text-neutral-100">{stat.value}</dd>
          </div>
        ))}
      </dl>
    </Panel>
  )
}

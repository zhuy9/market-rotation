import type { CrossAssetRow } from '../api/types'
import { formatPercent, returnColorClass } from '../lib/format'
import { Panel } from './Panel'

interface CrossAssetPanelProps {
  rows: CrossAssetRow[]
}

const CATEGORY_LABELS: Record<string, string> = {
  equity: 'Equities',
  rates: 'Rates',
  credit: 'Credit',
  commodities: 'Commodities',
  currency: 'USD',
  volatility: 'Volatility',
}

const CATEGORY_ORDER = ['equity', 'rates', 'credit', 'commodities', 'currency', 'volatility']

export function CrossAssetPanel({ rows }: CrossAssetPanelProps) {
  const groups = CATEGORY_ORDER.map((category) => ({
    category,
    label: CATEGORY_LABELS[category] ?? category,
    items: rows.filter((row) => row.category === category),
  })).filter((group) => group.items.length > 0)

  return (
    <Panel title="Cross-Asset Performance">
      <div className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 lg:grid-cols-6">
        {groups.map((group) => (
          <div key={group.category}>
            <h3 className="mb-2 text-xs font-semibold tracking-wide text-neutral-500 uppercase">
              {group.label}
            </h3>
            <div className="mb-1 flex justify-between text-[10px] text-neutral-600">
              <span />
              <span className="flex gap-2">
                <span className="w-10 text-right">1D</span>
                <span className="w-10 text-right">5D</span>
                <span className="w-10 text-right">20D</span>
              </span>
            </div>
            <ul className="space-y-1.5">
              {group.items.map((item) => (
                <li key={item.symbol} className="flex items-center justify-between gap-2 text-sm">
                  <span className="font-mono text-neutral-200">{item.symbol}</span>
                  <span className="flex gap-2 font-mono text-xs tabular-nums">
                    <span className={`w-10 text-right ${returnColorClass(item.return_1d)}`}>
                      {formatPercent(item.return_1d)}
                    </span>
                    <span className={`w-10 text-right ${returnColorClass(item.return_5d)}`}>
                      {formatPercent(item.return_5d)}
                    </span>
                    <span className={`w-10 text-right ${returnColorClass(item.return_20d)}`}>
                      {formatPercent(item.return_20d)}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Panel>
  )
}

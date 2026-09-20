import { useState } from 'react'

import type { SectorRow } from '../api/types'
import { formatPercent, returnColorClass } from '../lib/format'
import { Panel } from './Panel'

type NumericKey = 'return_1d' | 'return_5d' | 'return_20d' | 'vs_spy_5d' | 'vs_spy_20d'

const COLUMNS: { key: NumericKey; label: string }[] = [
  { key: 'return_1d', label: '1D' },
  { key: 'return_5d', label: '5D' },
  { key: 'return_20d', label: '20D' },
  { key: 'vs_spy_5d', label: 'vs SPY 5D' },
  { key: 'vs_spy_20d', label: 'vs SPY 20D' },
]

interface SectorHeatmapProps {
  sectors: SectorRow[]
}

export function SectorHeatmap({ sectors }: SectorHeatmapProps) {
  const [sortKey, setSortKey] = useState<NumericKey>('return_5d')
  const [ascending, setAscending] = useState(false)

  const sorted = [...sectors].sort((a, b) => {
    const left = a[sortKey]
    const right = b[sortKey]
    if (left === null && right === null) return 0
    if (left === null) return 1
    if (right === null) return -1
    return ascending ? left - right : right - left
  })

  function toggleSort(key: NumericKey) {
    if (key === sortKey) {
      setAscending((prev) => !prev)
    } else {
      setSortKey(key)
      setAscending(false)
    }
  }

  return (
    <Panel title="Sector Heatmap">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-neutral-800 text-xs tracking-wide text-neutral-500 uppercase">
            <th className="py-1.5 text-left">Ticker</th>
            <th className="py-1.5 text-left">Sector</th>
            {COLUMNS.map((column) => (
              <th
                key={column.key}
                className="cursor-pointer py-1.5 text-right select-none"
                onClick={() => toggleSort(column.key)}
              >
                {column.label}
                {sortKey === column.key ? (ascending ? ' ↑' : ' ↓') : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((sector) => (
            <tr key={sector.symbol} className="border-b border-neutral-800/60">
              <td className="py-1.5 font-mono font-medium text-neutral-100">{sector.symbol}</td>
              <td className="py-1.5 text-neutral-400">{sector.name}</td>
              {COLUMNS.map((column) => (
                <td
                  key={column.key}
                  className={`py-1.5 text-right font-mono tabular-nums ${returnColorClass(sector[column.key])}`}
                >
                  {formatPercent(sector[column.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  )
}

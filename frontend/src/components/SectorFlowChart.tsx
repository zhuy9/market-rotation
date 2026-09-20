import { useState } from 'react'
import {
  Bar,
  BarChart,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { Flows } from '../api/types'
import { TOOLTIP_STYLE } from '../lib/chart'
import { formatFlow, formatTradingDate } from '../lib/format'
import { Panel } from './Panel'

const INFLOW = '#34d399'
const OUTFLOW = '#fb7185'

const METHODOLOGY =
  'Net creation/redemption flow, from State Street published data: the ' +
  'day-over-day change in shares outstanding priced at that day NAV. ETF ' +
  'shares are created and redeemed only by authorized participants, so this ' +
  'is measured flow rather than a price-based estimate.'

// Each sector needs vertical room for a readable bar and its label.
const ROW_HEIGHT = 26

interface SectorFlowChartProps {
  flows: Flows
}

export function SectorFlowChart({ flows }: SectorFlowChartProps) {
  // The longest window is the headline number; the shorter ones show whether a
  // move is recent or steady.
  const [window, setWindow] = useState(flows.windows[flows.windows.length - 1])

  const key = `${window}D`
  const data = flows.sectors
    .map((sector) => ({ ...sector, value: sector.flows[key] ?? null }))
    .filter((row) => row.value !== null)
    .sort((a, b) => (b.value as number) - (a.value as number))

  return (
    <Panel title="Sector Fund Flows" titleTooltip={METHODOLOGY}>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex gap-1" role="group" aria-label="Flow window">
          {flows.windows.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setWindow(option)}
              aria-pressed={option === window}
              className={`cursor-pointer rounded px-2 py-0.5 font-mono text-xs transition focus-visible:outline focus-visible:outline-neutral-500 ${
                option === window
                  ? 'bg-neutral-700 text-neutral-100'
                  : 'text-neutral-500 hover:text-neutral-300'
              }`}
            >
              {option}D
            </button>
          ))}
        </div>
        <span className="text-xs text-neutral-500">{`as of ${formatTradingDate(flows.as_of)}`}</span>
      </div>

      {data.length === 0 ? (
        <p className="py-8 text-center text-sm text-neutral-500">
          No flow data for the {key} window.
        </p>
      ) : (
        <>
          {/* The chart is an SVG with no text alternative, so its content is
              announced here. The empty case above is already plain text. */}
          <p className="sr-only">
            {data.map((row) => `${row.name}: ${formatFlow(row.value)}`).join('. ')}
          </p>
          <ResponsiveContainer width="100%" height={data.length * ROW_HEIGHT + 30}>
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 0, right: 16, bottom: 0, left: 8 }}
            >
              <XAxis
                type="number"
                tickFormatter={(value: number) => formatFlow(value)}
                tick={{ fill: '#737373', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="symbol"
                width={44}
                tick={{ fill: '#d4d4d4', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <ReferenceLine x={0} stroke="#525252" />
              <Tooltip
                cursor={{ fill: '#ffffff10' }}
                {...TOOLTIP_STYLE}
                formatter={(value) => [formatFlow(Number(value)), 'Net flow'] as [string, string]}
                labelFormatter={(label) =>
                  data.find((row) => row.symbol === label)?.name ?? String(label)
                }
              />
              <Bar dataKey="value" radius={2}>
                {data.map((row) => (
                  <Cell key={row.symbol} fill={(row.value as number) >= 0 ? INFLOW : OUTFLOW} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </>
      )}
    </Panel>
  )
}

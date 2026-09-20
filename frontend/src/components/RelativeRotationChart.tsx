import { ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'

import type { SectorRow } from '../api/types'
import { QUADRANT_COLOR } from '../lib/regime'
import { Panel } from './Panel'

interface RotationPoint {
  symbol: string
  x: number
  y: number
  quadrant: string
}

interface RelativeRotationChartProps {
  sectors: SectorRow[]
}

interface DotProps {
  cx?: number
  cy?: number
  payload?: RotationPoint
}

function RotationDot({ cx, cy, payload }: DotProps) {
  if (cx === undefined || cy === undefined || !payload) return null
  const color = QUADRANT_COLOR[payload.quadrant] ?? '#a3a3a3'
  return (
    <g>
      <circle cx={cx} cy={cy} r={4} fill={color} />
      <text x={cx} y={cy - 8} textAnchor="middle" fontSize={10} fill={color}>
        {payload.symbol}
      </text>
    </g>
  )
}

export function RelativeRotationChart({ sectors }: RelativeRotationChartProps) {
  const points: RotationPoint[] = sectors
    .filter((s) => s.vs_spy_20d !== null && s.vs_spy_5d !== null)
    .map((s) => ({
      symbol: s.symbol,
      x: (s.vs_spy_20d as number) * 100,
      y: (s.vs_spy_5d as number) * 100,
      quadrant: s.quadrant ?? 'LAGGING',
    }))

  return (
    <Panel title="Relative Rotation">
      <div className="mb-1 grid grid-cols-2 px-2 text-[10px] tracking-wide text-neutral-600 uppercase">
        <span className="text-left">Improving</span>
        <span className="text-right">Leading</span>
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <ScatterChart margin={{ top: 0, right: 20, bottom: 0, left: 0 }}>
          <XAxis
            type="number"
            dataKey="x"
            name="20D vs SPY"
            stroke="#525252"
            tick={{ fill: '#a3a3a3', fontSize: 11 }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="5D vs SPY"
            stroke="#525252"
            tick={{ fill: '#a3a3a3', fontSize: 11 }}
          />
          <ReferenceLine x={0} stroke="#525252" />
          <ReferenceLine y={0} stroke="#525252" />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            contentStyle={{ background: '#171717', border: '1px solid #404040', fontSize: 12 }}
            itemStyle={{ color: '#e5e5e5' }}
            labelStyle={{ color: '#e5e5e5' }}
            formatter={(value) => `${Number(value).toFixed(2)}%`}
          />
          <Scatter data={points} shape={RotationDot} />
        </ScatterChart>
      </ResponsiveContainer>
      <div className="mt-1 grid grid-cols-2 px-2 text-[10px] tracking-wide text-neutral-600 uppercase">
        <span className="text-left">Lagging</span>
        <span className="text-right">Weakening</span>
      </div>
    </Panel>
  )
}

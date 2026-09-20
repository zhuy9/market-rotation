import { useState } from 'react'
import {
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { SectorRow } from '../api/types'
import { QUADRANT_COLOR } from '../lib/regime'
import { Panel } from './Panel'

const MAX_TRAIL_SESSIONS = 5
const DEFAULT_TRAIL_SESSIONS = 1

// A sector with an unknown quadrant (either coordinate missing) gets this
// instead of being coloured as a real quadrant.
const NEUTRAL_COLOR = '#a3a3a3'

interface PlotPoint {
  symbol: string
  x: number
  y: number
  quadrant: string
  isCurrent: boolean
}

interface RelativeRotationChartProps {
  sectors: SectorRow[]
}

interface DotProps {
  cx?: number
  cy?: number
  payload?: PlotPoint
}

function RotationDot({ cx, cy, payload }: DotProps) {
  if (cx === undefined || cy === undefined || !payload) return null
  const color = QUADRANT_COLOR[payload.quadrant] ?? NEUTRAL_COLOR

  if (!payload.isCurrent) {
    return <circle cx={cx} cy={cy} r={1.5} fill={color} fillOpacity={0.5} />
  }
  return (
    <g>
      <circle cx={cx} cy={cy} r={4} fill={color} />
      <text x={cx} y={cy - 8} textAnchor="middle" fontSize={10} fill={color}>
        {payload.symbol}
      </text>
    </g>
  )
}

// Trail (previous `sessions` sessions, oldest first) + current position, as one
// path Recharts can connect with a line — PRD section 17's optional "faded trail".
// sector.trail is always oldest-first with up to MAX_TRAIL_SESSIONS points, so
// showing fewer sessions is just slicing the most recent end of it.
function sectorPath(sector: SectorRow, sessions: number): PlotPoint[] {
  if (sector.vs_spy_20d === null || sector.vs_spy_5d === null) return []
  const quadrant = sector.quadrant ?? ''

  // sessions=0 must yield no trail, not slice(-0) === slice(0) === the whole array.
  const historical: PlotPoint[] = (sessions > 0 ? sector.trail.slice(-sessions) : [])
    .filter((p) => p.x !== null && p.y !== null)
    .map((p) => ({
      symbol: sector.symbol,
      x: (p.x as number) * 100,
      y: (p.y as number) * 100,
      quadrant,
      isCurrent: false,
    }))

  const current: PlotPoint = {
    symbol: sector.symbol,
    x: sector.vs_spy_20d * 100,
    y: sector.vs_spy_5d * 100,
    quadrant,
    isCurrent: true,
  }
  return [...historical, current]
}

export function RelativeRotationChart({ sectors }: RelativeRotationChartProps) {
  const [trailSessions, setTrailSessions] = useState(DEFAULT_TRAIL_SESSIONS)
  const plottable = sectors.filter((s) => s.vs_spy_20d !== null && s.vs_spy_5d !== null)

  return (
    <Panel
      title="Relative Rotation"
      titleTooltip="Each sector's recent sessions, connected by a faded trail to its current position (the labeled dot). Adjust how many sessions of trail to show below."
    >
      <div className="mb-2 flex items-center justify-end gap-2 px-2">
        <label htmlFor="trail-sessions" className="text-xs text-neutral-500">
          Trail: {trailSessions} session{trailSessions === 1 ? '' : 's'}
        </label>
        <input
          id="trail-sessions"
          type="range"
          min={0}
          max={MAX_TRAIL_SESSIONS}
          step={1}
          value={trailSessions}
          onChange={(e) => setTrailSessions(Number(e.target.value))}
          className="w-24 accent-neutral-400"
        />
      </div>
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
          {plottable.map((sector) => (
            <Scatter
              key={sector.symbol}
              data={sectorPath(sector, trailSessions)}
              shape={RotationDot}
              line={{
                stroke: QUADRANT_COLOR[sector.quadrant ?? ''] ?? NEUTRAL_COLOR,
                strokeWidth: 1.25,
                strokeOpacity: 0.5,
              }}
              isAnimationActive={false}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
      <div className="mt-1 grid grid-cols-2 px-2 text-[10px] tracking-wide text-neutral-600 uppercase">
        <span className="text-left">Lagging</span>
        <span className="text-right">Weakening</span>
      </div>
    </Panel>
  )
}

import type { Regime } from '../api/types'
import { regimeStyle } from '../lib/regime'
import { Panel } from './Panel'

interface RegimeCardProps {
  regime: Regime
}

const METHODOLOGY = `Deterministic, rule-based classification — no AI. Rules are checked in a fixed priority order and the first match wins: 1) Broad Risk-Off, 2) Defensive Rotation, 3) Broad Risk-On, 4) Internal Rotation, 5) Mixed (fallback, none matched). Each rule looks at SPY 5-day return, sector breadth and dispersion, and cross-asset confirmations (credit, gold, Treasuries, VIX). Full thresholds: docs/data-methodology.md.`

export function RegimeCard({ regime }: RegimeCardProps) {
  const style = regimeStyle(regime.name)

  return (
    <Panel title="Market Regime" titleTooltip={METHODOLOGY}>
      <div className="flex flex-wrap items-center gap-3">
        <span className={`rounded-full border px-3 py-1 text-sm font-semibold ${style.className}`}>
          {style.label}
        </span>
        <span className="text-xs tracking-wide text-neutral-500 uppercase">
          Confidence: {regime.confidence}
        </span>
      </div>
      <ul className="mt-3 space-y-1 text-sm text-neutral-300">
        {regime.reasons.map((reason) => (
          <li key={reason} className="flex gap-2">
            <span className="text-neutral-600">•</span>
            <span>{reason}</span>
          </li>
        ))}
      </ul>
    </Panel>
  )
}

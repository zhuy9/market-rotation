import type { Regime } from '../api/types'
import { regimeStyle } from '../lib/regime'
import { Panel } from './Panel'

interface RegimeCardProps {
  regime: Regime
}

export function RegimeCard({ regime }: RegimeCardProps) {
  const style = regimeStyle(regime.name)

  return (
    <Panel title="Market Regime">
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

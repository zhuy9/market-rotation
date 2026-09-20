interface RegimeStyle {
  label: string
  className: string
}

const REGIME_STYLES: Record<string, RegimeStyle> = {
  BROAD_RISK_ON: {
    label: 'Broad Risk-On',
    className: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  },
  BROAD_RISK_OFF: {
    label: 'Broad Risk-Off',
    className: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
  },
  DEFENSIVE_ROTATION: {
    label: 'Defensive Rotation',
    className: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  },
  INTERNAL_ROTATION: {
    label: 'Internal Rotation',
    className: 'bg-sky-500/15 text-sky-400 border-sky-500/30',
  },
  MIXED: {
    label: 'Mixed / Unclear',
    className: 'bg-neutral-500/15 text-neutral-300 border-neutral-500/30',
  },
}

const FALLBACK_STYLE: RegimeStyle = {
  label: 'Unknown',
  className: 'bg-neutral-500/15 text-neutral-300 border-neutral-500/30',
}

export function regimeStyle(name: string): RegimeStyle {
  return REGIME_STYLES[name] ?? { ...FALLBACK_STYLE, label: name }
}

export const QUADRANT_COLOR: Record<string, string> = {
  LEADING: '#34d399',
  IMPROVING: '#38bdf8',
  WEAKENING: '#fbbf24',
  LAGGING: '#fb7185',
}

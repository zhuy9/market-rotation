export function formatPercent(value: number | null): string {
  if (value === null) return 'n/a'
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`
}

export function returnColorClass(value: number | null): string {
  if (value === null) return 'text-neutral-500'
  return value > 0 ? 'text-emerald-400' : value < 0 ? 'text-rose-400' : 'text-neutral-400'
}

function format(value: string | null, options: Intl.DateTimeFormatOptions): string {
  if (value === null) return 'n/a'
  return new Date(value).toLocaleString('en-US', options)
}

// Daily bars are stamped at midnight, so rendering a clock time would be
// precision the data does not have. Show the trading date only.
export function formatTradingDate(value: string | null): string {
  return format(value, { dateStyle: 'medium' })
}

// A real wall-clock moment (when the provider was last polled), labelled with
// the viewer's timezone so "how fresh is this" is unambiguous.
export function formatRetrievedAt(value: string | null): string {
  // dateStyle/timeStyle cannot be combined with timeZoneName, so the parts are
  // spelled out individually to keep the timezone label.
  return format(value, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
  })
}

// Flows arrive in dollars and run from single millions to several billion, so
// the unit is chosen per value rather than fixed.
export function formatFlow(value: number | null): string {
  if (value === null) return 'n/a'
  const millions = value / 1e6
  const sign = millions >= 0 ? '+' : '-'
  const magnitude = Math.abs(millions)
  return magnitude >= 1000
    ? `${sign}$${(magnitude / 1000).toFixed(2)}B`
    : `${sign}$${magnitude.toFixed(0)}M`
}

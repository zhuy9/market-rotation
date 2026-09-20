export function formatPercent(value: number | null): string {
  if (value === null) return 'n/a'
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`
}

export function returnColorClass(value: number | null): string {
  if (value === null) return 'text-neutral-500'
  return value > 0 ? 'text-emerald-400' : value < 0 ? 'text-rose-400' : 'text-neutral-400'
}

export function formatTimestamp(value: string | null): string {
  if (value === null) return 'n/a'
  return new Date(value).toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

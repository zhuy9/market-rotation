interface RefreshButtonProps {
  onRefresh: () => void
  isRefreshing: boolean
}

export function RefreshButton({ onRefresh, isRefreshing }: RefreshButtonProps) {
  return (
    <button
      type="button"
      onClick={onRefresh}
      disabled={isRefreshing}
      className="rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-1.5 text-sm font-medium text-neutral-100 transition hover:bg-neutral-700 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {isRefreshing ? 'Refreshing…' : 'Refresh Data'}
    </button>
  )
}

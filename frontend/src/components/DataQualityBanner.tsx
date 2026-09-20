interface DataQualityBannerProps {
  isStale: boolean
  warnings: string[]
}

export function DataQualityBanner({ isStale, warnings }: DataQualityBannerProps) {
  if (!isStale && warnings.length === 0) return null

  return (
    <div className="space-y-1 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-300">
      {isStale && (
        <p className="font-semibold">STALE DATA — latest observation is older than expected.</p>
      )}
      {warnings.map((warning) => (
        <p key={warning}>{warning}</p>
      ))}
    </div>
  )
}

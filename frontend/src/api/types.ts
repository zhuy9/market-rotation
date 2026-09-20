export interface Regime {
  name: string
  confidence: string
  reasons: string[]
}

export interface Breadth {
  positive: number
  total: number
  ratio: number | null
}

export interface SectorRow {
  symbol: string
  name: string
  return_1d: number | null
  return_5d: number | null
  return_20d: number | null
  vs_spy_5d: number | null
  vs_spy_20d: number | null
  quadrant: string | null
}

export interface CrossAssetRow {
  symbol: string
  name: string
  category: string
  return_1d: number | null
  return_5d: number | null
  return_20d: number | null
}

export interface Ratio {
  return_1d: number | null
  return_5d: number | null
  return_20d: number | null
}

export interface Dashboard {
  as_of: string
  provider: string
  data_timestamp: string | null
  is_stale: boolean
  regime: Regime
  sectors: SectorRow[]
  cross_asset: CrossAssetRow[]
  breadth_1d: Breadth
  breadth_5d: Breadth
  dispersion_1d: number | null
  dispersion_5d: number | null
  defensive_spread_5d: number | null
  ratios: Record<string, Ratio>
  warnings: string[]
}

export interface RefreshResult {
  status: string
  updated_symbols: number
  failed_symbols: string[]
  as_of: string
}

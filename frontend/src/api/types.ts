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

export interface RotationPoint {
  x: number | null
  y: number | null
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
  trail: RotationPoint[]
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

/** The two ratio proxies the backend always reports: equal-weight breadth
 *  (RSP/SPY) and credit risk (HYG/LQD). */
export interface Ratios {
  rsp_spy: Ratio
  hyg_lqd: Ratio
}

export interface Dashboard {
  as_of: string
  provider: string
  data_timestamp: string | null
  retrieved_at: string | null
  is_stale: boolean
  regime: Regime
  sectors: SectorRow[]
  cross_asset: CrossAssetRow[]
  breadth_1d: Breadth
  breadth_5d: Breadth
  dispersion_1d: number | null
  dispersion_5d: number | null
  defensive_spread_5d: number | null
  ratios: Ratios
  warnings: string[]
}

export interface RefreshResult {
  status: string
  updated_symbols: number
  failed_symbols: string[]
  as_of: string
}

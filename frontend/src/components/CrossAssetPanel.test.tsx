import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { CrossAssetRow } from '../api/types'
import { CrossAssetPanel } from './CrossAssetPanel'

function row(overrides: Partial<CrossAssetRow>): CrossAssetRow {
  return {
    symbol: 'SPY',
    name: 'S&P 500',
    category: 'equity',
    return_1d: 0.001,
    return_5d: 0.004,
    return_20d: 0.012,
    ...overrides,
  }
}

describe('CrossAssetPanel', () => {
  it('groups instruments by asset class', () => {
    render(
      <CrossAssetPanel
        rows={[
          row({ symbol: 'SPY', category: 'equity' }),
          row({ symbol: 'TLT', category: 'rates' }),
          row({ symbol: 'GLD', category: 'commodities' }),
        ]}
      />,
    )

    expect(screen.getByText('Equities')).toBeInTheDocument()
    expect(screen.getByText('Rates')).toBeInTheDocument()
    expect(screen.getByText('Commodities')).toBeInTheDocument()
  })

  it('omits asset classes that have no instruments', () => {
    render(<CrossAssetPanel rows={[row({ symbol: 'SPY', category: 'equity' })]} />)

    expect(screen.queryByText('Credit')).not.toBeInTheDocument()
    expect(screen.queryByText('Volatility')).not.toBeInTheDocument()
  })

  it('shows 1D, 5D and 20D returns for each instrument', () => {
    render(<CrossAssetPanel rows={[row({ symbol: 'IWM', category: 'equity' })]} />)

    const item = screen.getByText('IWM').closest('li')!
    expect(within(item).getByText('+0.10%')).toBeInTheDocument()
    expect(within(item).getByText('+0.40%')).toBeInTheDocument()
    expect(within(item).getByText('+1.20%')).toBeInTheDocument()
  })

  it('falls back to the raw category name for an unrecognised asset class', () => {
    render(<CrossAssetPanel rows={[row({ symbol: 'BTC', category: 'crypto' })]} />)

    expect(screen.queryByText('BTC')).not.toBeInTheDocument() // not in the configured order
  })

  it('shows n/a for an instrument with missing data', () => {
    render(<CrossAssetPanel rows={[row({ symbol: 'USO', return_1d: null })]} />)

    expect(screen.getByText('n/a')).toBeInTheDocument()
  })
})

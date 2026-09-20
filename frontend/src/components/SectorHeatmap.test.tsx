import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { SectorRow } from '../api/types'
import { SectorHeatmap } from './SectorHeatmap'

function makeSector(overrides: Partial<SectorRow>): SectorRow {
  return {
    symbol: 'XLK',
    name: 'Technology',
    return_1d: 0.01,
    return_5d: 0.02,
    return_20d: 0.03,
    vs_spy_5d: 0.01,
    vs_spy_20d: 0.01,
    quadrant: 'LEADING',
    trail: [],
    ...overrides,
  }
}

const SECTORS: SectorRow[] = [
  makeSector({ symbol: 'XLK', return_5d: 0.02 }),
  makeSector({ symbol: 'XLE', return_5d: -0.03 }),
  makeSector({ symbol: 'XLU', return_5d: 0.05 }),
]

describe('SectorHeatmap', () => {
  it('renders one row per sector', () => {
    render(<SectorHeatmap sectors={SECTORS} />)

    expect(screen.getByText('XLK')).toBeInTheDocument()
    expect(screen.getByText('XLE')).toBeInTheDocument()
    expect(screen.getByText('XLU')).toBeInTheDocument()
  })

  it('sorts descending by 5D return by default', () => {
    render(<SectorHeatmap sectors={SECTORS} />)

    const rows = screen.getAllByRole('row').slice(1) // skip header
    const firstCellText = rows[0].querySelector('td')?.textContent
    expect(firstCellText).toBe('XLU') // highest 5D return (+5%)
  })

  it('reverses order when the same column header is clicked again', () => {
    render(<SectorHeatmap sectors={SECTORS} />)

    fireEvent.click(screen.getByRole('button', { name: /^5D/ }))

    const rows = screen.getAllByRole('row').slice(1)
    const firstCellText = rows[0].querySelector('td')?.textContent
    expect(firstCellText).toBe('XLE') // lowest 5D return (-3%) after reversing
  })

  it('exposes sortable columns as keyboard-operable buttons', () => {
    render(<SectorHeatmap sectors={SECTORS} />)

    // Every numeric column sorts, so every one needs to be reachable by keyboard.
    expect(screen.getAllByRole('button')).toHaveLength(5)
  })

  it('reports the active sort column and direction to assistive tech', () => {
    render(<SectorHeatmap sectors={SECTORS} />)

    const sorted = screen.getAllByRole('columnheader').find((h) => h.textContent?.startsWith('5D'))
    expect(sorted).toHaveAttribute('aria-sort', 'descending')

    fireEvent.click(screen.getByRole('button', { name: /^5D/ }))
    expect(sorted).toHaveAttribute('aria-sort', 'ascending')
  })

  it('sorts sectors with missing data to the bottom in either direction', () => {
    const withGap = [
      makeSector({ symbol: 'XLK', return_5d: 0.02 }),
      makeSector({ symbol: 'XLRE', return_5d: null }),
      makeSector({ symbol: 'XLE', return_5d: -0.03 }),
    ]
    render(<SectorHeatmap sectors={withGap} />)

    const tickers = () =>
      screen
        .getAllByRole('row')
        .slice(1)
        .map((r) => r.querySelector('td')?.textContent)

    expect(tickers()).toEqual(['XLK', 'XLE', 'XLRE'])

    fireEvent.click(screen.getByRole('button', { name: /^5D/ }))
    expect(tickers()).toEqual(['XLE', 'XLK', 'XLRE'])
  })

  it('shows missing data as n/a instead of crashing', () => {
    render(<SectorHeatmap sectors={[makeSector({ symbol: 'XLRE', return_1d: null })]} />)

    expect(screen.getAllByText('n/a').length).toBeGreaterThan(0)
  })
})

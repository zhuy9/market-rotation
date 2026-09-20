import { render, screen } from '@testing-library/react'
import { cloneElement, type ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'

import type { SectorRow } from '../api/types'
import { RelativeRotationChart } from './RelativeRotationChart'

interface ChartSize {
  width?: number
  height?: number
}

// ResponsiveContainer measures its parent, which is always 0x0 in jsdom, so the
// chart would render nothing at all. Giving the inner chart a fixed size makes
// the sector labels assertable. The layout it produces is still approximate, so
// these tests cover which sectors get plotted -- not pixel positions or the
// per-session trail dots, which only a real browser lays out correctly.
vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof import('recharts')>()
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactElement<ChartSize> }) =>
      cloneElement(children, { width: 800, height: 400 }),
  }
})

function sector(overrides: Partial<SectorRow>): SectorRow {
  return {
    symbol: 'XLK',
    name: 'Technology',
    return_1d: 0.01,
    return_5d: 0.02,
    return_20d: 0.03,
    vs_spy_5d: 0.01,
    vs_spy_20d: 0.02,
    quadrant: 'LEADING',
    trail: [],
    ...overrides,
  }
}

describe('RelativeRotationChart', () => {
  it('labels all four quadrants (PRD section 38)', () => {
    render(<RelativeRotationChart sectors={[sector({})]} />)

    for (const label of ['Leading', 'Improving', 'Weakening', 'Lagging']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })

  it('plots every sector that has both coordinates', () => {
    render(
      <RelativeRotationChart
        sectors={[
          sector({ symbol: 'XLK' }),
          sector({ symbol: 'XLE', quadrant: 'LAGGING', vs_spy_5d: -0.01, vs_spy_20d: -0.02 }),
          sector({ symbol: 'XLU', quadrant: 'IMPROVING', vs_spy_5d: 0.01, vs_spy_20d: -0.02 }),
        ]}
      />,
    )

    expect(screen.getByText('XLK')).toBeInTheDocument()
    expect(screen.getByText('XLE')).toBeInTheDocument()
    expect(screen.getByText('XLU')).toBeInTheDocument()
  })

  it('omits a sector whose coordinates are unknown instead of guessing a quadrant', () => {
    render(
      <RelativeRotationChart
        sectors={[
          sector({ symbol: 'XLK' }),
          sector({ symbol: 'XLRE', vs_spy_20d: null, quadrant: null }),
        ]}
      />,
    )

    expect(screen.getByText('XLK')).toBeInTheDocument()
    expect(screen.queryByText('XLRE')).not.toBeInTheDocument()
  })
})

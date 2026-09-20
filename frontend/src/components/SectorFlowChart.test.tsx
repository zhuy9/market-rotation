import { fireEvent, render, screen } from '@testing-library/react'
import { cloneElement, type ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'

import type { Flows } from '../api/types'
import { SectorFlowChart } from './SectorFlowChart'

interface ChartSize {
  width?: number
  height?: number
}

// ResponsiveContainer measures its parent, which is always 0x0 in jsdom, so the
// chart renders nothing without a fixed size. These tests cover which sectors
// are plotted and how the window control behaves -- not bar geometry, which
// only a real browser lays out.
vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof import('recharts')>()
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactElement<ChartSize> }) =>
      cloneElement(children, { width: 800, height: 400 }),
  }
})

function buildFlows(overrides: Partial<Flows> = {}): Flows {
  return {
    as_of: '2026-09-17T00:00:00',
    windows: [1, 5, 20],
    sectors: [
      { symbol: 'XLK', name: 'Technology', flows: { '1D': -103e6, '5D': -282e6, '20D': -692e6 } },
      { symbol: 'XLRE', name: 'Real Estate', flows: { '1D': 352e6, '5D': 275e6, '20D': 152e6 } },
    ],
    ...overrides,
  }
}

describe('SectorFlowChart', () => {
  it('announces every plotted sector and its flow, since the chart is an SVG', () => {
    render(<SectorFlowChart flows={buildFlows()} />)

    expect(screen.getByText(/Technology: -\$692M/)).toBeInTheDocument()
    expect(screen.getByText(/Real Estate: \+\$152M/)).toBeInTheDocument()
  })

  it('defaults to the longest window, which is the headline number', () => {
    render(<SectorFlowChart flows={buildFlows()} />)

    expect(screen.getByRole('button', { name: '20D' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '1D' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('switches window when another is chosen', () => {
    render(<SectorFlowChart flows={buildFlows()} />)

    fireEvent.click(screen.getByRole('button', { name: '1D' }))

    expect(screen.getByRole('button', { name: '1D' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '20D' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('omits a sector whose flow for that window is unknown', () => {
    const flows = buildFlows({
      sectors: [
        { symbol: 'XLK', name: 'Technology', flows: { '1D': null, '20D': -692e6 } },
        { symbol: 'XLRE', name: 'Real Estate', flows: { '1D': 352e6, '20D': 152e6 } },
      ],
    })
    render(<SectorFlowChart flows={flows} />)

    fireEvent.click(screen.getByRole('button', { name: '1D' }))

    // Null is "no trustworthy flow", not zero, so the bar is left out entirely.
    expect(screen.queryByText(/Technology/)).not.toBeInTheDocument()
    expect(screen.getByText(/Real Estate: \+\$352M/)).toBeInTheDocument()
  })

  it('explains an empty window instead of drawing an axis with no bars', () => {
    const flows = buildFlows({
      sectors: [{ symbol: 'XLK', name: 'Technology', flows: { '1D': null, '20D': null } }],
    })
    render(<SectorFlowChart flows={flows} />)

    expect(screen.getByText(/no flow data for the 20D window/i)).toBeInTheDocument()
  })

  it('shows the date the flows are as of', () => {
    render(<SectorFlowChart flows={buildFlows()} />)

    expect(screen.getByText(/as of Sep 17, 2026/)).toBeInTheDocument()
  })
})

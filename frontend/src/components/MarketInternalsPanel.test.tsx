import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { MarketInternalsPanel } from './MarketInternalsPanel'

function renderPanel(overrides: Partial<Parameters<typeof MarketInternalsPanel>[0]> = {}) {
  return render(
    <MarketInternalsPanel
      breadth5d={{ positive: 8, total: 11, ratio: 8 / 11 }}
      dispersion5d={0.024}
      rsp5d={0.003}
      hygLqd5d={-0.001}
      growthValue5d={0.012}
      defensiveSpread5d={0.016}
      {...overrides}
    />,
  )
}

describe('MarketInternalsPanel', () => {
  it('shows every internal with their numeric values', () => {
    renderPanel()

    expect(screen.getByText('8 / 11')).toBeInTheDocument() // sector breadth
    expect(screen.getByText('+2.40%')).toBeInTheDocument() // dispersion
    expect(screen.getByText('+0.30%')).toBeInTheDocument() // RSP vs SPY
    expect(screen.getByText('-0.10%')).toBeInTheDocument() // HYG vs LQD
    expect(screen.getByText('+1.60%')).toBeInTheDocument() // defensive spread
    expect(screen.getByText('+1.20%')).toBeInTheDocument() // IVW vs IVE
  })

  it('explains each metric rather than relying on the label alone', () => {
    renderPanel()

    const explanations = screen.getAllByRole('tooltip')
    expect(explanations).toHaveLength(6)
  })

  it('shows n/a for metrics with missing data instead of breaking', () => {
    renderPanel({
      dispersion5d: null,
      rsp5d: null,
      hygLqd5d: null,
      growthValue5d: null,
      defensiveSpread5d: null,
    })

    expect(screen.getAllByText('n/a')).toHaveLength(5)
  })
})

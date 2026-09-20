import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { RegimeCard } from './RegimeCard'

describe('RegimeCard', () => {
  it('shows the human-readable regime label, confidence, and reasons', () => {
    render(
      <RegimeCard
        regime={{
          name: 'DEFENSIVE_ROTATION',
          confidence: 'high',
          reasons: ['Defensive sectors outperformed cyclical sectors by +1.6%.'],
        }}
      />,
    )

    expect(screen.getByText('Defensive Rotation')).toBeInTheDocument()
    expect(screen.getByText(/confidence: high/i)).toBeInTheDocument()
    expect(
      screen.getByText('Defensive sectors outperformed cyclical sectors by +1.6%.'),
    ).toBeInTheDocument()
  })

  it('falls back gracefully for an unrecognized regime name', () => {
    render(<RegimeCard regime={{ name: 'SOMETHING_NEW', confidence: 'low', reasons: [] }} />)

    expect(screen.getByText('SOMETHING_NEW')).toBeInTheDocument()
  })
})

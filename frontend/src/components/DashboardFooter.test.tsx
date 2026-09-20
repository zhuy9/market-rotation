import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DashboardFooter } from './DashboardFooter'

describe('DashboardFooter', () => {
  it('states plainly that this is not financial advice', () => {
    render(<DashboardFooter />)

    expect(screen.getByText(/not financial advice/i)).toBeInTheDocument()
  })

  it('repeats that regimes are inferred from price, not measured fund flows', () => {
    render(<DashboardFooter />)

    expect(screen.getByText(/does not measure actual money flows/i)).toBeInTheDocument()
  })

  it('attributes the data source and links the source code, safely', () => {
    render(<DashboardFooter />)

    const source = screen.getByRole('link', { name: /source code/i })
    expect(source).toHaveAttribute('href', 'https://github.com/zhuy9/market-rotation')

    for (const link of screen.getAllByRole('link')) {
      expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    }
    expect(screen.getByRole('link', { name: /yfinance/i })).toBeInTheDocument()
  })
})

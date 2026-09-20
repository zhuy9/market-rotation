import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { InfoTooltip } from './InfoTooltip'

describe('InfoTooltip', () => {
  it('renders the explanatory text for assistive tech / hover reveal', () => {
    render(<InfoTooltip text="Explains what this number means." />)

    expect(screen.getByRole('tooltip')).toHaveTextContent('Explains what this number means.')
  })
})

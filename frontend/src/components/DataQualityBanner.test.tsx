import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DataQualityBanner } from './DataQualityBanner'

describe('DataQualityBanner', () => {
  it('renders nothing when the data is current and complete', () => {
    const { container } = render(<DataQualityBanner isStale={false} warnings={[]} />)

    expect(container).toBeEmptyDOMElement()
  })

  it('labels stale data explicitly rather than presenting it as current', () => {
    render(<DataQualityBanner isStale warnings={[]} />)

    expect(screen.getByText(/stale data/i)).toBeInTheDocument()
  })

  it('lists every data-quality warning from the backend', () => {
    render(
      <DataQualityBanner
        isStale={false}
        warnings={['USO data is unavailable.', 'Latest TLT observation is stale.']}
      />,
    )

    expect(screen.getByText('USO data is unavailable.')).toBeInTheDocument()
    expect(screen.getByText('Latest TLT observation is stale.')).toBeInTheDocument()
  })
})

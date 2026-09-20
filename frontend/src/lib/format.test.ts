import { describe, expect, it } from 'vitest'

import { formatPercent, formatTimestamp, returnColorClass } from './format'

describe('formatPercent', () => {
  it('formats a positive value with a leading plus sign', () => {
    expect(formatPercent(0.0421)).toBe('+4.21%')
  })

  it('formats a negative value without a double sign', () => {
    expect(formatPercent(-0.013)).toBe('-1.30%')
  })

  it('returns n/a for missing data', () => {
    expect(formatPercent(null)).toBe('n/a')
  })
})

describe('returnColorClass', () => {
  it('is green for positive, red for negative, neutral for zero or missing', () => {
    expect(returnColorClass(0.01)).toContain('emerald')
    expect(returnColorClass(-0.01)).toContain('rose')
    expect(returnColorClass(0)).toContain('neutral')
    expect(returnColorClass(null)).toContain('neutral')
  })
})

describe('formatTimestamp', () => {
  it('returns n/a for a missing timestamp', () => {
    expect(formatTimestamp(null)).toBe('n/a')
  })

  it('formats an ISO timestamp into a readable string', () => {
    expect(formatTimestamp('2026-09-19T20:00:00Z')).not.toBe('n/a')
  })
})

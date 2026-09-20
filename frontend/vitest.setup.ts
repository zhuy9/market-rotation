import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Vitest runs without `globals`, so Testing Library's automatic cleanup never
// registers itself. Without this the rendered DOM accumulates across tests in
// a file and a query can match a previous test's render instead of this one's.
afterEach(cleanup)

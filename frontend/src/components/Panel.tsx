import type { ReactNode } from 'react'

import { InfoTooltip } from './InfoTooltip'

interface PanelProps {
  title: string
  titleTooltip?: string
  children: ReactNode
}

export function Panel({ title, titleTooltip, children }: PanelProps) {
  return (
    <section className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
      <h2 className="mb-3 flex items-center text-xs font-semibold tracking-wider text-neutral-400 uppercase">
        {title}
        {titleTooltip && <InfoTooltip text={titleTooltip} width="w-64" placement="bottom" />}
      </h2>
      {children}
    </section>
  )
}

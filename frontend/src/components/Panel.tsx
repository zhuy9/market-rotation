import type { ReactNode } from 'react'

interface PanelProps {
  title: string
  children: ReactNode
  className?: string
}

export function Panel({ title, children, className = '' }: PanelProps) {
  return (
    <section className={`rounded-xl border border-neutral-800 bg-neutral-900/60 p-4 ${className}`}>
      <h2 className="mb-3 text-xs font-semibold tracking-wider text-neutral-400 uppercase">{title}</h2>
      {children}
    </section>
  )
}

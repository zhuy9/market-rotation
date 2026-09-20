interface InfoTooltipProps {
  text: string
}

export function InfoTooltip({ text }: InfoTooltipProps) {
  return (
    <span className="group relative ml-1 inline-flex cursor-help items-center align-middle">
      <span
        className="flex h-3.5 w-3.5 items-center justify-center rounded-full border border-neutral-600 text-[9px] leading-none text-neutral-500"
        aria-hidden="true"
      >
        i
      </span>
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1.5 w-48 -translate-x-1/2 rounded-md border border-neutral-700 bg-neutral-800 px-2.5 py-1.5 text-xs font-normal text-neutral-200 opacity-0 shadow-lg transition-opacity group-hover:opacity-100"
      >
        {text}
      </span>
    </span>
  )
}

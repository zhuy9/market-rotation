interface InfoTooltipProps {
  text: string
  width?: string
  placement?: 'top' | 'bottom'
}

const PLACEMENT_CLASSES: Record<'top' | 'bottom', string> = {
  top: 'bottom-full mb-1.5',
  bottom: 'top-full mt-1.5',
}

export function InfoTooltip({ text, width = 'w-48', placement = 'top' }: InfoTooltipProps) {
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
        className={`pointer-events-none absolute left-1/2 z-10 ${width} -translate-x-1/2 rounded-md border border-neutral-700 bg-neutral-800 px-2.5 py-1.5 text-xs font-normal normal-case text-neutral-200 opacity-0 shadow-lg transition-opacity group-hover:opacity-100 ${PLACEMENT_CLASSES[placement]}`}
      >
        {text}
      </span>
    </span>
  )
}

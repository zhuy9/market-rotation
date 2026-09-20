const REPOSITORY_URL = 'https://github.com/zhuy9/market-rotation'
const YFINANCE_URL = 'https://pypi.org/project/yfinance/'

const linkClass =
  'text-neutral-400 underline decoration-neutral-700 underline-offset-2 transition hover:text-neutral-200 hover:decoration-neutral-400 focus-visible:rounded-xs focus-visible:outline focus-visible:outline-neutral-500'

export function DashboardFooter() {
  return (
    <footer className="mt-2 border-t border-neutral-800 pt-4 text-xs leading-relaxed text-neutral-500">
      <p>
        <span className="font-semibold text-neutral-300">Not financial advice.</span> This dashboard
        is for personal research and education. It infers rotation and risk regimes from relative
        price behaviour — it does not measure actual money flows, and it does not predict prices.
        Data may be delayed, incomplete or wrong; verify it independently before acting on it.
      </p>
      <p className="mt-2">
        Market data from Yahoo Finance via{' '}
        <a className={linkClass} href={YFINANCE_URL} target="_blank" rel="noopener noreferrer">
          yfinance
        </a>
        , an unofficial API — you are responsible for complying with Yahoo&rsquo;s terms of use.{' '}
        <span aria-hidden="true">·</span>{' '}
        <a className={linkClass} href={REPOSITORY_URL} target="_blank" rel="noopener noreferrer">
          Source code
        </a>{' '}
        <span aria-hidden="true">·</span> MIT License
      </p>
    </footer>
  )
}

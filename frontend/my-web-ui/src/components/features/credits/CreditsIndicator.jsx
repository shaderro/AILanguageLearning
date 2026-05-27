/**
 * Navbar usage indicator — subtle credits display with usage popover.
 */
import { useState, useRef, useEffect } from 'react'
import { useUIText } from '../../../i18n/useUIText'
import { formatCredits, isCreditsInsufficient } from '../../../utils/creditsUtils'

const CreditsIndicator = ({ tokenBalance, role, onOpenUsage }) => {
  const t = useUIText()
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

  const amount = formatCredits(tokenBalance)
  const low = isCreditsInsufficient(tokenBalance, role)

  useEffect(() => {
    if (!open) return
    const onDocClick = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onDocClick)
    return () => document.removeEventListener('mousedown', onDocClick)
  }, [open])

  return (
    <div className="relative" ref={rootRef}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={[
          'inline-flex items-baseline gap-1 px-2 py-1 rounded-md text-xs transition-colors',
          'text-gray-500 hover:text-gray-700 hover:bg-gray-50',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-200',
        ].join(' ')}
        aria-expanded={open}
        aria-haspopup="dialog"
      >
        <span className="tabular-nums font-medium text-gray-600">{amount}</span>
        <span className="hidden sm:inline text-gray-400">{t('credits')}</span>
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-64 rounded-lg border border-gray-200 bg-white shadow-lg z-30 p-4"
          role="dialog"
          aria-label={t('Credits remaining')}
        >
          <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
            {t('Credits remaining')}
          </p>
          <p className="mt-1 text-2xl font-semibold tabular-nums text-gray-900">{amount}</p>
          {low && (
            <p className="mt-1 text-xs text-gray-500">{t('Running low')}</p>
          )}
          <p className="mt-3 text-sm leading-relaxed text-gray-500">
            {t('Used for AI explanations and analysis.')}
          </p>

          <div className="mt-4 pt-3 border-t border-gray-100 space-y-2">
            <p className="text-xs text-gray-400">{t('Billing — coming soon')}</p>
            {onOpenUsage && (
              <button
                type="button"
                onClick={() => {
                  setOpen(false)
                  onOpenUsage()
                }}
                className="text-xs text-gray-600 hover:text-gray-900 transition-colors"
              >
                {t('View usage details')} →
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default CreditsIndicator

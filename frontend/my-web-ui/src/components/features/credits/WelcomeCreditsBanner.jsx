/**
 * One-time welcome banner for new users who received signup credits.
 */
import { useState } from 'react'
import { useUIText } from '../../../i18n/useUIText'
import { NEW_USER_SIGNUP_CREDITS } from '../../../utils/creditsUtils'

const WelcomeCreditsBanner = ({ credits = NEW_USER_SIGNUP_CREDITS, onDismiss }) => {
  const t = useUIText()
  const [visible, setVisible] = useState(true)

  if (!visible) return null

  const handleDismiss = () => {
    setVisible(false)
    onDismiss?.()
  }

  const title = t('You received {n} free credits').replace('{n}', String(credits))

  return (
    <div
      className="fixed top-16 right-4 z-40 max-w-sm rounded-lg border border-gray-200 bg-white shadow-md px-4 py-3"
      role="status"
    >
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900">{title}</p>
          <p className="mt-0.5 text-sm text-gray-500">
            {t('Used for AI explanations and analysis.')}
          </p>
        </div>
        <button
          type="button"
          onClick={handleDismiss}
          className="shrink-0 text-gray-400 hover:text-gray-600 transition-colors p-0.5"
          aria-label="Dismiss"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  )
}

export default WelcomeCreditsBanner

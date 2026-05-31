/**
 * Navbar credits — opens in-app billing modal (not settings).
 */
import { useBilling } from '../../../contexts/BillingContext'
import { useUIText } from '../../../i18n/useUIText'
import { formatCredits, isCreditsInsufficient } from '../../../utils/creditsUtils'

const CreditsIndicator = ({ tokenBalance, role }) => {
  const t = useUIText()
  const { openBilling } = useBilling()

  const amount = formatCredits(tokenBalance)
  const low = isCreditsInsufficient(tokenBalance, role)

  return (
    <button
      type="button"
      onClick={() => openBilling({ variant: 'usage', trigger: 'header' })}
      className={[
        'inline-flex items-baseline gap-1 px-2 py-1 rounded-md text-xs transition-colors',
        'text-gray-500 hover:text-gray-700 hover:bg-gray-50',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-200',
        low ? 'ring-1 ring-amber-200 bg-amber-50/50' : '',
      ].join(' ')}
      aria-label={t('Credits remaining')}
    >
      <span className={`tabular-nums font-medium ${low ? 'text-amber-700' : 'text-gray-600'}`}>
        {amount}
      </span>
      <span className="hidden sm:inline text-gray-400">{t('credits')}</span>
    </button>
  )
}

export default CreditsIndicator

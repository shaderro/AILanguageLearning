import { useBilling } from '../../../contexts/BillingContext'
import { useUIText } from '../../../i18n/useUIText'
import { formatCredits } from '../../../utils/creditsUtils'
import { CREDIT_PACKS, PRO_MONTHLY_CREDITS, PRO_PRICE_LABEL, planLabel } from '../../../utils/billingConstants'

export default function BillingModal() {
  const t = useUIText()
  const {
    modalState,
    plan,
    tokenBalance,
    isUpgrading,
    isBuyingCredits,
    billingError,
    closeBilling,
    simulateUpgrade,
    simulateBuyCredits,
  } = useBilling()

  if (!modalState.open) return null

  const isPaywall = modalState.variant === 'paywall'
  const creditsDisplay = formatCredits(tokenBalance)
  const isPro = plan === 'pro'

  const paywallMessage = (() => {
    if (modalState.trigger === 'chat') {
      return t('You need credits to continue chatting with AI.')
    }
    if (modalState.trigger === 'annotation') {
      return t('You need credits to use AI explanations on this word.')
    }
    return t('You need credits to use this AI feature.')
  })()

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 px-4">
      <div
        className="w-full max-w-md rounded-xl border border-gray-200 bg-white shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="billing-modal-title"
      >
        <div className="border-b border-gray-100 px-5 py-4">
          {isPaywall ? (
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-600">
              {t('Credits exhausted')}
            </p>
          ) : (
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
              {t('Usage & billing')}
            </p>
          )}
          <h2 id="billing-modal-title" className="mt-1 text-lg font-semibold text-gray-900">
            {isPaywall ? t('Upgrade to keep learning') : t('Your plan & credits')}
          </h2>
        </div>

        <div className="px-5 py-4 space-y-4">
          {isPaywall && (
            <p className="text-sm text-gray-600">{paywallMessage}</p>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-gray-50 p-3">
              <p className="text-xs text-gray-500">{t('Current plan')}</p>
              <p className="mt-1 text-lg font-semibold text-gray-900">{planLabel(plan, t)}</p>
            </div>
            <div className="rounded-lg bg-gray-50 p-3">
              <p className="text-xs text-gray-500">{t('Credits remaining')}</p>
              <p className="mt-1 text-lg font-semibold tabular-nums text-gray-900">{creditsDisplay}</p>
            </div>
          </div>

          <p className="text-sm text-gray-500">
            {t('Used for AI explanations and analysis.')}
          </p>

          {!isPro && (
            <div className="rounded-lg border border-indigo-100 bg-indigo-50/60 p-4">
              <p className="text-sm font-medium text-gray-900">
                Pro · {PRO_PRICE_LABEL}{t('/month')}
              </p>
              <p className="mt-1 text-xs text-gray-600">
                {t('Includes {n} credits per month (simulated)').replace('{n}', String(PRO_MONTHLY_CREDITS))}
              </p>
              <button
                type="button"
                onClick={simulateUpgrade}
                disabled={isUpgrading || isBuyingCredits}
                className="mt-3 w-full rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
              >
                {isUpgrading ? t('处理中...') : t('Upgrade to Pro (simulated)')}
              </button>
            </div>
          )}

          <div className="rounded-lg border border-dashed border-gray-200 p-3">
            <p className="text-xs font-medium text-gray-500 mb-2">{t('Buy credits (placeholder)')}</p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => simulateBuyCredits(CREDIT_PACKS.small)}
                disabled={isUpgrading || isBuyingCredits}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                +{CREDIT_PACKS.small}
              </button>
              <button
                type="button"
                onClick={() => simulateBuyCredits(CREDIT_PACKS.large)}
                disabled={isUpgrading || isBuyingCredits}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                +{CREDIT_PACKS.large}
              </button>
            </div>
          </div>

          {billingError && (
            <p className="text-sm text-red-600">{billingError}</p>
          )}
        </div>

        <div className="flex justify-end border-t border-gray-100 px-5 py-4">
          <button
            type="button"
            onClick={closeBilling}
            disabled={isUpgrading}
            className="rounded-lg px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
          >
            {t('Close')}
          </button>
        </div>
      </div>
    </div>
  )
}

import { useBillingSandbox } from './BillingSandboxContext'

export default function CheckoutModal() {
  const {
    checkoutOpen,
    checkoutPhase,
    lastCheckoutResult,
    closeCheckout,
    confirmCheckout,
    plans,
  } = useBillingSandbox()

  if (!checkoutOpen) return null

  const pro = plans.pro

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div
        className="w-full max-w-md rounded-xl border border-gray-200 bg-white shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="sandbox-checkout-title"
      >
        <div className="border-b border-gray-100 px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-600">
            Fake checkout · Not Paddle
          </p>
          <h2 id="sandbox-checkout-title" className="mt-1 text-lg font-semibold text-gray-900">
            Upgrade to {pro.name}
          </h2>
        </div>

        <div className="px-5 py-4 space-y-4">
          {checkoutPhase === 'review' && (
            <>
              <div className="rounded-lg bg-gray-50 p-4 text-sm text-gray-700 space-y-2">
                <div className="flex justify-between">
                  <span>{pro.name} subscription</span>
                  <span className="font-medium">{pro.priceLabel} / {pro.interval}</span>
                </div>
                <div className="flex justify-between text-gray-500">
                  <span>Included credits (simulated)</span>
                  <span>+{pro.includedCredits}</span>
                </div>
              </div>
              <p className="text-xs text-gray-500">
                Step 1: Review · Step 2: Confirm · Step 3: Simulated success · Step 4: Local state updates only.
              </p>
            </>
          )}

          {checkoutPhase === 'processing' && (
            <div className="py-8 text-center">
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-gray-800" />
              <p className="mt-3 text-sm text-gray-600">Processing simulated payment…</p>
            </div>
          )}

          {checkoutPhase === 'success' && lastCheckoutResult && (
            <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-900 space-y-1">
              <p className="font-semibold">Payment successful (simulated)</p>
              <p>Plan: {lastCheckoutResult.plan.toUpperCase()}</p>
              <p>Credits granted: +{lastCheckoutResult.creditsGranted}</p>
              <p>New balance: {lastCheckoutResult.totalCredits}</p>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t border-gray-100 px-5 py-4">
          {checkoutPhase === 'review' && (
            <>
              <button
                type="button"
                onClick={closeCheckout}
                className="rounded-lg px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmCheckout}
                className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
              >
                Confirm payment
              </button>
            </>
          )}
          {checkoutPhase === 'success' && (
            <button
              type="button"
              onClick={closeCheckout}
              className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

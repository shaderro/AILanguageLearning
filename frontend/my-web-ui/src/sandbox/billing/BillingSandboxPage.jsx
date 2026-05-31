import { useBillingSandbox } from './BillingSandboxContext'
import SimulationBanner from './SimulationBanner'
import CheckoutModal from './CheckoutModal'

function Panel({ title, children, className = '' }) {
  return (
    <section className={`rounded-xl border border-slate-700 bg-slate-900 p-5 ${className}`}>
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400 mb-4">{title}</h2>
      {children}
    </section>
  )
}

function ActionButton({ onClick, children, variant = 'default', disabled = false }) {
  const base = 'rounded-lg px-3 py-2 text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed'
  const styles = {
    default: 'border border-slate-600 bg-slate-800 text-slate-100 hover:bg-slate-700',
    primary: 'bg-indigo-500 text-white hover:bg-indigo-400',
    danger: 'border border-red-500/50 text-red-300 hover:bg-red-500/10',
    success: 'border border-emerald-500/50 text-emerald-300 hover:bg-emerald-500/10',
  }
  return (
    <button type="button" onClick={onClick} disabled={disabled} className={`${base} ${styles[variant]}`}>
      {children}
    </button>
  )
}

export default function BillingSandboxPage() {
  const {
    state,
    plans,
    costs,
    creditPacks,
    reset,
    addCredits,
    upgradePro,
    downgrade,
    openProCheckout,
    simulateUsage,
    buyCreditPack,
    continueLimitedMode,
    isExhausted,
  } = useBillingSandbox()

  const currentPlan = state.plan === 'pro' ? plans.pro : plans.free
  const canAfford = (cost) => state.credits >= cost

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <CheckoutModal />

      <div className="mx-auto max-w-5xl px-4 py-8 space-y-6">
        <SimulationBanner subtitle="Validate pricing UX, upgrade timing, and credit consumption — isolated localStorage state only." />

        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-slate-500">/sandbox/billing</p>
            <h1 className="mt-1 text-2xl font-bold">Billing Sandbox</h1>
          </div>
          <div className="flex gap-2 text-sm">
            <a href="/sandbox" className="text-slate-400 hover:text-slate-200">Hub</a>
            <span className="text-slate-600">·</span>
            <a href="/" className="text-slate-400 hover:text-slate-200">Main app</a>
          </div>
        </header>

        {/* Current state */}
        <div className="grid gap-4 sm:grid-cols-3">
          <Panel title="Current plan">
            <p className="text-3xl font-bold capitalize">{currentPlan.name}</p>
            <p className="mt-1 text-sm text-slate-400">
              {currentPlan.priceLabel}
              {currentPlan.interval !== 'forever' ? ` / ${currentPlan.interval}` : ''}
            </p>
            {state.limitedMode && (
              <p className="mt-2 text-xs text-amber-400 font-medium">Limited mode active (simulation)</p>
            )}
          </Panel>
          <Panel title="Credits balance">
            <p className="text-3xl font-bold tabular-nums">{state.credits}</p>
            <p className="mt-1 text-sm text-slate-400">Display credits (not production tokens)</p>
          </Panel>
          <Panel title="Developer controls">
            <div className="flex flex-wrap gap-2">
              <ActionButton onClick={reset}>Reset state</ActionButton>
              <ActionButton onClick={() => addCredits(100)} variant="success">+100</ActionButton>
              <ActionButton onClick={() => addCredits(500)} variant="success">+500</ActionButton>
              <ActionButton onClick={upgradePro} variant="primary" disabled={state.plan === 'pro'}>
                Upgrade to Pro (instant)
              </ActionButton>
              <ActionButton onClick={downgrade} variant="danger" disabled={state.plan === 'free'}>
                Downgrade to Free
              </ActionButton>
            </div>
          </Panel>
        </div>

        {/* Pricing */}
        <Panel title="Pricing (simulated)">
          <div className="grid gap-4 md:grid-cols-2">
            <div className={`rounded-lg border p-5 ${state.plan === 'free' ? 'border-indigo-500/60 bg-indigo-500/5' : 'border-slate-700'}`}>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{plans.free.name}</h3>
                {state.plan === 'free' && (
                  <span className="text-xs rounded bg-slate-700 px-2 py-0.5">Current</span>
                )}
              </div>
              <p className="mt-2 text-2xl font-bold">{plans.free.priceLabel}</p>
              <p className="mt-2 text-sm text-slate-400">{plans.free.description}</p>
              <ul className="mt-4 text-sm text-slate-300 space-y-1">
                <li>· {plans.free.includedCredits} credits included</li>
                <li>· Basic reading & AI features</li>
              </ul>
            </div>

            <div className={`rounded-lg border p-5 ${state.plan === 'pro' ? 'border-indigo-500/60 bg-indigo-500/5' : 'border-slate-700'}`}>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{plans.pro.name}</h3>
                {state.plan === 'pro' && (
                  <span className="text-xs rounded bg-indigo-600 px-2 py-0.5">Current</span>
                )}
              </div>
              <p className="mt-2 text-2xl font-bold">
                {plans.pro.priceLabel}
                <span className="text-base font-normal text-slate-400"> / month</span>
              </p>
              <p className="mt-2 text-sm text-slate-400">{plans.pro.description}</p>
              <ul className="mt-4 text-sm text-slate-300 space-y-1">
                <li>· {plans.pro.includedCredits} credits / month (on upgrade)</li>
                <li>· Simulated priority & higher limits</li>
              </ul>
              <div className="mt-4">
                <ActionButton
                  onClick={openProCheckout}
                  variant="primary"
                  disabled={state.plan === 'pro'}
                >
                  {state.plan === 'pro' ? 'Already on Pro' : 'Upgrade (fake checkout)'}
                </ActionButton>
              </div>
            </div>
          </div>
        </Panel>

        {/* Credit consumption */}
        <Panel title="Credit consumption simulator">
          <p className="text-sm text-slate-400 mb-4">
            Each action deducts credits locally. Insufficient balance triggers exhaustion UI below.
          </p>
          <div className="flex flex-wrap gap-2">
            <ActionButton
              onClick={() => simulateUsage('chat')}
              disabled={!canAfford(costs.chat)}
            >
              Simulate Chat (−{costs.chat})
            </ActionButton>
            <ActionButton
              onClick={() => simulateUsage('annotation')}
              disabled={!canAfford(costs.annotation)}
            >
              Simulate Annotation (−{costs.annotation})
            </ActionButton>
            <ActionButton
              onClick={() => simulateUsage('summarization')}
              disabled={!canAfford(costs.summarization)}
            >
              Simulate Summarization (−{costs.summarization})
            </ActionButton>
          </div>
        </Panel>

        {/* Exhaustion */}
        {isExhausted && (
          <Panel title="Credits exhausted" className="border-amber-500/40 bg-amber-500/5">
            <p className="text-lg font-semibold text-amber-200">Credits exhausted</p>
            <p className="mt-2 text-sm text-amber-100/80">
              Your sandbox balance is 0. Choose how a user might react in this scenario.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <ActionButton onClick={continueLimitedMode} variant="default">
                Continue in limited mode
              </ActionButton>
              <ActionButton onClick={() => buyCreditPack('small')} variant="success">
                Simulate buy +{creditPacks.small}
              </ActionButton>
              <ActionButton onClick={() => buyCreditPack('large')} variant="success">
                Simulate buy +{creditPacks.large}
              </ActionButton>
              {state.plan === 'free' && (
                <ActionButton onClick={openProCheckout} variant="primary">
                  Upgrade to Pro
                </ActionButton>
              )}
            </div>
            {state.limitedMode && (
              <p className="mt-3 text-xs text-slate-400 font-mono">
                Limited mode: no real feature lockout in this sandbox — label only for UX testing.
              </p>
            )}
          </Panel>
        )}

        {/* Activity log */}
        <Panel title="Activity log">
          {state.activityLog.length === 0 ? (
            <p className="text-sm text-slate-500 font-mono">No events yet. Reset or simulate an action.</p>
          ) : (
            <ul className="space-y-2 max-h-64 overflow-y-auto font-mono text-xs">
              {state.activityLog.map((entry) => (
                <li key={entry.ts + entry.message} className="text-slate-400 border-b border-slate-800 pb-2">
                  <span className="text-slate-500">{entry.ts}</span>
                  <span className="ml-2 text-slate-300">{entry.message}</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  )
}

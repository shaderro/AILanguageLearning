import SimulationBanner from './SimulationBanner'

export default function BillingSandboxHome() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-3xl px-4 py-10 space-y-8">
        <SimulationBanner subtitle="Developer sandbox for subscription and credits UX — fully isolated from LinkText production." />

        <header>
          <p className="font-mono text-xs uppercase tracking-widest text-slate-400">LinkText /sandbox</p>
          <h1 className="mt-2 text-3xl font-bold">Billing Sandbox Hub</h1>
          <p className="mt-2 text-slate-400 text-sm max-w-xl">
            Test pricing perception, upgrade timing, credit consumption, and exhaustion flows without Paddle or real user accounts.
          </p>
        </header>

        <section className="rounded-xl border border-slate-700 bg-slate-900 p-6 space-y-4">
          <h2 className="text-lg font-semibold">Available sandboxes</h2>
          <a
            href="/sandbox/billing"
            className="flex items-center justify-between rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-4 py-4 hover:bg-indigo-500/20 transition-colors"
          >
            <div>
              <p className="font-medium text-indigo-200">Billing & credits</p>
              <p className="text-sm text-slate-400 mt-1">
                Free vs Pro plans, fake checkout, credit consumption, exhaustion UX
              </p>
            </div>
            <span className="text-indigo-300 text-sm">Open →</span>
          </a>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 text-sm text-slate-400 space-y-2 font-mono">
          <p>Storage key: linktext_billing_sandbox_state_v1</p>
          <p>Routes: /sandbox · /sandbox/billing</p>
          <p>
            <a href="/" className="text-indigo-400 hover:underline">← Back to main app</a>
          </p>
        </section>
      </div>
    </div>
  )
}

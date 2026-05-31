/** Isolated billing sandbox state — never touches production user / API. */

export const SANDBOX_STORAGE_KEY = 'linktext_billing_sandbox_state_v1'

export const SANDBOX_PLANS = {
  free: {
    id: 'free',
    name: 'Free',
    priceLabel: '$0',
    interval: 'forever',
    includedCredits: 80,
    description: 'Starter credits for trying LinkText.',
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    priceLabel: '$9',
    interval: 'month',
    includedCredits: 1000,
    description: 'Simulated subscription with monthly credit refill on upgrade.',
  },
}

export const SANDBOX_COSTS = {
  chat: 3,
  annotation: 8,
  summarization: 12,
}

export const SANDBOX_CREDIT_PACKS = {
  small: 300,
  large: 700,
}

export const DEFAULT_SANDBOX_STATE = {
  plan: 'free',
  credits: SANDBOX_PLANS.free.includedCredits,
  limitedMode: false,
  activityLog: [],
}

function safeParse(raw) {
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function loadSandboxState() {
  if (typeof window === 'undefined') {
    return { ...DEFAULT_SANDBOX_STATE, activityLog: [] }
  }
  const parsed = safeParse(window.localStorage.getItem(SANDBOX_STORAGE_KEY))
  if (!parsed || typeof parsed !== 'object') {
    return { ...DEFAULT_SANDBOX_STATE, activityLog: [] }
  }
  const plan = parsed.plan === 'pro' ? 'pro' : 'free'
  const credits = Number.isFinite(Number(parsed.credits))
    ? Math.max(0, Number(parsed.credits))
    : DEFAULT_SANDBOX_STATE.credits
  return {
    plan,
    credits,
    limitedMode: Boolean(parsed.limitedMode),
    activityLog: Array.isArray(parsed.activityLog) ? parsed.activityLog.slice(0, 50) : [],
  }
}

export function saveSandboxState(state) {
  if (typeof window === 'undefined') return
  const payload = {
    plan: state.plan,
    credits: state.credits,
    limitedMode: state.limitedMode,
    activityLog: state.activityLog.slice(0, 50),
  }
  window.localStorage.setItem(SANDBOX_STORAGE_KEY, JSON.stringify(payload))
}

export function appendLog(state, message) {
  const entry = {
    ts: new Date().toISOString(),
    message,
  }
  return {
    ...state,
    activityLog: [entry, ...state.activityLog].slice(0, 50),
  }
}

export function resetSandboxState() {
  const next = { ...DEFAULT_SANDBOX_STATE, activityLog: [] }
  saveSandboxState(next)
  return appendLog(next, 'Reset to Free plan with 80 credits.')
}

export function addCredits(state, amount, reason) {
  const delta = Math.max(0, Number(amount) || 0)
  const next = appendLog(
    {
      ...state,
      credits: state.credits + delta,
      limitedMode: false,
    },
    reason || `Added ${delta} credits.`,
  )
  saveSandboxState(next)
  return next
}

export function setPlan(state, plan, logMessage) {
  const nextPlan = plan === 'pro' ? 'pro' : 'free'
  const next = appendLog({ ...state, plan: nextPlan }, logMessage)
  saveSandboxState(next)
  return next
}

export function simulateProUpgrade(state) {
  let next = setPlan(state, 'pro', 'Upgraded to Pro (simulated checkout).')
  next = addCredits(next, SANDBOX_PLANS.pro.includedCredits, `Pro upgrade grant: +${SANDBOX_PLANS.pro.includedCredits} credits.`)
  return next
}

export function simulateDowngrade(state) {
  const next = appendLog({ ...state, plan: 'free' }, 'Downgraded to Free (simulated).')
  saveSandboxState(next)
  return next
}

export function consumeCredits(state, cost, label) {
  const amount = Math.max(0, Number(cost) || 0)
  if (state.credits < amount) {
    return { ok: false, state, error: 'insufficient' }
  }
  const next = appendLog(
    {
      ...state,
      credits: state.credits - amount,
      limitedMode: state.credits - amount === 0 ? state.limitedMode : false,
    },
    `${label}: −${amount} credits (balance ${state.credits - amount}).`,
  )
  saveSandboxState(next)
  return { ok: true, state: next }
}

export function enableLimitedMode(state) {
  const next = appendLog({ ...state, limitedMode: true }, 'Continued in limited mode (simulation only — no real lockout).')
  saveSandboxState(next)
  return next
}

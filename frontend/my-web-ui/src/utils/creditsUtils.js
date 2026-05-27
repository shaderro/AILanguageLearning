/** AI usage credits (display layer). Backend stores raw token units: 10_000 units = 1 credit. */

export const CREDITS_PER_TOKEN_UNIT = 10000
export const NEW_USER_SIGNUP_CREDITS = 80
export const INSUFFICIENT_CREDITS_THRESHOLD = 1000

export const formatCredits = (tokenBalance) => {
  if (tokenBalance === undefined || tokenBalance === null) {
    return '0'
  }
  const credits = Math.max(0, tokenBalance) / CREDITS_PER_TOKEN_UNIT
  return Number.isInteger(credits) ? String(credits) : credits.toFixed(1)
}

export const getCreditsValue = (tokenBalance) => {
  if (tokenBalance === undefined || tokenBalance === null) {
    return 0
  }
  return Math.max(0, tokenBalance) / CREDITS_PER_TOKEN_UNIT
}

export const isCreditsInsufficient = (tokenBalance, role = 'user') => {
  if (role === 'admin') {
    return false
  }
  if (tokenBalance === undefined || tokenBalance === null) {
    return true
  }
  return tokenBalance < INSUFFICIENT_CREDITS_THRESHOLD
}

const WELCOME_PENDING_KEY = 'pending_welcome_credits'

export const welcomeCreditsSeenKey = (userId) => `welcome_credits_seen_${userId}`

export const markPendingWelcomeCredits = () => {
  try {
    localStorage.setItem(WELCOME_PENDING_KEY, '1')
  } catch {
    // ignore
  }
}

export const clearPendingWelcomeCredits = () => {
  try {
    localStorage.removeItem(WELCOME_PENDING_KEY)
  } catch {
    // ignore
  }
}

export const shouldShowWelcomeCredits = (userId) => {
  if (!userId || typeof window === 'undefined') return false
  try {
    if (localStorage.getItem(welcomeCreditsSeenKey(userId))) return false
    return localStorage.getItem(WELCOME_PENDING_KEY) === '1'
  } catch {
    return false
  }
}

export const dismissWelcomeCredits = (userId) => {
  if (!userId || typeof window === 'undefined') return
  try {
    localStorage.setItem(welcomeCreditsSeenKey(userId), '1')
    clearPendingWelcomeCredits()
  } catch {
    // ignore
  }
}

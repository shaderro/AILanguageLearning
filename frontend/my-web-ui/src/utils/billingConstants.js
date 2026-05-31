/** In-app billing constants (display credits; backend stores token units). */

export const PRO_MONTHLY_CREDITS = 1000
export const PRO_PRICE_LABEL = '$9'
export const CREDIT_PACKS = {
  small: 300,
  large: 700,
}

export const normalizePlan = (plan) => (plan === 'pro' ? 'pro' : 'free')

export const planLabel = (plan, t) => {
  const p = normalizePlan(plan)
  return p === 'pro' ? (t('Pro') || 'Pro') : (t('Free') || 'Free')
}

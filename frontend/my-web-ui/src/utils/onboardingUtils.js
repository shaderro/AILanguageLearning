const PENDING_ONBOARDING_KEY = 'pending_onboarding'

export const onboardingCompletedKey = (userId) => `onboarding_completed_${userId}`

export const markPendingOnboarding = () => {
  try {
    localStorage.setItem(PENDING_ONBOARDING_KEY, '1')
  } catch {
    // ignore
  }
}

export const clearPendingOnboarding = () => {
  try {
    localStorage.removeItem(PENDING_ONBOARDING_KEY)
  } catch {
    // ignore
  }
}

export const userNeedsOnboarding = (userInfo) => {
  if (!userInfo) return false
  const hasContentLang = Boolean(userInfo.content_language && String(userInfo.content_language).trim())
  const hasLanguagesList = Array.isArray(userInfo.languages_list) && userInfo.languages_list.length > 0
  return !hasContentLang && !hasLanguagesList
}

export const shouldShowOnboarding = (userId, userInfo) => {
  if (!userId || typeof window === 'undefined') return false
  try {
    if (localStorage.getItem(onboardingCompletedKey(userId))) return false
    if (userNeedsOnboarding(userInfo)) return true
    return localStorage.getItem(PENDING_ONBOARDING_KEY) === '1'
  } catch {
    return false
  }
}

export const completeOnboarding = (userId) => {
  if (!userId || typeof window === 'undefined') return
  try {
    localStorage.setItem(onboardingCompletedKey(userId), '1')
    clearPendingOnboarding()
  } catch {
    // ignore
  }
}

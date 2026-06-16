import { readStoredHeaderLanguages } from './headerLanguageStorage'

/** @deprecated Legacy global key — migrated to per-user keys */
const LEGACY_PENDING_ONBOARDING_KEY = 'pending_onboarding'

export const onboardingCompletedKey = (userId) => `onboarding_completed_${userId}`

export const pendingOnboardingKey = (userId) => `pending_onboarding_${userId}`

const migrateLegacyPendingOnboarding = (userId) => {
  try {
    if (localStorage.getItem(LEGACY_PENDING_ONBOARDING_KEY) !== '1') return false
    localStorage.setItem(pendingOnboardingKey(userId), '1')
    localStorage.removeItem(LEGACY_PENDING_ONBOARDING_KEY)
    return true
  } catch {
    return false
  }
}

export const markPendingOnboarding = (userId) => {
  try {
    if (userId != null) {
      localStorage.setItem(pendingOnboardingKey(userId), '1')
    }
    localStorage.removeItem(LEGACY_PENDING_ONBOARDING_KEY)
  } catch {
    // ignore
  }
}

export const clearPendingOnboarding = (userId) => {
  try {
    if (userId != null) {
      localStorage.removeItem(pendingOnboardingKey(userId))
    }
    localStorage.removeItem(LEGACY_PENDING_ONBOARDING_KEY)
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

/** 线上老用户：有使用记录、本地语言缓存，或账号已存在超过 1 天 */
export const isReturningUser = (userInfo, userId) => {
  if (!userInfo) return false

  if (Number(userInfo.total_tokens_used) > 0) return true

  if (userId != null && readStoredHeaderLanguages(userId)?.length > 0) return true

  if (userInfo.created_at) {
    const created = new Date(userInfo.created_at)
    if (!Number.isNaN(created.getTime())) {
      const ageMs = Date.now() - created.getTime()
      if (ageMs > 24 * 60 * 60 * 1000) return true
    }
  }

  return false
}

export const shouldShowOnboarding = (userId, userInfo) => {
  if (!userId || typeof window === 'undefined') return false
  try {
    if (localStorage.getItem(onboardingCompletedKey(userId))) return false
    if (isReturningUser(userInfo, userId)) return false

    migrateLegacyPendingOnboarding(userId)

    const hasPendingFlag = localStorage.getItem(pendingOnboardingKey(userId)) === '1'
    if (!hasPendingFlag) return false

    return userNeedsOnboarding(userInfo) || hasPendingFlag
  } catch {
    return false
  }
}

export const completeOnboarding = (userId) => {
  if (!userId || typeof window === 'undefined') return
  try {
    localStorage.setItem(onboardingCompletedKey(userId), '1')
    clearPendingOnboarding(userId)
  } catch {
    // ignore
  }
}

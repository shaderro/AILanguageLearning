export const CONTENT_LANGUAGE_NAMES = [
  '中文',
  '英文',
  '西班牙语',
  '法语',
  '日语',
  '韩语',
  '德文',
  '阿拉伯语',
  '俄语',
]

export const LANGUAGE_CODE_TO_NAME = {
  zh: '中文',
  en: '英文',
  de: '德文',
  es: '西班牙语',
  fr: '法语',
  ja: '日语',
  ko: '韩语',
  ar: '阿拉伯语',
  ru: '俄语',
}

export const languageCodesToNames = (codes) => {
  if (!Array.isArray(codes)) return []
  return codes.map((code) => LANGUAGE_CODE_TO_NAME[code]).filter(Boolean)
}

export const getHeaderLanguageStorageKey = (userId) => {
  if (userId == null || userId === '') return null
  return `content_languages_chosen_${userId}`
}

export const readStoredHeaderLanguages = (userId) => {
  const key = getHeaderLanguageStorageKey(userId)
  if (!key || typeof window === 'undefined') return null

  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return null
    const valid = parsed.filter((lang) => CONTENT_LANGUAGE_NAMES.includes(lang))
    return valid.length > 0 ? valid : null
  } catch {
    return null
  }
}

export const writeStoredHeaderLanguages = (userId, names) => {
  const key = getHeaderLanguageStorageKey(userId)
  if (!key || typeof window === 'undefined') return []

  const valid = Array.from(
    new Set(names.filter((lang) => CONTENT_LANGUAGE_NAMES.includes(lang))),
  )
  if (valid.length === 0) return []

  try {
    window.localStorage.setItem(key, JSON.stringify(valid))
  } catch {
    // ignore
  }
  return valid
}

/**
 * 解析「正在学习」语言列表：已登录用户优先服务端 languages_list，避免 guest 缓存或默认德文污染。
 */
export const resolveHeaderLanguages = ({
  userId,
  isAuthenticated,
  userInfo,
  selectedLanguage,
  needsOnboarding = false,
}) => {
  if (isAuthenticated && Array.isArray(userInfo?.languages_list) && userInfo.languages_list.length > 0) {
    const fromServer = languageCodesToNames(userInfo.languages_list)
    if (fromServer.length > 0) return fromServer
  }

  if (isAuthenticated && needsOnboarding) {
    return []
  }

  const stored = readStoredHeaderLanguages(userId)
  if (stored?.length) return stored

  if (isAuthenticated) {
    if (userInfo?.content_language && LANGUAGE_CODE_TO_NAME[userInfo.content_language]) {
      return [LANGUAGE_CODE_TO_NAME[userInfo.content_language]]
    }
    return selectedLanguage ? [selectedLanguage] : []
  }

  return selectedLanguage ? [selectedLanguage] : ['德文']
}

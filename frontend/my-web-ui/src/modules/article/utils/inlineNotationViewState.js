const STORAGE_KEY = 'ailang:inline-notation-viewed'

const listeners = new Set()

function notifyListeners() {
  listeners.forEach((listener) => {
    try {
      listener()
    } catch {
      // ignore subscriber errors
    }
  })
}

export function subscribeInlineNotationViewState(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function readStore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw == null) return null
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return null
  }
}

function writeStore(store) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
  } catch {
    // ignore quota / private mode errors
  }
}

/**
 * 是否已查看过该 inline notation。
 * 仅当 localStorage 中明确记录为已查看时返回 true；新出现的 notation 默认未查看（显示绿点）。
 */
export function isInlineNotationViewed(articleId, notationKey) {
  const store = readStore()
  if (store == null) return false

  const articleKey = String(articleId)
  const viewedKeys = store[articleKey]
  if (!Array.isArray(viewedKeys)) return false

  return viewedKeys.includes(notationKey)
}

/** 标记 inline notation 已查看，并写入 localStorage */
export function markInlineNotationViewed(articleId, notationKey) {
  if (articleId == null || !notationKey) return

  const store = readStore() ?? {}
  const articleKey = String(articleId)
  const existing = Array.isArray(store[articleKey]) ? store[articleKey] : []

  if (existing.includes(notationKey)) return

  store[articleKey] = [...existing, notationKey]
  writeStore(store)
  notifyListeners()
}

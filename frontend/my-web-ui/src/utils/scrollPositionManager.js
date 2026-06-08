/**
 * 文章阅读进度管理器
 * 使用 localStorage 持久化保存页码与滚动位置，支持用户隔离
 */

const STORAGE_PREFIX = 'article_scroll_position_'
const PROGRESS_PREFIX = 'article_reading_progress_'

function normalizeArticleId(articleId) {
  return String(articleId)
}

function getStorageKey(userId, articleId) {
  return `${STORAGE_PREFIX}${userId}_${normalizeArticleId(articleId)}`
}

function getProgressKey(userId, articleId) {
  return `${PROGRESS_PREFIX}${userId}_${normalizeArticleId(articleId)}`
}

function parseProgressRaw(raw) {
  if (raw == null) return null
  try {
    const parsed = JSON.parse(raw)
    if (parsed && typeof parsed === 'object') {
      const pageIndex = Math.max(1, parseInt(parsed.pageIndex, 10) || 1)
      const scrollByPage =
        parsed.scrollByPage && typeof parsed.scrollByPage === 'object'
          ? Object.fromEntries(
              Object.entries(parsed.scrollByPage).map(([page, value]) => [
                String(page),
                Math.max(0, parseInt(value, 10) || 0),
              ]),
            )
          : {}
      return { pageIndex, scrollByPage }
    }
  } catch {
    // legacy plain-number scroll value
  }
  const legacyScroll = parseInt(raw, 10)
  if (!Number.isNaN(legacyScroll)) {
    return { pageIndex: 1, scrollByPage: { '1': legacyScroll } }
  }
  return null
}

/**
 * @returns {{ pageIndex: number, scrollByPage: Record<string, number> } | null}
 */
export function getArticleReadingProgress(userId, articleId) {
  if (!userId || !articleId) return null
  try {
    const progressRaw = localStorage.getItem(getProgressKey(userId, articleId))
    if (progressRaw != null) {
      return parseProgressRaw(progressRaw)
    }
    const legacyRaw = localStorage.getItem(getStorageKey(userId, articleId))
    return parseProgressRaw(legacyRaw)
  } catch (e) {
    console.warn('⚠️ [ReadingProgress] 获取阅读进度失败:', e)
    return null
  }
}

export function getArticleScrollForPage(userId, articleId, pageIndex) {
  const progress = getArticleReadingProgress(userId, articleId)
  if (!progress) return 0
  return progress.scrollByPage[String(pageIndex)] ?? 0
}

function writeArticleReadingProgress(userId, articleId, progress) {
  if (!userId || !articleId || !progress) return
  try {
    localStorage.setItem(getProgressKey(userId, articleId), JSON.stringify(progress))
    localStorage.removeItem(getStorageKey(userId, articleId))
  } catch (e) {
    console.warn('⚠️ [ReadingProgress] 保存阅读进度失败:', e)
  }
}

export function saveArticlePageIndex(userId, articleId, pageIndex) {
  if (!userId || !articleId) return
  const safePage = Math.max(1, parseInt(pageIndex, 10) || 1)
  const existing = getArticleReadingProgress(userId, articleId) || { pageIndex: 1, scrollByPage: {} }
  writeArticleReadingProgress(userId, articleId, {
    pageIndex: safePage,
    scrollByPage: existing.scrollByPage,
  })
}

export function saveArticleScrollForPage(userId, articleId, pageIndex, scrollTop) {
  if (!userId || !articleId) return
  const safePage = Math.max(1, parseInt(pageIndex, 10) || 1)
  const safeScroll = Math.max(0, parseInt(scrollTop, 10) || 0)
  const existing = getArticleReadingProgress(userId, articleId) || { pageIndex: safePage, scrollByPage: {} }
  writeArticleReadingProgress(userId, articleId, {
    pageIndex: existing.pageIndex || safePage,
    scrollByPage: {
      ...existing.scrollByPage,
      [String(safePage)]: safeScroll,
    },
  })
}

export function saveArticlePageAndScroll(userId, articleId, pageIndex, scrollTop) {
  if (!userId || !articleId) return
  const safePage = Math.max(1, parseInt(pageIndex, 10) || 1)
  const safeScroll = Math.max(0, parseInt(scrollTop, 10) || 0)
  const existing = getArticleReadingProgress(userId, articleId) || { pageIndex: 1, scrollByPage: {} }
  writeArticleReadingProgress(userId, articleId, {
    pageIndex: safePage,
    scrollByPage: {
      ...existing.scrollByPage,
      [String(safePage)]: safeScroll,
    },
  })
}

/** @deprecated use saveArticleScrollForPage / saveArticlePageAndScroll */
export function saveScrollPosition(userId, articleId, scrollTop) {
  saveArticlePageAndScroll(userId, articleId, 1, scrollTop)
}

/** @deprecated use getArticleScrollForPage */
export function getScrollPosition(userId, articleId) {
  return getArticleScrollForPage(userId, articleId, 1)
}

export function clearScrollPosition(userId, articleId) {
  if (!userId || !articleId) return
  try {
    localStorage.removeItem(getStorageKey(userId, articleId))
    localStorage.removeItem(getProgressKey(userId, articleId))
  } catch (e) {
    console.warn('⚠️ [ReadingProgress] 清除阅读进度失败:', e)
  }
}

export function clearAllScrollPositions(userId) {
  if (!userId) return
  try {
    const scrollPrefix = getStorageKey(userId, '')
    const progressPrefix = getProgressKey(userId, '')
    const keysToRemove = []
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i)
      if (key && (key.startsWith(scrollPrefix) || key.startsWith(progressPrefix))) {
        keysToRemove.push(key)
      }
    }
    keysToRemove.forEach((key) => localStorage.removeItem(key))
  } catch (e) {
    console.warn('⚠️ [ReadingProgress] 清除所有阅读进度失败:', e)
  }
}

export function debounce(func, wait) {
  let timeout
  let lastArgs = null

  const debounced = function executedFunction(...args) {
    lastArgs = args
    clearTimeout(timeout)
    timeout = setTimeout(() => {
      timeout = null
      lastArgs = null
      func(...args)
    }, wait)
  }

  debounced.flush = () => {
    if (!timeout) return
    clearTimeout(timeout)
    timeout = null
    const args = lastArgs || []
    lastArgs = null
    func(...args)
  }

  debounced.cancel = () => {
    clearTimeout(timeout)
    timeout = null
    lastArgs = null
  }

  return debounced
}

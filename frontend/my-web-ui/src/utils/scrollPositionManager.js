/**
 * 滚动位置管理器
 * 使用 localStorage 持久化保存文章滚动位置，支持用户隔离
 */

const STORAGE_PREFIX = 'article_scroll_position_'

/**
 * 获取存储键名（包含用户ID和文章ID）
 * @param {string|number} userId - 用户ID（登录用户）或游客ID
 * @param {string|number} articleId - 文章ID
 * @returns {string} 存储键名
 */
function getStorageKey(userId, articleId) {
  return `${STORAGE_PREFIX}${userId}_${articleId}`
}

/**
 * 保存滚动位置
 * @param {string|number} userId - 用户ID（登录用户）或游客ID
 * @param {string|number} articleId - 文章ID
 * @param {number} scrollTop - 滚动位置
 */
export function saveScrollPosition(userId, articleId, scrollTop) {
  if (!userId || !articleId) {
    return
  }
  
  try {
    const key = getStorageKey(userId, articleId)
    localStorage.setItem(key, String(scrollTop))
  } catch (e) {
    // localStorage 可能已满或不可用
    console.warn('⚠️ [ScrollPosition] 保存滚动位置失败:', e)
  }
}

/**
 * 获取滚动位置
 * @param {string|number} userId - 用户ID（登录用户）或游客ID
 * @param {string|number} articleId - 文章ID
 * @returns {number|null} 滚动位置，如果不存在则返回 null
 */
export function getScrollPosition(userId, articleId) {
  if (!userId || !articleId) {
    return null
  }
  
  try {
    const key = getStorageKey(userId, articleId)
    const saved = localStorage.getItem(key)
    if (saved === null) {
      return null
    }
    const position = parseInt(saved, 10)
    return isNaN(position) ? null : position
  } catch (e) {
    console.warn('⚠️ [ScrollPosition] 获取滚动位置失败:', e)
    return null
  }
}

/**
 * 清除滚动位置
 * @param {string|number} userId - 用户ID（登录用户）或游客ID
 * @param {string|number} articleId - 文章ID
 */
export function clearScrollPosition(userId, articleId) {
  if (!userId || !articleId) {
    return
  }
  
  try {
    const key = getStorageKey(userId, articleId)
    localStorage.removeItem(key)
  } catch (e) {
    console.warn('⚠️ [ScrollPosition] 清除滚动位置失败:', e)
  }
}

/**
 * 清除用户的所有滚动位置
 * @param {string|number} userId - 用户ID（登录用户）或游客ID
 */
export function clearAllScrollPositions(userId) {
  if (!userId) {
    return
  }
  
  try {
    const prefix = getStorageKey(userId, '')
    const keysToRemove = []
    
    // 遍历所有 localStorage 键
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(prefix)) {
        keysToRemove.push(key)
      }
    }
    
    keysToRemove.forEach(key => localStorage.removeItem(key))
    console.log(`✅ [ScrollPosition] 已清除用户 ${userId} 的 ${keysToRemove.length} 个滚动位置`)
  } catch (e) {
    console.warn('⚠️ [ScrollPosition] 清除所有滚动位置失败:', e)
  }
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}


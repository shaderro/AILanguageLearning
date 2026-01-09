/**
 * 复习进度管理器
 * 使用 localStorage 持久化保存复习进度，支持用户隔离
 */

const STORAGE_PREFIX = 'review_progress_'

/**
 * 获取存储键名（包含用户ID和复习类型）
 * @param {string|number} userId - 用户ID（登录用户）或游客ID
 * @param {string} reviewType - 复习类型：'vocab' 或 'grammar'
 * @returns {string} 存储键名
 */
function getStorageKey(userId, reviewType) {
  return `${STORAGE_PREFIX}${userId}_${reviewType}`
}

/**
 * 保存复习进度
 * @param {string|number} userId - 用户ID（登录用户）或游客ID
 * @param {string} reviewType - 复习类型：'vocab' 或 'grammar'
 * @param {Object} progress - 进度对象
 * @param {number} progress.currentIndex - 当前复习索引
 * @param {Array} progress.items - 复习项目列表（包含ID）
 * @param {Array} progress.results - 已完成的答案结果
 * @param {string} progress.filterHash - 筛选条件的哈希值（用于验证是否匹配）
 */
export function saveReviewProgress(userId, reviewType, progress) {
  if (!userId || !reviewType) {
    return
  }
  
  try {
    const key = getStorageKey(userId, reviewType)
    const data = {
      ...progress,
      savedAt: new Date().toISOString()
    }
    localStorage.setItem(key, JSON.stringify(data))
    console.log(`✅ [ReviewProgress] 保存${reviewType}复习进度:`, progress.currentIndex, '/', progress.items.length)
  } catch (e) {
    console.warn('⚠️ [ReviewProgress] 保存复习进度失败:', e)
  }
}

/**
 * 获取复习进度
 * @param {string|number} userId - 用户ID（登录用户）或游客ID
 * @param {string} reviewType - 复习类型：'vocab' 或 'grammar'
 * @returns {Object|null} 进度对象，如果不存在则返回 null
 */
export function getReviewProgress(userId, reviewType) {
  if (!userId || !reviewType) {
    return null
  }
  
  try {
    const key = getStorageKey(userId, reviewType)
    const saved = localStorage.getItem(key)
    if (!saved) {
      return null
    }
    
    const progress = JSON.parse(saved)
    
    // 检查进度是否过期（超过7天自动清除）
    if (progress.savedAt) {
      const savedDate = new Date(progress.savedAt)
      const now = new Date()
      const daysDiff = (now - savedDate) / (1000 * 60 * 60 * 24)
      if (daysDiff > 7) {
        console.log(`⚠️ [ReviewProgress] 复习进度已过期（${Math.floor(daysDiff)}天），自动清除`)
        clearReviewProgress(userId, reviewType)
        return null
      }
    }
    
    return progress
  } catch (e) {
    console.warn('⚠️ [ReviewProgress] 获取复习进度失败:', e)
    return null
  }
}

/**
 * 清除复习进度
 * @param {string|number} userId - 用户ID（登录用户）或游客ID
 * @param {string} reviewType - 复习类型：'vocab' 或 'grammar'
 */
export function clearReviewProgress(userId, reviewType) {
  if (!userId || !reviewType) {
    return
  }
  
  try {
    const key = getStorageKey(userId, reviewType)
    localStorage.removeItem(key)
    console.log(`✅ [ReviewProgress] 清除${reviewType}复习进度`)
  } catch (e) {
    console.warn('⚠️ [ReviewProgress] 清除复习进度失败:', e)
  }
}

/**
 * 生成筛选条件的哈希值（用于验证进度是否匹配当前筛选条件）
 * @param {Object} filters - 筛选条件对象
 * @returns {string} 哈希值
 */
export function generateFilterHash(filters) {
  // 简单的哈希函数，基于筛选条件的字符串表示
  const str = JSON.stringify(filters)
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32bit integer
  }
  return hash.toString()
}

/**
 * 验证进度是否匹配当前筛选条件
 * @param {Object} progress - 保存的进度对象
 * @param {string} currentFilterHash - 当前筛选条件的哈希值
 * @returns {boolean} 是否匹配
 */
export function validateProgress(progress, currentFilterHash) {
  if (!progress || !progress.filterHash) {
    return false
  }
  
  // 如果筛选条件不匹配，进度无效
  if (progress.filterHash !== currentFilterHash) {
    console.log('⚠️ [ReviewProgress] 筛选条件已改变，进度不匹配')
    return false
  }
  
  // 检查进度是否完整
  if (!progress.items || !Array.isArray(progress.items) || progress.items.length === 0) {
    return false
  }
  
  if (typeof progress.currentIndex !== 'number' || progress.currentIndex < 0) {
    return false
  }
  
  // 如果已经完成所有项目，进度无效
  if (progress.currentIndex >= progress.items.length) {
    return false
  }
  
  return true
}


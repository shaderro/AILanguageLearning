/**
 * 分页面状态管理器
 * 用于在localStorage中保存和恢复vocab、grammar、article页面的分页面状态
 */

const PAGE_STATE_PREFIX = 'page_state_'
const LANGUAGE_KEY = 'last_language'

/**
 * 保存页面的分页面状态
 * @param {string} pageType - 页面类型: 'vocab', 'grammar', 'article'
 * @param {object} state - 状态对象，例如 { selectedWordId: 123 } 或 { articleId: 'abc' }
 */
export const savePageState = (pageType, state) => {
  try {
    const key = `${PAGE_STATE_PREFIX}${pageType}`
    localStorage.setItem(key, JSON.stringify(state))
    console.log(`✅ [PageState] 保存 ${pageType} 页面状态:`, state)
  } catch (error) {
    console.error(`❌ [PageState] 保存 ${pageType} 页面状态失败:`, error)
  }
}

/**
 * 获取页面的分页面状态
 * @param {string} pageType - 页面类型: 'vocab', 'grammar', 'article'
 * @returns {object|null} 状态对象，如果不存在则返回null
 */
export const getPageState = (pageType) => {
  try {
    const key = `${PAGE_STATE_PREFIX}${pageType}`
    const data = localStorage.getItem(key)
    if (data) {
      const state = JSON.parse(data)
      console.log(`✅ [PageState] 获取 ${pageType} 页面状态:`, state)
      return state
    }
    return null
  } catch (error) {
    console.error(`❌ [PageState] 获取 ${pageType} 页面状态失败:`, error)
    return null
  }
}

/**
 * 清除页面的分页面状态
 * @param {string} pageType - 页面类型: 'vocab', 'grammar', 'article'，如果不提供则清除所有
 */
export const clearPageState = (pageType = null) => {
  try {
    if (pageType) {
      const key = `${PAGE_STATE_PREFIX}${pageType}`
      localStorage.removeItem(key)
      console.log(`✅ [PageState] 清除 ${pageType} 页面状态`)
    } else {
      // 清除所有页面状态
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith(PAGE_STATE_PREFIX)) {
          localStorage.removeItem(key)
        }
      })
      console.log(`✅ [PageState] 清除所有页面状态`)
    }
  } catch (error) {
    console.error(`❌ [PageState] 清除页面状态失败:`, error)
  }
}

/**
 * 保存当前语言
 * @param {string} language - 当前语言
 */
export const saveCurrentLanguage = (language) => {
  try {
    localStorage.setItem(LANGUAGE_KEY, language)
    console.log(`✅ [PageState] 保存当前语言:`, language)
  } catch (error) {
    console.error(`❌ [PageState] 保存当前语言失败:`, error)
  }
}

/**
 * 获取上次保存的语言
 * @returns {string|null} 语言字符串，如果不存在则返回null
 */
export const getLastLanguage = () => {
  try {
    return localStorage.getItem(LANGUAGE_KEY)
  } catch (error) {
    console.error(`❌ [PageState] 获取上次语言失败:`, error)
    return null
  }
}

/**
 * 检查语言是否发生变化，如果变化则清除所有页面状态
 * @param {string} currentLanguage - 当前语言
 */
export const checkLanguageChange = (currentLanguage) => {
  const lastLanguage = getLastLanguage()
  if (lastLanguage && lastLanguage !== currentLanguage) {
    console.log(`🔄 [PageState] 语言从 ${lastLanguage} 切换到 ${currentLanguage}，清除所有页面状态`)
    clearPageState()
  }
  saveCurrentLanguage(currentLanguage)
}


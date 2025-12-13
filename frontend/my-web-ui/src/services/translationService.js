/**
 * 轻量级翻译服务
 * 提供 hover 词典翻译功能（非 AI），作为 select → ask AI 之前的轻量翻译层
 */

// ==================== 系统语言获取 ====================

/**
 * 获取并normalize用户系统语言
 * @returns {string} 语言代码 'en' | 'zh' | 'de' | 'ja'，暂时只支持 'en' | 'zh'，其他 fallback 到 'en'
 */
export const getSystemLanguage = () => {
  if (typeof navigator === 'undefined') {
    return 'en' // 服务端渲染时默认返回英文
  }

  const systemLang = navigator.language || navigator.userLanguage || 'en'
  const langCode = systemLang.toLowerCase().split('-')[0] // 提取主语言代码，如 'zh-CN' -> 'zh'

  // Normalize 成支持的语言代码
  const normalizedMap = {
    'en': 'en',
    'zh': 'zh',
    'de': 'de',
    'ja': 'ja',
  }

  // 暂时只支持 en 和 zh，其他 fallback 到 en
  const supportedLanguages = ['en', 'zh']
  const normalized = normalizedMap[langCode] || 'en'
  
  return supportedLanguages.includes(normalized) ? normalized : 'en'
}

// ==================== 缓存管理 ====================

const CACHE_PREFIX = 'quick_translation_'
const CACHE_VERSION = 'v1'
const CACHE_EXPIRY_DAYS = 30 // 缓存30天

/**
 * 生成缓存key
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @returns {string} 缓存key
 */
const getCacheKey = (word, sourceLang, targetLang) => {
  const normalizedWord = word.toLowerCase().trim()
  return `${CACHE_PREFIX}${CACHE_VERSION}_${sourceLang}_${targetLang}_${normalizedWord}`
}

/**
 * 从localStorage获取缓存
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @returns {object|null} 缓存的翻译结果，格式: { translation: string, cachedAt: number }
 */
const getCachedTranslation = (word, sourceLang, targetLang) => {
  try {
    const key = getCacheKey(word, sourceLang, targetLang)
    const cached = localStorage.getItem(key)
    if (!cached) return null

    const data = JSON.parse(cached)
    const now = Date.now()
    const expiryTime = data.cachedAt + (CACHE_EXPIRY_DAYS * 24 * 60 * 60 * 1000)

    // 检查是否过期
    if (now > expiryTime) {
      localStorage.removeItem(key)
      return null
    }

    return data
  } catch (error) {
    console.error('❌ [TranslationService] 读取缓存失败:', error)
    return null
  }
}

/**
 * 保存翻译结果到localStorage
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @param {string} translation - 翻译结果
 */
const setCachedTranslation = (word, sourceLang, targetLang, translation) => {
  try {
    const key = getCacheKey(word, sourceLang, targetLang)
    const data = {
      translation,
      cachedAt: Date.now()
    }
    localStorage.setItem(key, JSON.stringify(data))
  } catch (error) {
    console.error('❌ [TranslationService] 保存缓存失败:', error)
    // localStorage可能已满，尝试清理旧缓存
    try {
      clearOldCache()
    } catch (clearError) {
      console.error('❌ [TranslationService] 清理旧缓存失败:', clearError)
    }
  }
}

/**
 * 清理过期的缓存
 */
const clearOldCache = () => {
  try {
    const now = Date.now()
    const keysToRemove = []

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(CACHE_PREFIX)) {
        try {
          const data = JSON.parse(localStorage.getItem(key))
          const expiryTime = data.cachedAt + (CACHE_EXPIRY_DAYS * 24 * 60 * 60 * 1000)
          if (now > expiryTime) {
            keysToRemove.push(key)
          }
        } catch (e) {
          // 无效的缓存项，也删除
          keysToRemove.push(key)
        }
      }
    }

    keysToRemove.forEach(key => localStorage.removeItem(key))
    if (keysToRemove.length > 0) {
      console.log(`🧹 [TranslationService] 清理了 ${keysToRemove.length} 个过期缓存`)
    }
  } catch (error) {
    console.error('❌ [TranslationService] 清理缓存失败:', error)
  }
}

// ==================== 内存缓存 ====================

// 内存缓存，避免同一会话中重复查询
const memoryCache = new Map()

/**
 * 从内存缓存获取翻译
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @returns {string|null} 翻译结果
 */
const getMemoryCache = (word, sourceLang, targetLang) => {
  const key = `${sourceLang}_${targetLang}_${word.toLowerCase().trim()}`
  return memoryCache.get(key) || null
}

/**
 * 保存翻译到内存缓存
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @param {string} translation - 翻译结果
 */
const setMemoryCache = (word, sourceLang, targetLang, translation) => {
  const key = `${sourceLang}_${targetLang}_${word.toLowerCase().trim()}`
  memoryCache.set(key, translation)
}

// ==================== 本地Vocabulary表查询 ====================

/**
 * 从本地vocabulary表查询翻译
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @param {Function} vocabListGetter - 获取词汇列表的函数（可选）
 * @returns {Promise<string|null>} 翻译结果
 */
const queryLocalVocab = async (word, sourceLang, targetLang, vocabListGetter = null) => {
  if (!vocabListGetter || typeof vocabListGetter !== 'function') {
    return null
  }

  try {
    const normalizedWord = word.toLowerCase().trim()
    const vocabList = vocabListGetter()

    // 在词汇列表中查找匹配的词汇
    const matchedVocab = vocabList.find(vocab => {
      const vocabBody = (vocab.vocab_body || '').toLowerCase().trim()
      const vocabLang = vocab.language || vocab.lang || ''

      // 检查语言是否匹配
      const langMatches = vocabLang === sourceLang || 
                         vocabLang === '中文' && sourceLang === 'zh' ||
                         vocabLang === '英文' && sourceLang === 'en' ||
                         vocabLang === '德文' && sourceLang === 'de'

      // 检查单词是否匹配（精确匹配或包含匹配）
      return langMatches && (vocabBody === normalizedWord || vocabBody.includes(normalizedWord))
    })

    if (matchedVocab && matchedVocab.translation) {
      return matchedVocab.translation
    }

    return null
  } catch (error) {
    console.error('❌ [TranslationService] 查询本地vocabulary失败:', error)
    return null
  }
}

// ==================== 外部API查询 ====================

/**
 * 使用MyMemory API查询翻译
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @returns {Promise<string|null>} 翻译结果
 */
const queryMyMemoryAPI = async (word, sourceLang, targetLang) => {
  try {
    // MyMemory API 对文本长度有限制（通常约500字符）
    // 对于长文本，截断到合理长度
    const MAX_LENGTH = 500
    let textToTranslate = word
    
    // 如果文本过长，截断并添加省略号
    if (textToTranslate.length > MAX_LENGTH) {
      // 尝试在句号、问号、感叹号处截断，保持语义完整
      const truncated = textToTranslate.substring(0, MAX_LENGTH)
      const lastSentenceEnd = Math.max(
        truncated.lastIndexOf('.'),
        truncated.lastIndexOf('?'),
        truncated.lastIndexOf('!')
      )
      
      if (lastSentenceEnd > MAX_LENGTH * 0.7) {
        // 如果找到的句子结束位置在70%之后，使用该位置
        textToTranslate = truncated.substring(0, lastSentenceEnd + 1)
      } else {
        // 否则在单词边界截断
        const lastSpace = truncated.lastIndexOf(' ')
        if (lastSpace > MAX_LENGTH * 0.7) {
          textToTranslate = truncated.substring(0, lastSpace) + '...'
        } else {
          textToTranslate = truncated + '...'
        }
      }
      
      console.log(`⚠️ [TranslationService] 文本过长(${word.length}字符)，截断到${textToTranslate.length}字符`)
    }
    
    // MyMemory API endpoint
    // 注意：免费API有请求限制，建议后续替换为其他API或自建服务
    const apiUrl = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(textToTranslate)}&langpair=${sourceLang}|${targetLang}`
    
    const response = await fetch(apiUrl)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    
    if (data.responseStatus === 200 && data.responseData && data.responseData.translatedText) {
      let translation = data.responseData.translatedText
      
      // 如果原文本被截断了，在翻译结果后添加提示
      if (word.length > MAX_LENGTH) {
        translation += ' (翻译已截断)'
      }
      
      return translation
    }

    return null
  } catch (error) {
    console.error('❌ [TranslationService] MyMemory API查询失败:', error)
    return null
  }
}

/**
 * 可替换的API实现接口
 * 可以替换为其他翻译API（如Google Translate、DeepL等）
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @returns {Promise<string|null>} 翻译结果
 */
export const defaultTranslationAPI = queryMyMemoryAPI

// ==================== 主查询函数 ====================

/**
 * 获取快速翻译（主函数）
 * 查询顺序：本地vocabulary表 → 内存缓存 → localStorage缓存 → 外部API
 * 
 * @param {string} word - 要翻译的单词
 * @param {string} sourceLang - 源语言代码（如 'de', 'en', 'zh'）
 * @param {string} targetLang - 目标语言代码（如 'en', 'zh'），默认使用系统语言
 * @param {object} options - 可选配置
 * @param {Function} options.vocabListGetter - 获取本地vocabulary列表的函数（可选）
 * @param {Function} options.apiProvider - 自定义API提供者（可选，默认使用MyMemory）
 * @returns {Promise<string|null>} 翻译结果，如果查询失败返回null
 */
export const getQuickTranslation = async (
  word,
  sourceLang,
  targetLang = null,
  options = {}
) => {
  if (!word || typeof word !== 'string' || word.trim().length === 0) {
    return null
  }

  // 如果没有指定目标语言，使用系统语言
  if (!targetLang) {
    targetLang = getSystemLanguage()
  }

  const normalizedWord = word.trim()
  const { vocabListGetter = null, debugLogger = null } = options
  
  // 确保 apiProvider 是函数，如果为 null 或 undefined 则使用默认值
  const apiProvider = options.apiProvider && typeof options.apiProvider === 'function' 
    ? options.apiProvider 
    : defaultTranslationAPI

  // 记录开始查询
  if (debugLogger) {
    debugLogger('info', `开始查询翻译: "${normalizedWord}"`, { sourceLang, targetLang })
  }

  // 1. 查询内存缓存
  const memoryCacheResult = getMemoryCache(normalizedWord, sourceLang, targetLang)
  if (memoryCacheResult) {
    const msg = `从内存缓存获取翻译: "${normalizedWord}" -> "${memoryCacheResult}"`
    console.log('💾 [TranslationService]', msg)
    if (debugLogger) {
      debugLogger('success', msg, { word: normalizedWord, translation: memoryCacheResult, source: 'memory' })
    }
    return memoryCacheResult
  }

  // 2. 查询localStorage缓存
  const cachedResult = getCachedTranslation(normalizedWord, sourceLang, targetLang)
  if (cachedResult && cachedResult.translation) {
    const msg = `从localStorage缓存获取翻译: "${normalizedWord}" -> "${cachedResult.translation}"`
    console.log('💾 [TranslationService]', msg)
    if (debugLogger) {
      debugLogger('success', msg, { word: normalizedWord, translation: cachedResult.translation, source: 'localStorage' })
    }
    // 同时更新内存缓存
    setMemoryCache(normalizedWord, sourceLang, targetLang, cachedResult.translation)
    return cachedResult.translation
  }

  // 3. 查询本地vocabulary表
  if (vocabListGetter) {
    if (debugLogger) {
      debugLogger('info', `查询本地vocabulary表: "${normalizedWord}"`, { sourceLang, targetLang })
    }
    const localVocabResult = await queryLocalVocab(normalizedWord, sourceLang, targetLang, vocabListGetter)
    if (localVocabResult) {
      const msg = `从本地vocabulary表获取翻译: "${normalizedWord}" -> "${localVocabResult}"`
      console.log('📚 [TranslationService]', msg)
      if (debugLogger) {
        debugLogger('success', msg, { word: normalizedWord, translation: localVocabResult, source: 'localVocab' })
      }
      // 保存到缓存
      setMemoryCache(normalizedWord, sourceLang, targetLang, localVocabResult)
      setCachedTranslation(normalizedWord, sourceLang, targetLang, localVocabResult)
      return localVocabResult
    }
  }

  // 4. 查询外部API
  if (debugLogger) {
    debugLogger('info', `查询外部API: "${normalizedWord}"`, { sourceLang, targetLang, api: 'MyMemory' })
  }
  try {
    const apiResult = await apiProvider(normalizedWord, sourceLang, targetLang)
    if (apiResult) {
      const msg = `从外部API获取翻译: "${normalizedWord}" -> "${apiResult}"`
      console.log('🌐 [TranslationService]', msg)
      if (debugLogger) {
        debugLogger('success', msg, { word: normalizedWord, translation: apiResult, source: 'api', api: 'MyMemory' })
      }
      // 保存到缓存
      setMemoryCache(normalizedWord, sourceLang, targetLang, apiResult)
      setCachedTranslation(normalizedWord, sourceLang, targetLang, apiResult)
      return apiResult
    } else {
      if (debugLogger) {
        debugLogger('warning', `外部API未返回翻译结果: "${normalizedWord}"`, { sourceLang, targetLang, api: 'MyMemory' })
      }
    }
  } catch (error) {
    const msg = `外部API查询失败: "${normalizedWord}"`
    console.error('❌ [TranslationService]', msg, error)
    if (debugLogger) {
      debugLogger('error', msg, { word: normalizedWord, error: error.message, sourceLang, targetLang, api: 'MyMemory' })
    }
  }

  const msg = `未找到翻译: "${normalizedWord}" (${sourceLang} -> ${targetLang})`
  console.warn('⚠️ [TranslationService]', msg)
  if (debugLogger) {
    debugLogger('warning', msg, { word: normalizedWord, sourceLang, targetLang })
  }
  return null
}

// ==================== 工具函数 ====================

/**
 * 清除所有翻译缓存
 */
export const clearTranslationCache = () => {
  try {
    // 清除localStorage缓存
    const keysToRemove = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(CACHE_PREFIX)) {
        keysToRemove.push(key)
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key))

    // 清除内存缓存
    memoryCache.clear()

    console.log('🧹 [TranslationService] 已清除所有翻译缓存')
  } catch (error) {
    console.error('❌ [TranslationService] 清除缓存失败:', error)
  }
}

/**
 * 获取缓存统计信息
 * @returns {object} 缓存统计信息
 */
export const getCacheStats = () => {
  try {
    let localStorageCount = 0
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(CACHE_PREFIX)) {
        localStorageCount++
      }
    }

    return {
      memoryCacheSize: memoryCache.size,
      localStorageCacheSize: localStorageCount
    }
  } catch (error) {
    console.error('❌ [TranslationService] 获取缓存统计失败:', error)
    return { memoryCacheSize: 0, localStorageCacheSize: 0 }
  }
}


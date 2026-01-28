/**
 * 轻量级翻译服务
 * 提供 hover 词典翻译功能（非 AI），作为 select → ask AI 之前的轻量翻译层
 */

// 🔧 全局debug logger引用（用于内部函数输出日志到debug panel）
let globalDebugLogger = null

/**
 * 设置全局debug logger
 * @param {Function} logger - debug logger函数
 */
export const setGlobalDebugLogger = (logger) => {
  globalDebugLogger = logger
}

/**
 * 内部日志函数（同时输出到console和debug panel）
 */
const internalLog = (level, message, data = null) => {
  // 输出到console
  const consoleMethod = level === 'error' ? console.error : level === 'warning' ? console.warn : console.log
  consoleMethod(`[TranslationService] ${message}`, data || '')
  
  // 输出到debug panel（如果可用）
  if (globalDebugLogger) {
    globalDebugLogger(level, message, data)
  }
}

// ==================== 系统语言获取 ====================

/**
 * 获取并normalize用户系统语言
 * @returns {string} 语言代码 'en' | 'zh' | 'de' | 'ja'，暂时只支持 'en' | 'zh'，其他 fallback 到 'en'
 */
export const getSystemLanguage = () => {
  if (typeof navigator === 'undefined') {
    console.log('🔍 [getSystemLanguage] 服务端渲染环境，返回默认值: en')
    return 'en' // 服务端渲染时默认返回英文
  }

  const systemLang = navigator.language || navigator.userLanguage || 'en'
  const langCode = systemLang.toLowerCase().split('-')[0] // 提取主语言代码，如 'zh-CN' -> 'zh'

  console.log('🔍 [getSystemLanguage] 原始语言信息:', {
    navigatorLanguage: navigator.language,
    navigatorUserLanguage: navigator.userLanguage,
    systemLang,
    langCode
  })

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
  const result = supportedLanguages.includes(normalized) ? normalized : 'en'
  
  console.log('🔍 [getSystemLanguage] 语言检测结果:', {
    langCode,
    normalized,
    result,
    isEnglish: result === 'en'
  })
  
  return result
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

// ==================== 词典API查询 ====================

/**
 * 使用Free Dictionary API查询英语单词定义（免费，无需API密钥）
 * @param {string} word - 单词
 * @returns {Promise<string|null>} 词典定义，如果查询失败返回null
 */
const queryEnglishDictionaryAPI = async (word) => {
  try {
    const apiUrl = `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(word.toLowerCase().trim())}`
    
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)
    
    try {
      const response = await fetch(apiUrl, { signal: controller.signal })
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        if (response.status === 404) {
          return null
        }
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      if (Array.isArray(data) && data.length > 0) {
        const entry = data[0]
        if (entry.meanings && entry.meanings.length > 0) {
          const firstMeaning = entry.meanings[0]
          if (firstMeaning.definitions && firstMeaning.definitions.length > 0) {
            return firstMeaning.definitions[0].definition
          }
        }
      }

      return null
    } catch (fetchError) {
      clearTimeout(timeoutId)
      if (fetchError.name === 'AbortError') {
        throw new Error('请求超时')
      }
      throw fetchError
    }
  } catch (error) {
    console.error('❌ [TranslationService] English Dictionary API查询失败:', error.message)
    return null
  }
}

/**
 * 使用Wiktionary API查询德语单词定义（免费，无需API密钥）
 * 注意：Wiktionary API 支持多种语言，包括德语
 * @param {string} word - 单词
 * @param {string} targetLang - 目标语言代码（用于提取翻译）
 * @returns {Promise<string|null>} 词典定义或翻译，如果查询失败返回null
 */
const queryGermanDictionaryAPI = async (word, targetLang = 'en') => {
  try {
    // Wiktionary API endpoint（支持德语）
    // 使用MediaWiki API查询德语Wiktionary
    // 🔧 清理单词：去除标点符号和空格
    let cleanedWord = word.trim()
    // 去除常见的标点符号（逗号、句号、分号等）
    cleanedWord = cleanedWord.replace(/[,.;:!?'"()[\]{}]/g, '')
    // 去除首尾空格
    cleanedWord = cleanedWord.trim()
    
    if (!cleanedWord || cleanedWord.length === 0) {
      internalLog('warning', `清理后的单词为空: "${word}"`, { originalWord: word })
      return null
    }
    
    // 注意：德语单词首字母通常大写，需要保持原样
    // 尝试多种形式：原词、首字母大写、全小写
    const wordVariants = [
      cleanedWord, // 原词（保持原样）
      cleanedWord.charAt(0).toUpperCase() + cleanedWord.slice(1).toLowerCase(), // 首字母大写
      cleanedWord.toLowerCase() // 全小写
    ]
    
    // 去重
    const uniqueVariants = [...new Set(wordVariants)]
    
    internalLog('info', `查询德语词典: "${word}" -> "${cleanedWord}"`, { originalWord: word, cleanedWord, variants: uniqueVariants })
    
    // 尝试每个变体
    for (const variant of uniqueVariants) {
      // 🔧 使用两种方式查询：先尝试extracts，如果失败再尝试revisions
      // 方式1：使用extracts（更简洁，但可能不总是返回内容）
      const apiUrlExtracts = `https://de.wiktionary.org/w/api.php?action=query&format=json&prop=extracts&exintro&explaintext&titles=${encodeURIComponent(variant)}&origin=*`
      
      internalLog('info', `尝试变体: "${variant}" (extracts方式)`, { variant, url: apiUrlExtracts })
    
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      try {
        internalLog('info', `发送Wiktionary API请求`, { variant, url: apiUrlExtracts })
        const response = await fetch(apiUrlExtracts, { 
          signal: controller.signal,
          mode: 'cors', // 明确指定CORS模式
          credentials: 'omit' // 不发送credentials
        })
        clearTimeout(timeoutId)
        
        internalLog('info', `Wiktionary API响应状态`, { variant, status: response.status, statusText: response.statusText, ok: response.ok })
        
        if (!response.ok) {
          const errorText = await response.text().catch(() => '无法读取错误响应')
          internalLog('warning', `Wiktionary API响应错误: ${response.status}，尝试下一个变体`, { 
            variant, 
            status: response.status, 
            statusText: response.statusText,
            errorText: errorText.substring(0, 200)
          })
          continue
        }

      const data = await response.json()
      internalLog('info', `Wiktionary API响应`, { variant, hasData: !!data.query, responseKeys: data.query ? Object.keys(data.query) : [] })
      
      // Wiktionary API 返回格式
      if (data.query && data.query.pages) {
        const pageIds = Object.keys(data.query.pages)
        internalLog('info', `Wiktionary页面IDs`, { variant, pageIds, count: pageIds.length })
        
        if (pageIds.length > 0) {
          const pageId = pageIds[0]
          const page = data.query.pages[pageId]
          
          internalLog('info', `Wiktionary页面信息`, { 
            variant, 
            pageId, 
            hasExtract: !!page.extract, 
            extractLength: page.extract?.length,
            pageKeys: Object.keys(page),
            pageTitle: page.title,
            pageMissing: page.missing,
            pageInvalid: page.invalid,
            fullPageData: JSON.stringify(page).substring(0, 1000)
          })
          
          // 检查是否找到页面（pageId为-1表示未找到，或者page.missing存在）
          if (pageId === '-1' || page.missing !== undefined) {
            internalLog('warning', `Wiktionary未找到页面 (pageId=${pageId}, missing=${page.missing})，尝试下一个变体`, { variant, pageId, pageMissing: page.missing })
            continue
          }
          
          // 检查是否有extract
          if (!page.extract) {
            internalLog('info', `Wiktionary页面存在但没有extract，尝试使用revisions方式获取内容`, { variant, pageId, pageKeys: Object.keys(page), pageTitle: page.title })
            
            // 🔧 如果页面存在但没有extract，尝试使用revisions方式获取内容
            try {
              // 🔧 使用正确的revisions API参数
              const revisionsUrl = `https://de.wiktionary.org/w/api.php?action=query&format=json&prop=revisions&rvprop=content&rvslots=*&titles=${encodeURIComponent(variant)}&origin=*`
              internalLog('info', `尝试使用revisions方式获取内容`, { variant, url: revisionsUrl })
              
              const revController = new AbortController()
              const revTimeoutId = setTimeout(() => revController.abort(), 5000)
              
              const revResponse = await fetch(revisionsUrl, { 
                signal: revController.signal,
                mode: 'cors',
                credentials: 'omit'
              })
              clearTimeout(revTimeoutId)
              
              internalLog('info', `Revisions API响应状态`, { variant, status: revResponse.status, ok: revResponse.ok })
              
              if (revResponse.ok) {
                const revData = await revResponse.json()
                internalLog('info', `Revisions API响应`, { variant, hasData: !!revData.query, responseKeys: revData.query ? Object.keys(revData.query) : [] })
                
                if (revData.query && revData.query.pages) {
                  const revPageIds = Object.keys(revData.query.pages)
                  internalLog('info', `Revisions页面IDs`, { variant, pageIds: revPageIds })
                  
                  if (revPageIds.length > 0) {
                    const revPageId = revPageIds[0]
                    const revPage = revData.query.pages[revPageId]
                    
                    internalLog('info', `Revisions页面信息`, { 
                      variant, 
                      pageId: revPageId,
                      hasRevisions: !!revPage.revisions,
                      revisionsCount: revPage.revisions?.length || 0,
                      pageKeys: Object.keys(revPage),
                      fullPageData: JSON.stringify(revPage).substring(0, 1000)
                    })
                    
                    if (revPage.revisions && revPage.revisions.length > 0) {
                      const revision = revPage.revisions[0]
                      // 🔧 尝试不同的方式获取内容
                      const content = revision.slots?.main?.content || 
                                     revision['*'] || 
                                     revision.content || 
                                     ''
                      
                      internalLog('info', `获取到revisions内容`, { 
                        variant, 
                        contentLength: content.length, 
                        contentPreview: content.substring(0, 200),
                        hasSlots: !!revision.slots,
                        slotKeys: revision.slots ? Object.keys(revision.slots) : [],
                        revisionKeys: Object.keys(revision)
                      })
                      
                      // 从wikitext中提取简短定义（简单提取第一段）
                      if (content && content.length > 50) {
                        // 提取第一段文本（去除wikitext标记）
                        let text = content.split('\n').find(line => {
                          const trimmed = line.trim()
                          return trimmed.length > 20 && 
                                 !trimmed.startsWith('{{') && 
                                 !trimmed.startsWith('|') &&
                                 !trimmed.startsWith('=') &&
                                 !trimmed.startsWith('*') &&
                                 !trimmed.startsWith('#') &&
                                 !trimmed.startsWith('<!--')
                        }) || content.split('\n').find(line => line.trim().length > 10) || content.split('\n')[0]
                        
                        // 简单清理wikitext标记
                        text = text.replace(/\[\[([^\]]+)\]\]/g, '$1') // 链接
                        text = text.replace(/\{\{([^}]+)\}\}/g, '') // 模板
                        text = text.replace(/'''([^']+)'''/g, '$1') // 粗体
                        text = text.replace(/''([^']+)''/g, '$1') // 斜体
                        text = text.replace(/[=]{2,}/g, '') // 标题标记
                        text = text.replace(/<ref[^>]*>.*?<\/ref>/g, '') // 引用
                        text = text.replace(/<[^>]+>/g, '') // HTML标签
                        text = text.replace(/<!--.*?-->/g, '') // 注释
                        text = text.trim()
                        
                        if (text.length > 20) {
                          let extract = text
                          if (extract.length > 200) {
                            extract = extract.substring(0, 200) + '...'
                          }
                          
                          internalLog('success', `Wiktionary查询成功 (revisions方式): "${cleanedWord}"`, { 
                            originalWord: word,
                            cleanedWord, 
                            variant, 
                            extract: extract.substring(0, 100) + '...',
                            fullExtractLength: text.length
                          })
                          return extract
                        } else {
                          internalLog('warning', `提取的文本太短`, { variant, textLength: text.length, text: text.substring(0, 100) })
                        }
                      } else {
                        internalLog('warning', `revisions内容为空或太短`, { variant, contentLength: content.length })
                      }
                    } else {
                      internalLog('warning', `页面没有revisions`, { variant, pageId: revPageId })
                    }
                  }
                }
              } else {
                const errorText = await revResponse.text().catch(() => '无法读取错误响应')
                internalLog('warning', `Revisions API响应错误`, { variant, status: revResponse.status, errorText: errorText.substring(0, 200) })
              }
            } catch (revError) {
              internalLog('warning', `revisions方式查询失败，尝试下一个变体`, { 
                variant, 
                error: revError.message,
                errorName: revError.name,
                errorStack: revError.stack
              })
            }
            
            // 如果revisions方式也失败，尝试下一个变体
            continue
          }
          
          // 检查extract是否为空或太短
          const extractText = page.extract.trim()
          if (extractText.length < 10) {
            internalLog('warning', `Wiktionary extract太短，尝试下一个变体`, { variant, pageId, extractLength: extractText.length, extract: extractText })
            continue
          }
          
          // 提取前200个字符作为简短定义
          let extract = extractText
          if (extract.length > 200) {
            extract = extract.substring(0, 200) + '...'
          }
          
          internalLog('success', `Wiktionary查询成功: "${cleanedWord}"`, { 
            originalWord: word,
            cleanedWord, 
            variant, 
            extract: extract.substring(0, 100) + '...',
            fullExtractLength: extractText.length
          })
          return extract
        }
      }

      internalLog('warning', `Wiktionary API返回格式异常，尝试下一个变体`, { variant })
      continue
    } catch (fetchError) {
      clearTimeout(timeoutId)
      if (fetchError.name === 'AbortError') {
        internalLog('warning', `Wiktionary API请求超时，尝试下一个变体`, { variant })
        continue
      }
      internalLog('error', `Wiktionary API请求失败，尝试下一个变体`, { 
        variant, 
        error: fetchError.message, 
        errorName: fetchError.name,
        errorStack: fetchError.stack,
        errorType: typeof fetchError
      })
      continue
    }
    }
    
    // 所有变体都失败了
    internalLog('warning', `所有变体都查询失败: "${cleanedWord}"`, { originalWord: word, cleanedWord })
    return null
  } catch (error) {
    internalLog('error', `German Dictionary API查询失败: "${word}"`, { word, error: error.message, errorStack: error.stack })
    return null
  }
}

/**
 * 使用词典API查询单词定义（支持多种语言）
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码（用于判断是否需要翻译定义）
 * @returns {Promise<string|null>} 词典定义（翻译），如果查询失败返回null
 */
const queryDictionaryAPI = async (word, sourceLang, targetLang = 'en') => {
  try {
    internalLog('info', `queryDictionaryAPI 被调用`, { word, sourceLang, targetLang })
    // 根据源语言选择不同的词典API
    if (sourceLang === 'en') {
      // 英语：使用 Free Dictionary API
      internalLog('info', `使用英语词典API: "${word}"`, { word, sourceLang })
      return await queryEnglishDictionaryAPI(word)
    } else if (sourceLang === 'de') {
      // 德语：使用 Wiktionary API（德语版）
      internalLog('info', `使用德语词典API: "${word}"`, { word, sourceLang, targetLang })
      const result = await queryGermanDictionaryAPI(word, targetLang)
      internalLog(result ? 'success' : 'warning', `德语词典API返回`, { word, hasResult: !!result, result: result?.substring(0, 50) })
      return result
    } else {
      // 其他语言：目前不支持，返回null让翻译API处理
      // 未来可以添加更多语言的词典API支持
      internalLog('warning', `不支持该语言的词典API`, { sourceLang })
      return null
    }
  } catch (error) {
    internalLog('error', `Dictionary API查询失败`, { word, sourceLang, error: error.message })
    return null
  }
}

// ==================== 外部API查询 ====================

/**
 * 语言代码映射表（将通用代码映射到各API支持的语言代码）
 */
const LANGUAGE_CODE_MAP = {
  // MyMemory 和 LibreTranslate 都支持的语言代码
  'de': 'de',  // 德语
  'en': 'en',  // 英语
  'zh': 'zh',  // 中文
  'ja': 'ja',  // 日语
  'fr': 'fr',  // 法语
  'es': 'es',  // 西班牙语
  'it': 'it',  // 意大利语
  'pt': 'pt',  // 葡萄牙语
  'ru': 'ru',  // 俄语
  'ar': 'ar',  // 阿拉伯语
}

/**
 * 标准化语言代码
 */
const normalizeLangCode = (langCode) => {
  return LANGUAGE_CODE_MAP[langCode] || langCode
}

/**
 * 使用MyMemory API查询翻译
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @returns {Promise<string|null>} 翻译结果
 */
const queryMyMemoryAPI = async (word, sourceLang, targetLang) => {
  try {
    const normalizedSource = normalizeLangCode(sourceLang)
    const normalizedTarget = normalizeLangCode(targetLang)
    
    // MyMemory API 对文本长度有限制（通常约500字符）
    const MAX_LENGTH = 500
    let textToTranslate = word
    
    if (textToTranslate.length > MAX_LENGTH) {
      const truncated = textToTranslate.substring(0, MAX_LENGTH)
      const lastSentenceEnd = Math.max(
        truncated.lastIndexOf('.'),
        truncated.lastIndexOf('?'),
        truncated.lastIndexOf('!')
      )
      
      if (lastSentenceEnd > MAX_LENGTH * 0.7) {
        textToTranslate = truncated.substring(0, lastSentenceEnd + 1)
      } else {
        const lastSpace = truncated.lastIndexOf(' ')
        if (lastSpace > MAX_LENGTH * 0.7) {
          textToTranslate = truncated.substring(0, lastSpace) + '...'
        } else {
          textToTranslate = truncated + '...'
        }
      }
    }
    
    const apiUrl = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(textToTranslate)}&langpair=${normalizedSource}|${normalizedTarget}`
    
    // 添加超时控制（5秒）
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)
    
    try {
      const response = await fetch(apiUrl, { signal: controller.signal })
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      if (data.responseStatus === 200 && data.responseData && data.responseData.translatedText) {
        let translation = data.responseData.translatedText.trim()
        
        // 如果翻译结果和原文相同，可能不是有效翻译
        if (translation.toLowerCase() === word.toLowerCase()) {
          return null
        }
        
        if (word.length > MAX_LENGTH) {
          translation += ' (翻译已截断)'
        }
        
        return translation
      }

      return null
    } catch (fetchError) {
      clearTimeout(timeoutId)
      if (fetchError.name === 'AbortError') {
        throw new Error('请求超时')
      }
      throw fetchError
    }
  } catch (error) {
    console.error('❌ [TranslationService] MyMemory API查询失败:', error.message)
    return null
  }
}

/**
 * 使用LibreTranslate API查询翻译（免费开源，无需API密钥）
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @returns {Promise<string|null>} 翻译结果
 */
const queryLibreTranslateAPI = async (word, sourceLang, targetLang) => {
  try {
    // LibreTranslate 支持的语言代码映射
    const libreLangMap = {
      'de': 'de',
      'en': 'en',
      'zh': 'zh',
      'ja': 'ja',
      'fr': 'fr',
      'es': 'es',
      'it': 'it',
      'pt': 'pt',
      'ru': 'ru',
      'ar': 'ar',
    }
    
    const normalizedSource = libreLangMap[sourceLang] || sourceLang
    const normalizedTarget = libreLangMap[targetLang] || targetLang
    
    // 检查语言是否支持
    if (!libreLangMap[sourceLang] || !libreLangMap[targetLang]) {
      return null
    }
    
    // 使用公共 LibreTranslate 服务器
    // 注意：可以使用多个公共服务器作为备选
    const servers = [
      'https://libretranslate.de',
      'https://translate.argosopentech.com',
      'https://libretranslate.com'
    ]
    
    // 尝试每个服务器，直到成功
    for (const server of servers) {
      try {
        const apiUrl = `${server}/translate`
        
        // 添加超时控制（5秒）
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000)
        
        try {
          const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              q: word,
              source: normalizedSource,
              target: normalizedTarget,
              format: 'text'
            }),
            signal: controller.signal
          })
          
          clearTimeout(timeoutId)
          
          if (!response.ok) {
            // 如果这个服务器失败，尝试下一个
            continue
          }

          const data = await response.json()
          
          if (data && data.translatedText) {
            const translation = data.translatedText.trim()
            
            // 如果翻译结果和原文相同，可能不是有效翻译
            if (translation.toLowerCase() === word.toLowerCase()) {
              continue
            }
            
            return translation
          }
        } catch (fetchError) {
          clearTimeout(timeoutId)
          if (fetchError.name === 'AbortError') {
            // 超时，尝试下一个服务器
            continue
          }
          // 其他错误，尝试下一个服务器
          continue
        }
      } catch (error) {
        // 服务器错误，尝试下一个
        continue
      }
    }
    
    return null
  } catch (error) {
    console.error('❌ [TranslationService] LibreTranslate API查询失败:', error.message)
    return null
  }
}

/**
 * 使用多个API进行查询，自动切换和重试
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @param {Array<Function>} apiProviders - API提供者数组
 * @returns {Promise<string|null>} 翻译结果
 */
const queryWithMultipleAPIs = async (word, sourceLang, targetLang, apiProviders) => {
  if (!apiProviders || apiProviders.length === 0) {
    return null
  }
  
  // 依次尝试每个API
  for (let i = 0; i < apiProviders.length; i++) {
    const apiProvider = apiProviders[i]
    // 获取API名称（从 displayName 或 name 属性）
    const apiName = apiProvider.displayName || apiProvider.name || `API${i + 1}`
    
    try {
      console.log(`🔍 [TranslationService] 尝试 ${apiName}...`)
      const result = await apiProvider(word, sourceLang, targetLang)
      
      if (result) {
        console.log(`✅ [TranslationService] ${apiName} 查询成功: "${word}" -> "${result}"`)
        return result
      } else {
        console.log(`⚠️ [TranslationService] ${apiName} 未返回结果，尝试下一个API`)
      }
    } catch (error) {
      console.warn(`⚠️ [TranslationService] ${apiName} 查询失败:`, error.message)
      // 继续尝试下一个API
    }
  }
  
  return null
}

/**
 * 默认API提供者列表（按优先级排序）
 * 当第一个API失败时，自动切换到下一个
 */
export const defaultTranslationAPIs = [
  queryMyMemoryAPI,
  queryLibreTranslateAPI
]

// 为API函数添加显示名称（用于日志）
queryMyMemoryAPI.displayName = 'MyMemory'
queryLibreTranslateAPI.displayName = 'LibreTranslate'

/**
 * 默认API实现（使用多个API的自动切换）
 * @param {string} word - 单词
 * @param {string} sourceLang - 源语言代码
 * @param {string} targetLang - 目标语言代码
 * @returns {Promise<string|null>} 翻译结果
 */
export const defaultTranslationAPI = async (word, sourceLang, targetLang) => {
  return await queryWithMultipleAPIs(word, sourceLang, targetLang, defaultTranslationAPIs)
}

// ==================== 主查询函数 ====================

/**
 * 获取快速翻译（主函数）
 * 
 * 对于单词（isWord=true）：
 *   查询顺序：本地vocabulary表 → 内存缓存 → localStorage缓存 → 词典API → 翻译API
 * 
 * 对于句子（isWord=false）：
 *   查询顺序：内存缓存 → localStorage缓存 → 翻译API（跳过词典查询）
 * 
 * @param {string} word - 要翻译的单词或句子
 * @param {string} sourceLang - 源语言代码（如 'de', 'en', 'zh'）
 * @param {string} targetLang - 目标语言代码（如 'en', 'zh'），默认使用系统语言
 * @param {object} options - 可选配置
 * @param {Function} options.vocabListGetter - 获取本地vocabulary列表的函数（可选）
 * @param {Function} options.apiProvider - 自定义API提供者（可选，默认使用MyMemory）
 * @param {boolean} options.isWord - 是否为单词查询（true=单词，false=句子），默认根据长度和空格判断
 * @param {boolean} options.useDictionary - 是否使用词典API（仅对单词有效），默认true
 * @param {boolean} options.returnWithSource - 是否返回包含来源信息的对象，默认false（返回字符串）
 * @returns {Promise<string|null>|Promise<{text: string, source: string}|null>} 翻译结果，如果returnWithSource=true则返回对象，否则返回字符串
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
  const { vocabListGetter = null, debugLogger = null, useDictionary = true, returnWithSource = false } = options
  
  // 🔧 判断是否为单词：如果未指定isWord，则根据长度和空格判断
  // 单词通常：长度较短（<50字符）且不包含空格，或明确指定isWord=true
  let isWord = options.isWord
  if (isWord === undefined) {
    // 自动判断：如果长度较短且不包含空格，认为是单词
    isWord = normalizedWord.length < 50 && !normalizedWord.includes(' ')
  }
  
  // 🔧 改进：支持单个API函数或API数组
  // 如果为 null 或 undefined 则使用默认API列表
  let apiProvider = options.apiProvider
  if (!apiProvider) {
    apiProvider = defaultTranslationAPIs
  } else if (typeof apiProvider === 'function') {
    // 单个API函数，转换为数组
    apiProvider = [apiProvider]
  } else if (!Array.isArray(apiProvider)) {
    // 无效类型，使用默认
    apiProvider = defaultTranslationAPIs
  }

  // 记录开始查询
  if (debugLogger) {
    debugLogger('info', `开始查询${isWord ? '单词' : '句子'}翻译: "${normalizedWord.substring(0, 50)}${normalizedWord.length > 50 ? '...' : ''}"`, { sourceLang, targetLang, isWord })
  }

  // 🔧 对于单词查询，如果useDictionary=true，优先查询词典，不先查缓存
  // 这样可以确保词典结果优先于之前的翻译结果
  // 对于句子查询或useDictionary=false，先查缓存
  
  // 1. 查询内存缓存（仅当不是单词查询或useDictionary=false时）
  if (!isWord || !useDictionary) {
    const memoryCacheResult = getMemoryCache(normalizedWord, sourceLang, targetLang)
    if (memoryCacheResult) {
      const msg = `从内存缓存获取翻译: "${normalizedWord}" -> "${memoryCacheResult}"`
      console.log('💾 [TranslationService]', msg)
      if (debugLogger) {
        debugLogger('success', msg, { word: normalizedWord, translation: memoryCacheResult, source: 'memory' })
      }
      return memoryCacheResult
    }

    // 2. 查询localStorage缓存（仅当不是单词查询或useDictionary=false时）
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
  }

  // 2. 查询本地vocabulary表（仅对单词有效）
  if (isWord && vocabListGetter) {
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
      // 🔧 返回结果时包含来源信息（本地vocab视为翻译）
      if (returnWithSource) {
        return { text: localVocabResult, source: 'translation' }
      }
      return localVocabResult
    }
  }

  // 3. 查询词典API（仅对单词有效，且useDictionary=true）
  // 🔧 优先查询词典，确保词典结果优先于翻译结果
  // 支持的语言：
  //   - 英语：使用 Free Dictionary API
  //   - 德语：使用 Wiktionary API（德语版）
  //   - 其他语言：返回null，自动回退到翻译API
  if (isWord && useDictionary) {
    internalLog('info', `开始查询词典API: "${normalizedWord}"`, { word: normalizedWord, sourceLang, targetLang, isWord, useDictionary })
    if (debugLogger) {
      debugLogger('info', `查询词典API: "${normalizedWord}"`, { sourceLang, targetLang })
    }
    try {
      const dictResult = await queryDictionaryAPI(normalizedWord, sourceLang, targetLang)
      internalLog(dictResult ? 'success' : 'warning', `词典API查询结果`, { word: normalizedWord, hasResult: !!dictResult, result: dictResult?.substring(0, 50) })
      if (dictResult) {
        // 词典返回的是源语言的定义（英语或德语）
        // 如果目标语言不是源语言，用户会看到源语言定义（更详细）
        // 如果需要目标语言翻译，可以继续使用翻译API
        
        const msg = `从词典API获取定义: "${normalizedWord}" -> "${dictResult.substring(0, 50)}${dictResult.length > 50 ? '...' : ''}"`
        internalLog('success', msg, { word: normalizedWord, translation: dictResult, source: 'dictionary', sourceLang })
        if (debugLogger) {
          debugLogger('success', msg, { word: normalizedWord, translation: dictResult, source: 'dictionary', sourceLang })
        }
      // 保存到缓存
      setMemoryCache(normalizedWord, sourceLang, targetLang, dictResult)
      setCachedTranslation(normalizedWord, sourceLang, targetLang, dictResult)
      // 🔧 返回结果时包含来源信息
      if (returnWithSource) {
        return { text: dictResult, source: 'dictionary' }
      }
      return dictResult
      } else {
        internalLog('warning', `词典API未找到结果，继续使用翻译API: "${normalizedWord}"`, { word: normalizedWord, sourceLang, targetLang })
        if (debugLogger) {
          debugLogger('info', `词典API未找到结果或语言不支持，继续使用翻译API: "${normalizedWord}"`, { sourceLang, targetLang })
        }
      }
    } catch (error) {
      internalLog('error', `词典API查询失败: "${normalizedWord}"`, { word: normalizedWord, error: error.message, stack: error.stack })
      if (debugLogger) {
        debugLogger('warning', `词典API查询失败，继续使用翻译API: "${normalizedWord}"`, { error: error.message })
      }
      // 词典查询失败，继续使用翻译API
    }
  }

  // 4. 如果之前跳过了缓存查询（因为是单词查询且useDictionary=true），现在查询缓存
  // 🔧 重要：对于单词查询且useDictionary=true，如果词典查询失败，不要使用缓存中的旧结果
  // 因为缓存中的结果可能是之前的翻译，我们想要优先显示词典结果
  // 所以这里完全跳过缓存，直接继续查询翻译API
  // 这样可以确保词典结果优先，翻译结果作为备选
  // 注意：如果词典查询成功，已经在步骤3返回了，不会执行到这里
  // 所以这里只处理词典查询失败的情况，跳过缓存，继续查询翻译API

  // 5. 查询外部翻译API（支持多个API自动切换）
  if (debugLogger) {
    debugLogger('info', `查询外部翻译API: "${normalizedWord.substring(0, 50)}${normalizedWord.length > 50 ? '...' : ''}"`, { sourceLang, targetLang, apiCount: apiProvider.length, isWord })
  }
  
  try {
    const apiResult = await queryWithMultipleAPIs(normalizedWord, sourceLang, targetLang, apiProvider)
    if (apiResult) {
      const msg = `从外部API获取翻译: "${normalizedWord}" -> "${apiResult}"`
      console.log('🌐 [TranslationService]', msg)
      if (debugLogger) {
        debugLogger('success', msg, { word: normalizedWord, translation: apiResult, source: 'api', apiCount: apiProvider.length })
      }
      // 保存到缓存
      setMemoryCache(normalizedWord, sourceLang, targetLang, apiResult)
      setCachedTranslation(normalizedWord, sourceLang, targetLang, apiResult)
      // 🔧 返回结果时包含来源信息
      if (returnWithSource) {
        return { text: apiResult, source: 'translation' }
      }
      return apiResult
    } else {
      if (debugLogger) {
        debugLogger('warning', `所有外部API均未返回翻译结果: "${normalizedWord}"`, { sourceLang, targetLang, apiCount: apiProvider.length })
      }
    }
  } catch (error) {
    const msg = `外部API查询失败: "${normalizedWord}"`
    console.error('❌ [TranslationService]', msg, error)
    if (debugLogger) {
      debugLogger('error', msg, { word: normalizedWord, error: error.message, sourceLang, targetLang, apiCount: apiProvider.length })
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


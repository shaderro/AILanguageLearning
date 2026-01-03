import { useState, useRef, useMemo, useContext, useCallback, useEffect } from 'react'
import { getTokenKey, getTokenId } from '../utils/tokenUtils'
// import VocabExplanationButton from './VocabExplanationButton' // 暂时注释掉 - 以后可能会用到
import VocabTooltip from './VocabTooltip'
import VocabNotationCard from './notation/VocabNotationCard'
import GrammarNotation from './GrammarNotation'
import { NotationContext } from '../contexts/NotationContext'
import { useTokenSelectable } from '../selection/hooks/useTokenSelectable'
import QuickTranslationTooltip from '../../../components/QuickTranslationTooltip'
import { getQuickTranslation, getSystemLanguage } from '../../../services/translationService'
import { useLanguage, languageNameToCode, languageCodeToBCP47 } from '../../../contexts/LanguageContext'
import { useTranslationDebug } from '../../../contexts/TranslationDebugContext'

/**
 * TokenSpan - Renders individual token with selection and vocab explanation features
 */
export default function TokenSpan({
  token,
  tokenIdx,
  sentenceIdx,
  articleId,
  selectedTokenIds,
  activeSentenceIndex,
  hasExplanation,
  getExplanation,
  hoveredTokenId,
  setHoveredTokenId,
  handleGetExplanation,
  addSingle,
  isTokenAsked,
  markAsAsked,
  getNotationContent,
  setNotationContent,
  // 🔧 新增：分词下划线相关 props
  showSegmentationUnderline = false,
  wordTokenInfo = null,
  // 🔧 新增：朗读高亮相关 props
  isCurrentlyReading = false,
  // 🔧 新增：token hover 离开回调（用于整句翻译）
  onTokenMouseLeave = null,
  // 🔧 新增：AI详细解释回调
  onAskAI = null,
  // 🔧 新增：高亮范围
  highlightedRange = null
}) {
  // 从 NotationContext 获取 notation 相关功能
  const notationContext = useContext(NotationContext)
  const {
    getGrammarNotationsForSentence,
    getVocabNotationsForSentence,
    getVocabExampleForToken,
    isTokenAsked: isTokenAskedFromContext
  } = notationContext || {}
  
  const displayText = typeof token === 'string' ? token : (token?.token_body ?? token?.token ?? '')
  const anchorRef = useRef(null)
  const selectable = typeof token === 'object' ? !!token?.selectable : false
  const uid = getTokenId(token, sentenceIdx)
  const selected = uid ? selectedTokenIds.has(uid) : false
  const hasSelection = selectedTokenIds && selectedTokenIds.size > 0
  const hoverAllowed = selectable && (!hasSelection ? (activeSentenceIndex == null || activeSentenceIndex === sentenceIdx) : activeSentenceIndex === sentenceIdx)
  const cursorClass = hoverAllowed ? 'cursor-pointer' : 'cursor-default'
  const isTextToken = typeof token === 'object' && token?.token_type === 'text'

  // 🔧 新增：hover翻译相关状态和逻辑
  const { selectedLanguage } = useLanguage() // 获取全局语言状态（目标语言）
  // 清除调试日志
  const [quickTranslation, setQuickTranslation] = useState(null)
  const [translationSource, setTranslationSource] = useState(null) // 'dictionary' | 'translation'
  const [showQuickTranslation, setShowQuickTranslation] = useState(false)
  const [isLoadingTranslation, setIsLoadingTranslation] = useState(false)
  const hoverTranslationTimerRef = useRef(null)
  const translationQueryRef = useRef(null) // 用于取消正在进行的查询

  // 获取源语言（从文章数据推断，或使用默认值）
  // 注意：这里简化处理，实际可以从ArticleViewer传递articleLanguage
  const sourceLang = useMemo(() => {
    // 可以从token或sentence中获取语言信息，这里暂时使用默认值'de'
    // 后续可以通过props传递articleLanguage
    return 'de' // 默认德语，可以根据实际情况调整
  }, [])

  // 获取目标语言（系统语言或全局选择的语言）
  // 🔧 如果目标语言和源语言相同，使用系统语言或fallback到英文/中文
  const targetLang = useMemo(() => {
    const globalLang = languageNameToCode(selectedLanguage)
    const preferredLang = globalLang || getSystemLanguage()
    
    // 🔧 如果目标语言和源语言相同，需要选择不同的语言
    if (preferredLang === sourceLang) {
      const systemLang = getSystemLanguage()
      // 如果系统语言也不同，使用系统语言；否则fallback到英文或中文
      if (systemLang !== sourceLang) {
        return systemLang
      } else {
        // 如果系统语言也和源语言相同，fallback到英文（如果源语言不是英文）或中文
        const fallbackLang = sourceLang === 'en' ? 'zh' : 'en'
        return fallbackLang
      }
    }
    
    const logData = {
      sourceLang,
      selectedLanguage,
      globalLang,
      preferredLang,
      finalTargetLang: preferredLang
    }
    return preferredLang
  }, [selectedLanguage, sourceLang])

  // 🔧 hover翻译查询函数
  const queryQuickTranslation = useCallback(async (word) => {
    if (!word || word.trim().length === 0) {
      return
    }

    // 取消之前的查询
    if (translationQueryRef.current) {
      translationQueryRef.current = null
    }

    const currentQuery = {}
    translationQueryRef.current = currentQuery

    // 🔧 关闭翻译调试日志
    // const debugLogger = (level, message, data) => {
    //   addDebugLog(level, `[TokenSpan] ${message}`, data)
    // }
    
    // 🔧 设置全局debug logger为空函数，关闭翻译服务内部日志
    const { setGlobalDebugLogger } = await import('../../../services/translationService')
    setGlobalDebugLogger(() => {}) // 空函数，不输出日志

    try {
      // 🔧 关闭翻译调试日志
      // const logData = { word, sourceLang, targetLang }
      // console.log('🔍 [TokenSpan] 调用getQuickTranslation:', logData)
      // addDebugLog('info', `开始查询翻译: "${word}"`, logData)
      
      // 设置加载状态
      setIsLoadingTranslation(true)
      setShowQuickTranslation(true)
      
      // 🔧 单词查询：优先使用词典，如果词典没有结果再使用翻译API
      // 🔧 返回包含来源信息的对象
      const translationResult = await getQuickTranslation(word, sourceLang, targetLang, {
        // debugLogger, // 🔧 关闭调试日志
        isWord: true, // 明确指定为单词查询
        useDictionary: true, // 使用词典API
        returnWithSource: true // 返回包含来源信息的对象
      })
      
      // 处理返回结果（可能是字符串或对象）
      let translation = null
      let translationSource = null
      if (translationResult) {
        if (typeof translationResult === 'object' && translationResult.text) {
          translation = translationResult.text
          translationSource = translationResult.source
        } else {
          translation = translationResult
          // 如果没有来源信息，默认为翻译（向后兼容）
          translationSource = 'translation'
        }
      }
      
      // 🔧 关闭翻译调试日志
      // const resultData = { word, translation, source: translationSource }
      // console.log('✅ [TokenSpan] 翻译查询结果:', resultData)
      // addDebugLog(translation ? 'success' : 'warning', `翻译查询完成: "${word}"`, resultData)
      
      // 检查查询是否已被取消
      if (translationQueryRef.current === currentQuery) {
        setQuickTranslation(translation)
        setTranslationSource(translationSource) // 保存来源信息
        setIsLoadingTranslation(false)
        // 即使没有翻译结果，也保持显示状态
        setShowQuickTranslation(true)
        // 🔧 关闭翻译调试日志
        // const stateData = { 
        //   translation, 
        //   showQuickTranslation: true,
        //   isLoading: false
        // }
        // console.log('✅ [TokenSpan] 翻译tooltip状态更新:', stateData)
        // addDebugLog('info', `Tooltip状态更新: ${translation ? '显示翻译' : '显示空状态'}`, stateData)
        translationQueryRef.current = null
      } else {
        // 🔧 关闭翻译调试日志
        // console.log('⚠️ [TokenSpan] 翻译查询已被取消，忽略结果')
        // addDebugLog('warning', '翻译查询已被取消，忽略结果', { word })
        setIsLoadingTranslation(false)
      }
    } catch (error) {
      // 🔧 关闭翻译调试日志
      // const errorData = { word, error: error.message, stack: error.stack }
      // console.error('❌ [TokenSpan] 翻译查询失败:', error)
      // addDebugLog('error', `翻译查询失败: "${word}"`, errorData)
      if (translationQueryRef.current === currentQuery) {
        // 🔧 修复：即使查询失败，也保持 tooltip 显示，显示"无翻译"状态
        setQuickTranslation(null)
        setIsLoadingTranslation(false)
        // 🔧 保持显示状态，让 tooltip 组件显示"无翻译"状态
        setShowQuickTranslation(true)
        translationQueryRef.current = null
        // 🔧 不立即隐藏 tooltip，让用户看到"无翻译"状态
        // tooltip 会在鼠标离开时通过 clearTranslation 隐藏
      }
    }
  }, [sourceLang, targetLang])

  // 🔧 清理函数
  const clearTranslationTimer = useCallback(() => {
    if (hoverTranslationTimerRef.current) {
      clearTimeout(hoverTranslationTimerRef.current)
      hoverTranslationTimerRef.current = null
    }
  }, [])

  // 🔧 清理翻译状态
  const clearTranslation = useCallback(() => {
    clearTranslationTimer()
    setShowQuickTranslation(false)
    setQuickTranslation(null)
    setIsLoadingTranslation(false)
    // 取消正在进行的查询
    translationQueryRef.current = null
  }, [clearTranslationTimer])

  // 🔧 根据语言代码获取对应的语音
  const getVoiceForLanguage = useCallback((langCode) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      return null
    }
    
    const availableVoices = window.speechSynthesis.getVoices()
    
    if (!availableVoices || availableVoices.length === 0) {
      return null
    }
    
    const targetLang = languageCodeToBCP47(langCode)
    
    // 优先查找非多语言的、完全匹配的语音
    let voice = availableVoices.find(v => 
      v.lang === targetLang && 
      !v.name.toLowerCase().includes('multilingual')
    )
    
    // 如果找不到非多语言的，再查找完全匹配的（包括多语言）
    if (!voice) {
      voice = availableVoices.find(v => v.lang === targetLang)
    }
    
    // 如果找不到，查找语言代码前缀匹配的（优先非多语言）
    if (!voice) {
      const langPrefix = targetLang.split('-')[0]
      voice = availableVoices.find(v => 
        v.lang && 
        v.lang.startsWith(langPrefix) && 
        !v.name.toLowerCase().includes('multilingual')
      )
    }
    
    return voice || null
  }, [])
  
  // 🔧 朗读函数
  const handleSpeak = useCallback(async (text) => {
    if (!text) return
    
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      // 先取消任何正在进行的朗读
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel()
        await new Promise(resolve => setTimeout(resolve, 100))
      }
      
      // 使用源语言（因为要朗读的是原文）
      const langCode = sourceLang
      const targetLangBCP47 = languageCodeToBCP47(langCode)
      
      // 确保语音列表已加载
      let availableVoices = window.speechSynthesis.getVoices()
      if (availableVoices.length === 0) {
        await new Promise(resolve => setTimeout(resolve, 100))
        availableVoices = window.speechSynthesis.getVoices()
      }
      
      // 获取语音
      let validVoice = getVoiceForLanguage(langCode)
      if (validVoice) {
        validVoice = availableVoices.find(v => 
          v.name === validVoice.name && v.lang === validVoice.lang
        ) || availableVoices.find(v => v.lang === validVoice.lang)
      }
      
      if (!validVoice) {
        validVoice = getVoiceForLanguage(langCode)
      }
      
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = targetLangBCP47
      
      if (validVoice) {
        utterance.voice = validVoice
      }
      
      utterance.rate = 0.9
      utterance.pitch = 1.0
      utterance.volume = 1.0
      
      utterance.onerror = (event) => {
        if (event.error === 'interrupted') {
          console.log('🔊 [TokenSpan] 朗读被中断（正常情况）')
          return
        }
        console.error('❌ [TokenSpan] 朗读错误:', event.error)
      }
      
      window.speechSynthesis.speak(utterance)
    }
  }, [sourceLang, getVoiceForLanguage])
  
  // 🔧 tooltip hover 进入（保持 tooltip 显示）
  const handleTooltipMouseEnter = useCallback(() => {
    // 取消任何待清除的定时器
    clearTranslationTimer()
  }, [clearTranslationTimer])
  
  // 🔧 tooltip hover 离开（延迟清除翻译状态）
  const handleTooltipMouseLeave = useCallback(() => {
    // 延迟清除，给用户时间移动鼠标
    clearTranslationTimer()
    hoverTranslationTimerRef.current = setTimeout(() => {
      clearTranslation()
    }, 200)
  }, [clearTranslationTimer, clearTranslation])
  
  // 🔧 组件卸载时清理
  useEffect(() => {
    return () => {
      clearTranslationTimer()
      translationQueryRef.current = null
    }
  }, [clearTranslationTimer])
  
  // 检查token是否已被提问
  // sentence_id 从 sentenceIdx 计算得出 (sentenceIdx + 1)
  const tokenSentenceId = sentenceIdx + 1
  const tokenSentenceTokenId = token?.sentence_token_id
  // Selection hook（模块化选择行为）
  const { className: selectionTokenClass, onMouseEnter: selOnEnter, onMouseLeave: selOnLeave, onClick: selOnClick } = useTokenSelectable({
    textId: articleId,
    sentenceId: tokenSentenceId,
    tokenId: tokenSentenceTokenId
  })
  
  // 优先使用 Context 中的 isTokenAsked，如果没有则使用 props 中的（向后兼容）
  const isTokenAskedFunc = isTokenAskedFromContext || isTokenAsked
  const isAsked = isTextToken && tokenSentenceTokenId != null
    ? (isTokenAskedFunc ? isTokenAskedFunc(articleId, tokenSentenceId, tokenSentenceTokenId) : false)
    : false
  
  // 调试日志已关闭以提升性能

  // 检查是否有grammar notation
  const sentenceId = sentenceIdx + 1
  const grammarNotations = getGrammarNotationsForSentence ? getGrammarNotationsForSentence(sentenceId) : []
  const hasGrammar = grammarNotations.length > 0
  
  // 检查当前token是否在grammar notation的marked_token_ids中
  // 如果marked_token_ids为空，则整个句子都有grammar notation
  // 取消 grammar 灰色下划线的渲染，改用句子右下角徽标触发卡片
  const isInGrammarNotation = false

  // 优先检查 vocab notation（从新API加载）
  // vocab notation是数据源，asked tokens只是兼容层
  // 🔧 移除 useMemo，直接调用函数，确保每次渲染都能获取最新数据
  const vocabNotationsForSentence = typeof getVocabNotationsForSentence === 'function'
    ? getVocabNotationsForSentence(sentenceId)
    : []
  
  // 🔧 获取当前 token 的 word_token_id（如果存在）
  const currentTokenWordTokenId = token?.word_token_id ? Number(token.word_token_id) : null
  
  // 使用useMemo缓存匹配结果，避免每次渲染都重新计算
  // 🔧 修复：不仅检查是否有匹配，还要找到最匹配的 notation（用于后续显示正确的 vocab example）
  const { hasVocabNotationForToken, matchedNotation } = useMemo(() => {
    if (!Array.isArray(vocabNotationsForSentence) || tokenSentenceTokenId == null) {
      return { hasVocabNotationForToken: false, matchedNotation: null }
    }
    const currentTokenId = Number(tokenSentenceTokenId)
    
    // 🔧 优先匹配：如果当前 token 有 word_token_id，优先匹配相同 word_token_id 的 notation
    if (currentTokenWordTokenId != null) {
      const exactMatch = vocabNotationsForSentence.find(n => {
        const notationWordTokenId = n?.word_token_id ? Number(n.word_token_id) : null
        return notationWordTokenId === currentTokenWordTokenId
      })
      
      if (exactMatch) {
        return { hasVocabNotationForToken: true, matchedNotation: exactMatch }
      }
    }
    
    // 🔧 次优匹配：检查 word_token_token_ids 是否包含当前 token
    const wordTokenMatch = vocabNotationsForSentence.find(n => {
      if (n?.word_token_token_ids && Array.isArray(n.word_token_token_ids) && n.word_token_token_ids.length > 0) {
        const tokenIdsArray = n.word_token_token_ids.map(id => Number(id))
        return tokenIdsArray.includes(currentTokenId)
      }
      return false
    })
    
    if (wordTokenMatch) {
      return { hasVocabNotationForToken: true, matchedNotation: wordTokenMatch }
    }
    
    // 🔧 回退匹配：使用 token_id 精确匹配（用于空格语言或没有 word_token_token_ids 的情况）
    const tokenIdMatch = vocabNotationsForSentence.find(n => {
      const notationTokenId = Number(n?.token_id ?? n?.token_index)
      return notationTokenId === currentTokenId
    })
    
    if (tokenIdMatch) {
      return { hasVocabNotationForToken: true, matchedNotation: tokenIdMatch }
    }
    
    return { hasVocabNotationForToken: false, matchedNotation: null }
  }, [vocabNotationsForSentence, tokenSentenceTokenId, currentTokenWordTokenId])

  // 优先使用vocab notation，asked tokens作为备用（向后兼容）
  // 如果vocab notation存在，就不需要检查asked tokens了
  const hasVocabVisual = hasVocabNotationForToken || (isAsked && !hasVocabNotationForToken)

  // 🔧 检查是否在高亮范围内
  const isHighlighted = highlightedRange && 
    highlightedRange.sentenceIdx === sentenceIdx &&
    tokenIdx >= highlightedRange.startTokenIdx &&
    tokenIdx <= highlightedRange.endTokenIdx
  
  // 🔧 朗读高亮优先级最高，然后是选中，然后是拖拽高亮（仅在拖拽过程中显示），最后是 hover
  // 注意：拖拽高亮（isHighlighted）只在拖拽过程中显示，不影响选中状态（selected）
  const bgClass = isCurrentlyReading
    ? 'bg-green-200' // success-200 颜色
    : (selected
      ? 'bg-yellow-300' // 选中状态优先级高于拖拽高亮
      : (isHighlighted
        ? 'bg-yellow-200' // 拖拽高亮颜色改为黄色（仅在拖拽过程中）
        : (hoverAllowed ? 'bg-transparent hover:bg-yellow-200' : 'bg-transparent')))
  const tokenHasExplanation = isTextToken && hasExplanation(token)
  const tokenExplanation = isTextToken ? getExplanation(token) : null
  const isHovered = hoveredTokenId === uid
  
  // 管理TokenNotation的显示状态（针对已提问的token）
  const [showNotation, setShowNotation] = useState(false)
  const hideNotationTimerRef = useRef(null)
  
  // 获取该token的notation内容
  const notationContent = isAsked && getNotationContent 
    ? getNotationContent(articleId, tokenSentenceId, tokenSentenceTokenId)
    : null
  
  // 延迟隐藏 notation
  const scheduleHideNotation = () => {
    // 清除之前的延迟隐藏
    if (hideNotationTimerRef.current) {
      clearTimeout(hideNotationTimerRef.current)
    }
    // 设置新的延迟隐藏（200ms后隐藏）
    hideNotationTimerRef.current = setTimeout(() => {
      setShowNotation(false)
    }, 200)
  }
  
  // 取消延迟隐藏（保持显示）
  const cancelHideNotation = () => {
    if (hideNotationTimerRef.current) {
      clearTimeout(hideNotationTimerRef.current)
      hideNotationTimerRef.current = null
    }
  }
  
  // 处理 notation 的 mouse enter（鼠标进入卡片）
  const handleNotationMouseEnter = () => {
    cancelHideNotation()  // 取消隐藏
    setShowNotation(true)  // 确保显示
  }
  
  // 处理 notation 的 mouse leave（鼠标离开卡片）
  const handleNotationMouseLeave = () => {
    scheduleHideNotation()  // 延迟隐藏
  }

  return (
    <span
      key={getTokenKey(sentenceIdx, token, tokenIdx)}
      className="relative inline-block"
      ref={anchorRef}
    >
      <span
        data-token="1"
        data-token-id={uid || undefined} // 🔧 添加 data-token-id 属性，用于拖拽时识别 token
        ref={(el) => {
          // tokenRefsRef 已移除（不再需要拖拽功能）
        }}
        onMouseEnter={(e) => {
          // 只有可选择的token才触发hover效果
          if (selectable) {
            selOnEnter()
          }
          if (isTextToken && tokenHasExplanation) {
            setHoveredTokenId(uid)
          }
          // 如果有vocab notation（来自vocab_notations或asked tokens），显示notation卡片
          if (hasVocabVisual) {
            cancelHideNotation()  // 取消任何待处理的隐藏
            setShowNotation(true)
          }

          // 🔧 新增：hover翻译功能（延迟触发，避免频繁查询）
          // 只在没有vocab notation的情况下显示快速翻译（避免重复显示）
          if (isTextToken && !hasVocabVisual && hoverAllowed && displayText.trim().length > 0) {
            const hoverData = {
              isTextToken,
              hasVocabVisual,
              hoverAllowed,
              word: displayText,
              wordLength: displayText.trim().length,
              sourceLang,
              targetLang
            }
            // 🔧 关闭翻译调试日志
            // console.log('🔍 [TokenSpan] Hover翻译触发条件检查:', hoverData)
            // addDebugLog('info', `Hover触发: "${displayText}"`, hoverData)
            clearTranslationTimer()
            // 延迟250ms触发翻译查询（避免鼠标快速移动时频繁查询）
            hoverTranslationTimerRef.current = setTimeout(() => {
              // 🔧 关闭翻译调试日志
              // console.log('🔍 [TokenSpan] 开始查询翻译:', displayText)
              // addDebugLog('info', `延迟250ms后开始查询: "${displayText}"`, { word: displayText })
              queryQuickTranslation(displayText)
            }, 250)
          } else {
            const reason = !isTextToken ? 'not text token' :
                          hasVocabVisual ? 'has vocab notation' :
                          !hoverAllowed ? 'hover not allowed' :
                          displayText.trim().length === 0 ? 'empty word' : 'unknown'
            const skipData = {
              isTextToken,
              hasVocabVisual,
              hoverAllowed,
              word: displayText,
              reason
            }
            // 🔧 关闭翻译调试日志
            // console.log('⚠️ [TokenSpan] Hover翻译未触发:', skipData)
            // addDebugLog('warning', `Hover未触发: "${displayText}"`, skipData)
          }
        }}
        onMouseLeave={() => {
          // 只有可选择的token才清除hover效果
          if (selectable) {
            selOnLeave()
          }
          if (isTextToken && tokenHasExplanation) {
            setHoveredTokenId(null)
          }
          // 延迟隐藏notation（而不是立即隐藏）
          if (hasVocabVisual) {
            scheduleHideNotation()
          }
          // 🔧 新增：延迟清除hover翻译（给用户时间移动到 tooltip）
          if (isTextToken && displayText.trim().length > 0) {
            // 🔧 关闭翻译调试日志
            // addDebugLog('info', `Hover离开: "${displayText}"`, { word: displayText })
            // 🔧 修复：如果翻译查询还在进行中，等待查询完成后再决定是否隐藏
            // 延迟清除，如果鼠标移动到 tooltip 上，tooltip 的 onMouseEnter 会取消这个清除
            clearTranslationTimer()
            hoverTranslationTimerRef.current = setTimeout(() => {
              // 🔧 检查是否还有正在进行的查询
              // 如果有，延长延迟时间，让查询完成后再清除
              if (translationQueryRef.current) {
                // 🔧 关闭翻译调试日志
                // console.log('⏳ [TokenSpan] 翻译查询还在进行中，延长延迟清除时间')
                // 延长延迟时间到 500ms，给查询更多时间完成
                hoverTranslationTimerRef.current = setTimeout(() => {
                  clearTranslation()
                }, 500)
              } else {
                clearTranslation()
              }
            }, 200)
          } else {
            clearTranslation()
          }
          // 🔧 调用 token hover 离开回调（用于整句翻译）
          if (onTokenMouseLeave) {
            onTokenMouseLeave()
          }
          // 🔧 注意：分词下划线的显示/隐藏由 SentenceContainer 的 hover 状态控制
          // 这里不需要额外处理，因为当鼠标离开整个句子时，SentenceContainer 会处理
        }}
        onClick={(e) => { 
          // 只有可选择的token才响应点击
          if (selectable) { 
            if (typeof selOnClick === 'function') {
              selOnClick()
            }
            
            // 直接处理点击选择（toggle 行为）
            if (typeof addSingle === 'function') {
              addSingle(sentenceIdx, token)
            }
            
            e.preventDefault()
            e.stopPropagation()
          }
        }}
        className={[
          'px-0.5 rounded-sm transition-colors duration-150 select-none relative',
          cursorClass,
          bgClass,
          selectionTokenClass,
          // 只渲染 vocab 绿色下划线；grammar 改为句子徽标触发
          hasVocabVisual ? 'border-b-2 border-green-500' : ''
        ].join(' ')}
        style={{ color: '#111827' }}
      >
        {displayText}
        {/* 🔧 分词下划线：在 token 下方显示灰色下划线（表示 word token 的分词边界） */}
        {/* 🔧 只对文本类型的 token 显示下划线，不包括标点符号和空格 */}
        {showSegmentationUnderline && wordTokenInfo && isTextToken && token?.token_type !== 'punctuation' && token?.token_type !== 'space' && (() => {
          // 🔧 根据 token 在 word_token 中的位置，调整下划线的样式
          // 目标：同一个 word_token 内的字符下划线连续，不同 word_token 之间有间隙
          // 注意：token span 有 px-0.5 (左右各 2px padding)，下划线是绝对定位的
          // 下划线的 left 是相对于 token span 的内容区域（不包括 padding）的
          const { isFirstInWord, isLastInWord, isSingleCharWord } = wordTokenInfo
          
          let finalLeft = '0%'
          let finalWidth = '100%'
          
          // 🔧 统一基准：所有字符的下划线都从 padding 的左边缘开始（-2px），确保对齐
          // 然后通过宽度调整来实现连接或留空隙
          if (isSingleCharWord) {
            // 单独字符：从 padding 左边缘开始，但左右都有空隙（缩短到 75%，居中）
            // 调整 left 使下划线居中：从 padding 左边缘(-2px) + 内容区域12.5%开始
            finalLeft = 'calc(-2px + 12.5%)' // 从 padding 左边缘 + 内容区域12.5%开始（居中）
            finalWidth = '75%' // 宽度 75%
          } else if (isFirstInWord) {
            // 第一个字符：从 padding 左边缘开始，延伸到右侧（覆盖右侧 padding，与下一个字符连接）
            finalLeft = '-2px' // 从 padding 左边缘开始，统一基准
            finalWidth = 'calc(100% + 4px)' // 总宽度：内容(100%) + 左侧padding(2px) + 右侧padding(2px)
          } else if (isLastInWord) {
            // 最后一个字符：从 padding 左边缘开始（与前一个字符对齐），右侧留空隙
            finalLeft = '-2px' // 从 padding 左边缘开始，统一基准
            finalWidth = 'calc(100% + 4px - 10px)' // 总宽度减去右侧空隙（10px）
          } else {
            // 中间字符：从 padding 左边缘开始（与前一个字符对齐），延伸到右侧（与下一个字符连接）
            finalLeft = '-2px' // 从 padding 左边缘开始，统一基准
            finalWidth = 'calc(100% + 4px)' // 总宽度：内容(100%) + 左侧padding(2px) + 右侧padding(2px)
          }
          
          return (
            <span 
              className="absolute bottom-[-2px] h-[1.5px] bg-gray-400 pointer-events-none opacity-60"
              style={{ 
                // 确保下划线在 vocab 绿色下划线下方（如果有的话）
                zIndex: hasVocabVisual ? 0 : 1,
                left: finalLeft,
                width: finalWidth
              }}
            />
          )
        })()}
      </span>
      
      {isTextToken && tokenHasExplanation && (
        <VocabTooltip 
          token={token} 
          explanation={tokenExplanation} 
          isVisible={isHovered} 
        />
      )}

      {/* 🔧 新增：快速翻译tooltip（只在没有vocab notation时显示） */}
      {isTextToken && !hasVocabVisual && (
        <QuickTranslationTooltip
          word={displayText}
          translation={quickTranslation}
          translationSource={translationSource}
          isVisible={showQuickTranslation}
          anchorRef={anchorRef}
          position="bottom"
          showWord={false}
          isLoading={isLoadingTranslation}
          onSpeak={handleSpeak}
          onMouseEnter={handleTooltipMouseEnter}
          onMouseLeave={handleTooltipMouseLeave}
          onAskAI={onAskAI ? async () => {
            console.log('🔘 [TokenSpan] onAskAI 回调被调用', { 
              token, 
              sentenceIdx,
              displayText,
              hasOnAskAI: !!onAskAI,
              tokenType: typeof token,
              sentenceIdxType: typeof sentenceIdx
            })
            try {
              // 🔧 调用 onAskAI，它可能是异步函数
              const result = onAskAI(token, sentenceIdx)
              // 🔧 如果是 Promise，等待完成
              if (result && typeof result.then === 'function') {
                await result
              }
              console.log('✅ [TokenSpan] onAskAI 调用成功')
            } catch (error) {
              console.error('❌ [TokenSpan] onAskAI 调用失败', {
                error: error.message,
                stack: error.stack,
                token,
                sentenceIdx
              })
            }
          } : null}
        />
      )}
      
      {/* 暂时注释掉 VocabExplanationButton - 以后可能会用到 */}
      {/* {isTextToken && selected && selectedTokenIds.size === 1 && (
        <VocabExplanationButton 
          token={token} 
          onGetExplanation={handleGetExplanation}
          markAsAsked={markAsAsked}
          articleId={articleId}
          sentenceIdx={sentenceIdx}
        />
      )} */}
      
      {/* VocabNotationCard - 对有 vocab 标注（来自vocab_notations或asked tokens）的 token 显示 */}
      {hasVocabVisual && showNotation && (
        <VocabNotationCard 
          isVisible={showNotation}
          note={notationContent || "This is a test note"}
          textId={articleId}
          sentenceId={tokenSentenceId}
          // 🔧 修复：如果匹配到了 notation，使用该 notation 的 token_id（确保显示正确的 vocab example）
          tokenIndex={matchedNotation?.token_id ?? tokenSentenceTokenId}
          onMouseEnter={handleNotationMouseEnter}
          onMouseLeave={handleNotationMouseLeave}
          getVocabExampleForToken={getVocabExampleForToken}
          anchorRef={anchorRef}
        />
      )}
      
      {/* GrammarNotation is now handled at sentence level in SentenceContainer */}
    </span>
  )
}


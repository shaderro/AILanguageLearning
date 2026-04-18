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
import { languageCodeToBCP47 } from '../../../contexts/LanguageContext'
import { useUiLanguage } from '../../../contexts/UiLanguageContext'
import { useTranslationDebug } from '../../../contexts/TranslationDebugContext'
import { logVocabNotationDebug } from '../utils/vocabNotationDebug'

// 🔧 已移除：notationVisibilityStore 不再需要
// tooltip 状态现在由 NotationContext 中的 activeVocabNotation 全局管理，
// 即使 TokenSpan 重挂载，状态也不会丢失

/**
 * TokenSpan - Renders individual token with selection and vocab explanation features
 */
export default function TokenSpan({
  token,
  tokenIdx,
  sentenceIdx,
  sentenceId = null,
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
  highlightedRange = null,
  // 🔧 新增：Token是否不足（用于禁用AI详细解释按钮）
  isTokenInsufficient = false,
  // 🔧 新增：源语言代码（来自句子/文章），用于单词自动翻译
  sourceLanguageCode = null,
  // 🔧 新增：自动翻译开关（只有开启才显示 hover 单词翻译）
  autoTranslationEnabled = false,
  autoHintTarget = null,
  autoHintPreviewing = false,
  autoHintTooltipVisible = false,
  autoHintFading = false,
  autoHintMessage = '',
  onAutoHintInteraction = null,
}) {
  // 从 NotationContext 获取 notation 相关功能
  const notationContext = useContext(NotationContext)
  const {
    getGrammarNotationsForSentence,
    getVocabNotationsForSentence,
    getVocabExampleForToken,
    isTokenAsked: isTokenAskedFromContext,
    activeVocabNotation,  // 🔧 全局 tooltip 状态
    setActiveVocabNotation  // 🔧 全局 tooltip setter
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
  const { uiLanguage } = useUiLanguage() // 🔧 目标语言跟随 UI 语言（与句子翻译一致）
  // 清除调试日志
  const [quickTranslation, setQuickTranslation] = useState(null)
  const [translationSource, setTranslationSource] = useState(null) // 'dictionary' | 'translation'
  const [showQuickTranslation, setShowQuickTranslation] = useState(false)
  const [isLoadingTranslation, setIsLoadingTranslation] = useState(false)
  const hoverTranslationTimerRef = useRef(null)
  const translationQueryRef = useRef(null) // 用于取消正在进行的查询
  const activeHoverTextRef = useRef(null) // 🔧 当前 hover 会话“固定查询词”，用于避免错乱
  const [hoverQueryText, setHoverQueryText] = useState(null) // 🔧 tooltip 绑定的词（冻结）

  const normalizeLangCode = useCallback((code) => {
    if (!code) return null
    const s = String(code).trim().toLowerCase()
    if (['zh', 'zh-cn', 'zh_cn', 'zh-hans', '中文', 'chinese'].includes(s)) return 'zh'
    if (['zh-tw', 'zh_tw', '繁体中文'].includes(s)) return 'zh'
    if (['en', 'english', '英文'].includes(s)) return 'en'
    if (['de', 'german', '德文', '德语'].includes(s)) return 'de'
    if (['ja', 'japanese', '日语', '日本語', '日文'].includes(s)) return 'ja'
    // 兜底：取前缀（例如 fr-FR / ja-JP）
    const prefix = s.split(/[-_]/)[0]
    return prefix && prefix.length === 2 ? prefix : null
  }, [])

  // 获取源语言（从句子/文章数据传入，或使用默认值）
  const sourceLang = useMemo(() => {
    if (sourceLanguageCode && typeof sourceLanguageCode === 'string') {
      return normalizeLangCode(sourceLanguageCode) || sourceLanguageCode
    }
    // 默认回退：德语
    return 'de'
  }, [sourceLanguageCode, normalizeLangCode])

  // 获取目标语言（系统语言或全局选择的语言）
  // 🔧 如果目标语言和源语言相同，使用系统语言或fallback到英文/中文
  const targetLang = useMemo(() => {
    // 🔧 统一逻辑：单词自动翻译目标语言始终跟随 UI 语言（与整句翻译一致）
    const uiLangCode =
      uiLanguage === 'en'
        ? 'en'
        : uiLanguage === 'zh'
          ? 'zh'
          : (getSystemLanguage() || 'zh')

    if (!sourceLang) {
      return uiLangCode
    }

    // 如果 UI 语言和源语言相同，则翻译成另一种主要语言
    if (uiLangCode === sourceLang) {
      return sourceLang === 'en' ? 'zh' : 'en'
    }

    return uiLangCode
  }, [uiLanguage, sourceLang])

  // 🔧 单词翻译输入：优先使用 word token（例如中文分词后的词），避免逐字翻译导致错乱
  const translationInputText = useMemo(() => {
    const candidate = wordTokenInfo?.wordBody
    if (typeof candidate === 'string' && candidate.trim().length > 0) {
      return candidate
    }
    return displayText
  }, [wordTokenInfo, displayText])

  // 🔧 hover翻译查询函数
  const queryQuickTranslation = useCallback(async (word) => {
    if (!word || word.trim().length === 0) {
      return
    }

    // 取消之前的查询
    if (translationQueryRef.current) {
      translationQueryRef.current = null
    }

    const currentQuery = { word }
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
      
      // 🔧 单词查询：当前阶段仅使用翻译 API（不使用词典）
      // 🔧 返回包含来源信息的对象，方便调试不同来源
      const translationResult = await getQuickTranslation(word, sourceLang, targetLang, {
        // debugLogger, // 🔧 保持关闭调试日志
        isWord: true,          // 明确指定为单词查询
        useDictionary: false,  // 不使用词典 API，只用翻译 API
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
      if (translationQueryRef.current === currentQuery && activeHoverTextRef.current === word) {
        setQuickTranslation(translation)
        setTranslationSource(translationSource) // 保存来源信息（translation / dictionary 等）
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
      if (translationQueryRef.current === currentQuery && activeHoverTextRef.current === word) {
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
    setHoverQueryText(null)
    activeHoverTextRef.current = null
    // 取消正在进行的查询
    translationQueryRef.current = null
  }, [clearTranslationTimer])

  // 🔧 自动翻译关闭时，清理单词翻译状态
  useEffect(() => {
    if (!autoTranslationEnabled) {
      clearTranslation()
    }
  }, [autoTranslationEnabled, clearTranslation])

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
    // 避免 token 级发音打断文章整句朗读
    if (typeof window !== 'undefined' && (window.__ARTICLE_TTS_ACTIVE__ || window.__ARTICLE_TTS_OWNER__ === 'article')) {
      return
    }
    
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      // 不再主动 cancel 正在进行的朗读，避免打断主 TTS 会话
      if (window.speechSynthesis.speaking || window.speechSynthesis.pending) {
        return
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
  // 优先使用真实 sentence_id，只有缺失时才回退到 sentenceIdx + 1
  const tokenSentenceId = sentenceId ?? (sentenceIdx + 1)
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
  const grammarNotations = getGrammarNotationsForSentence ? getGrammarNotationsForSentence(tokenSentenceId) : []
  const hasGrammar = grammarNotations.length > 0
  
  // 检查当前token是否在grammar notation的marked_token_ids中
  // 如果marked_token_ids为空，则整个句子都有grammar notation
  // 取消 grammar 灰色下划线的渲染，改用句子右下角徽标触发卡片
  const isInGrammarNotation = false

  // 优先检查 vocab notation（从新API加载）
  // vocab notation是数据源，asked tokens只是兼容层
  // 🔧 移除 useMemo，直接调用函数，确保每次渲染都能获取最新数据
  const vocabNotationsForSentence = typeof getVocabNotationsForSentence === 'function'
    ? getVocabNotationsForSentence(tokenSentenceId)
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
  const autoHintForThisToken = Boolean(
    autoHintTarget &&
    autoHintTarget.type === 'vocab' &&
    Number(autoHintTarget.sentenceId) === Number(tokenSentenceId) &&
    Number(autoHintTarget.tokenId) === Number(tokenSentenceTokenId)
  )

  // 🔧 检查是否在高亮范围内
  const isHighlighted = highlightedRange && 
    highlightedRange.sentenceIdx === sentenceIdx &&
    tokenIdx >= highlightedRange.startTokenIdx &&
    tokenIdx <= highlightedRange.endTokenIdx
  
  // 🔧 朗读与选中样式可叠加：绿色朗读底层 + 黄色选中上层强调
  const bgClass = [
    isCurrentlyReading ? '!bg-green-300 ring-1 ring-green-400' : '',
    selected ? 'ring-2 ring-yellow-400 shadow-[inset_0_0_0_9999px_rgba(253,224,71,0.35)]' : '',
    !isCurrentlyReading && !selected && isHighlighted ? 'bg-yellow-200' : '',
    !isCurrentlyReading && !selected && !isHighlighted && hoverAllowed ? 'bg-transparent hover:bg-yellow-200' : '',
    !isCurrentlyReading && !selected && !isHighlighted && !hoverAllowed ? 'bg-transparent' : ''
  ].filter(Boolean).join(' ')
  const tokenHasExplanation = isTextToken && hasExplanation(token)
  const tokenExplanation = isTextToken ? getExplanation(token) : null
  const isHovered = hoveredTokenId === uid

  // 为当前 token 构造一个稳定的可序列化 key，用于全局可见性缓存
  // 当前实现中仅用于调试追踪，不再从缓存恢复可见性，避免跨 hover 会话的“幽灵状态”
  const notationKey = useMemo(
    () => `${articleId}:${tokenSentenceId}:${tokenSentenceTokenId}`,
    [articleId, tokenSentenceId, tokenSentenceTokenId]
  )
  
  // 🔧 从全局状态计算当前 token 是否应该显示 tooltip
  // activeVocabNotation 格式：{ articleId, sentenceId, tokenId } 或 null
  const showNotation = useMemo(() => {
    if (!activeVocabNotation) return false
    return (
      activeVocabNotation.articleId === articleId &&
      activeVocabNotation.sentenceId === tokenSentenceId &&
      activeVocabNotation.tokenId === tokenSentenceTokenId
    )
  }, [activeVocabNotation, articleId, tokenSentenceId, tokenSentenceTokenId])

  // 🔧 记录鼠标是否正在悬停当前 token（用于“hover 期间数据到达后自动展示”）
  const [isMouseOverToken, setIsMouseOverToken] = useState(false)
  // 🔧 会话级 hover 标记：只要鼠标在 token 或卡片上，就是 true
  const isHoveringRef = useRef(false)
  const hideNotationTimerRef = useRef(null)

  // 🔧 封装带日志的全局状态更新函数
  const setShowNotationWithTrace = useCallback(
    (nextValue, reason) => {
      const prevValue = showNotation
      
      // 🔧 如果新值和当前值相同，跳过更新，避免不必要的重新渲染
      if (prevValue === nextValue) {
        logVocabNotationDebug('[isVisible trace]', {
          source: 'TokenSpan',
          prevValue,
          nextValue,
          reason: `${reason} (skipped, same value)`,
          articleId,
          sentenceId: tokenSentenceId,
          tokenId: tokenSentenceTokenId,
          displayText,
          isMouseOverToken,
          isHoveringSession: isHoveringRef.current,
        })
        return
      }
      
      const nextNotation = nextValue
        ? { articleId, sentenceId: tokenSentenceId, tokenId: tokenSentenceTokenId }
        : null
      
      logVocabNotationDebug('[isVisible trace]', {
        source: 'TokenSpan',
        prevValue,
        nextValue,
        reason,
        articleId,
        sentenceId: tokenSentenceId,
        tokenId: tokenSentenceTokenId,
        displayText,
        isMouseOverToken,
        isHoveringSession: isHoveringRef.current,
      })
      
      if (setActiveVocabNotation) {
        setActiveVocabNotation(nextNotation)
      }
    },
    [articleId, tokenSentenceId, tokenSentenceTokenId, displayText, isMouseOverToken, showNotation, setActiveVocabNotation]
  )
  
  // 获取该token的notation内容
  const notationContent = isAsked && getNotationContent 
    ? getNotationContent(articleId, tokenSentenceId, tokenSentenceTokenId)
    : null
  
  // 延迟隐藏 notation：仅当延时结束时仍不在 token 或卡片上，才真正隐藏
  const scheduleHideNotation = () => {
    // 清除之前的延迟隐藏
    if (hideNotationTimerRef.current) {
      clearTimeout(hideNotationTimerRef.current)
    }
    logVocabNotationDebug('[hover-session] scheduleHideNotation', {
      articleId,
      sentenceId: tokenSentenceId,
      tokenId: tokenSentenceTokenId,
      displayText,
      hasVocabVisual,
      isMouseOverToken,
      isHoveringSession: isHoveringRef.current,
    })
    // 设置新的延迟隐藏（200ms后检查是否仍然未 hover）
    hideNotationTimerRef.current = setTimeout(() => {
      const currentShowNotation = showNotation  // 捕获当前值
      logVocabNotationDebug('[hover-session] hideTimeoutFired', {
        articleId,
        sentenceId: tokenSentenceId,
        tokenId: tokenSentenceTokenId,
        displayText,
        hasVocabVisual,
        isMouseOverToken,
        isHoveringSession: isHoveringRef.current,
        showNotationBefore: currentShowNotation,
      })
      if (!isHoveringRef.current) {
        setShowNotationWithTrace(false, 'mouseLeaveTimeout')
      } else {
        logVocabNotationDebug('[isVisible trace]', {
          source: 'TokenSpan',
          value: currentShowNotation,
          reason: 'mouseLeaveTimeoutCancelledByHover',
          articleId,
          sentenceId: tokenSentenceId,
          tokenId: tokenSentenceTokenId,
          displayText,
        })
      }
    }, 200)
  }
  
  // 取消延迟隐藏（保持显示）
  const cancelHideNotation = () => {
    if (hideNotationTimerRef.current) {
      clearTimeout(hideNotationTimerRef.current)
      hideNotationTimerRef.current = null
      const currentShowNotation = showNotation  // 捕获当前值
      logVocabNotationDebug('[hover-session] cancelHideNotation', {
        articleId,
        sentenceId: tokenSentenceId,
        tokenId: tokenSentenceTokenId,
        displayText,
        hasVocabVisual,
        isMouseOverToken,
        isHoveringSession: isHoveringRef.current,
        showNotation: currentShowNotation,
      })
    }
  }
  
  // 处理 notation 的 mouse enter（鼠标进入卡片）
  const handleNotationMouseEnter = () => {
    isHoveringRef.current = true
    cancelHideNotation()  // 取消隐藏
    setShowNotationWithTrace(true, 'cardMouseEnter')  // 确保显示
  }
  
  // 处理 notation 的 mouse leave（鼠标离开卡片）
  const handleNotationMouseLeave = () => {
    isHoveringRef.current = false
    scheduleHideNotation()  // 延迟隐藏
  }

  // 🔧 记录 showNotation 的变化，方便对比 TokenSpan 与 VocabNotationCard 的状态
  useEffect(() => {
    if (!isTextToken) return
    logVocabNotationDebug('🔁 [TokenSpan] showNotation state changed', {
      articleId,
      sentenceId: tokenSentenceId,
      tokenId: tokenSentenceTokenId,
      displayText,
      showNotation,
      hasVocabNotationForToken,
      hasVocabVisual,
      isAsked,
    })
  }, [
    showNotation,
    articleId,
    tokenSentenceId,
    tokenSentenceTokenId,
    displayText,
    hasVocabNotationForToken,
    hasVocabVisual,
    isAsked,
    isTextToken,
  ])

  // 🔧 修复：如果 vocab notations 在“正在 hover”期间才加载完成，自动展示 tooltip（避免必须第二次 hover）
  useEffect(() => {
    if (!isMouseOverToken) return
    if (!hasVocabVisual) return
    if (showNotation) return

    logVocabNotationDebug('🟢 [TokenSpan] notations arrived while hovering -> show tooltip', {
      articleId,
      sentenceId: tokenSentenceId,
      tokenId: tokenSentenceTokenId,
      displayText,
      hasVocabVisual,
      hasVocabNotationForToken,
      isAsked,
    })
    cancelHideNotation()
    setShowNotationWithTrace(true, 'hoverNotationsArrived')
  }, [
    isMouseOverToken,
    hasVocabVisual,
    showNotation,
    articleId,
    tokenSentenceId,
    tokenSentenceTokenId,
    displayText,
    hasVocabNotationForToken,
    isAsked,
  ])

  return (
    <span
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
          if (autoHintForThisToken) {
            onAutoHintInteraction?.({
              type: 'vocab',
              sentenceId: tokenSentenceId,
              tokenId: tokenSentenceTokenId,
            })
          }
          setIsMouseOverToken(true)
          isHoveringRef.current = true
          // 只有可选择的token才触发hover效果
          if (selectable) {
            selOnEnter()
          }
          if (isTextToken && tokenHasExplanation) {
            setHoveredTokenId(uid)
          }
          if (isTextToken) {
            const currentShowNotation = showNotation  // 捕获当前值
        logVocabNotationDebug('👆 [TokenSpan] mouse enter', {
              articleId,
              sentenceId: tokenSentenceId,
              tokenId: tokenSentenceTokenId,
              displayText,
              selectable,
              hasVocabNotationForToken,
              hasVocabVisual,
              isAsked,
              showNotationBefore: currentShowNotation,
            })
          }
          // 如果有vocab notation（来自vocab_notations或asked tokens），显示notation卡片
          if (hasVocabVisual) {
            cancelHideNotation()  // 取消任何待处理的隐藏
            setShowNotationWithTrace(true, 'mouseEnter')
            if (isTextToken) {
              logVocabNotationDebug('🟢 [TokenSpan] showNotation=true (triggered by mouse enter)', {
                articleId,
                sentenceId: tokenSentenceId,
                tokenId: tokenSentenceTokenId,
                displayText,
                tokenIndexForExample: matchedNotation?.token_id ?? tokenSentenceTokenId,
              })
            }
          }

          // 🔧 单词自动翻译：在没有 vocab notation 时，hover 一小段时间后触发
          if (autoTranslationEnabled && isTextToken && !hasVocabVisual && hoverAllowed && translationInputText.trim().length > 0) {
            // 冻结本次 hover 的查询词，避免 wordTokenInfo 异步变化导致“显示词/翻译词”错乱
            activeHoverTextRef.current = translationInputText
            setHoverQueryText(translationInputText)
            clearTranslationTimer()
            hoverTranslationTimerRef.current = setTimeout(() => {
              queryQuickTranslation(translationInputText)
            }, 400)
          }
        }}
        onMouseLeave={() => {
          setIsMouseOverToken(false)
          isHoveringRef.current = false
          // 只有可选择的token才清除hover效果
          if (selectable) {
            selOnLeave()
          }
          if (isTextToken && tokenHasExplanation) {
            setHoveredTokenId(null)
          }
          if (isTextToken) {
            const currentShowNotation = showNotation  // 捕获当前值
            logVocabNotationDebug('👋 [TokenSpan] mouse leave', {
              articleId,
              sentenceId: tokenSentenceId,
              tokenId: tokenSentenceTokenId,
              displayText,
              hasVocabNotationForToken,
              hasVocabVisual,
              isAsked,
              showNotationBefore: currentShowNotation,
            })
          }
          // 延迟隐藏notation（而不是立即隐藏）
          if (hasVocabVisual) {
            scheduleHideNotation()
          }
          // 🔧 单词自动翻译：hover 离开后延迟清理翻译状态
          if (autoTranslationEnabled && isTextToken && translationInputText.trim().length > 0) {
            clearTranslationTimer()
            hoverTranslationTimerRef.current = setTimeout(() => {
              if (translationQueryRef.current) {
                // 如果还有进行中的查询，再延迟一点再清理
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
          if (autoHintForThisToken) {
            onAutoHintInteraction?.({
              type: 'vocab',
              sentenceId: tokenSentenceId,
              tokenId: tokenSentenceTokenId,
            })
          }
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
          'px-0.5 rounded-sm transition-colors duration-150 select-none relative inline-flex items-center',
          cursorClass,
          selectionTokenClass,
          bgClass,
          autoHintForThisToken && autoHintPreviewing ? 'animate-pulse' : '',
        ].join(' ')}
        style={{ color: '#111827' }}
      >
        <span className={`relative inline-block ${hasVocabVisual ? 'pr-3' : ''}`}>
          {displayText}
          {hasVocabVisual && (
            <span
              aria-hidden="true"
              className="pointer-events-none absolute bottom-[0px] left-0 h-[2px] w-full bg-emerald-400/70"
            />
          )}
          {hasVocabVisual && (
            <span
              aria-hidden="true"
              className="pointer-events-none absolute right-0 top-[0.15em] inline-flex h-3.5 w-3.5 items-center justify-center leading-none text-emerald-500"
            >
              {isMouseOverToken ? (
                <span className="text-[10px]">✨</span>
              ) : (
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              )}
            </span>
          )}
        </span>
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

      {/* 单词快速翻译 tooltip（仅在自动翻译开启时显示；只显示翻译，不显示原始单词；显示在单词上方） */}
      {autoTranslationEnabled && isTextToken && !hasVocabVisual && (
        <QuickTranslationTooltip
          word={hoverQueryText || translationInputText}
          translation={quickTranslation}
          translationSource={translationSource}
          isVisible={showQuickTranslation}
          anchorRef={anchorRef}
          position="top"
          showWord={false} // 按要求：不显示原始词汇，只显示翻译
          isLoading={isLoadingTranslation}
          onSpeak={handleSpeak}
          onMouseEnter={handleTooltipMouseEnter}
          onMouseLeave={handleTooltipMouseLeave}
          // 🔧 不传 onAskAI：不显示“AI详细解释”的幽灵按钮
          uiScale={0.67}
          fullWidth={false}
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
      {/* 🔧 始终挂载卡片组件（只在 hasVocabVisual 为 true 时），通过 isVisible 控制显示，避免第一次 hover 时因为状态抖动被卸载 */}
      {hasVocabVisual && (
        <VocabNotationCard 
          isVisible={showNotation}
          note={notationContent || ""}
          textId={articleId}
          sentenceId={tokenSentenceId}
          matchedNotation={matchedNotation}
          // 🔧 修复：如果匹配到了 notation，使用该 notation 的 token_id（确保显示正确的 vocab example）
          tokenIndex={matchedNotation?.token_id ?? tokenSentenceTokenId}
          onMouseEnter={handleNotationMouseEnter}
          onMouseLeave={handleNotationMouseLeave}
          getVocabExampleForToken={getVocabExampleForToken}
          anchorRef={anchorRef}
          autoHintMessage={autoHintForThisToken && autoHintTooltipVisible ? autoHintMessage : ''}
          autoHintFading={autoHintForThisToken ? autoHintFading : false}
          autoOffsetY={autoHintForThisToken && autoHintTooltipVisible ? 8 : 0}
          onTooltipInteract={() => {
            if (!autoHintForThisToken) return
            onAutoHintInteraction?.({
              type: 'vocab',
              sentenceId: tokenSentenceId,
              tokenId: tokenSentenceTokenId,
            })
          }}
        />
      )}
      
      {/* GrammarNotation is now handled at sentence level in SentenceContainer */}
    </span>
  )
}


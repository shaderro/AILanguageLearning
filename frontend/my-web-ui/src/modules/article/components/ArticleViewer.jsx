import React, { useMemo, useEffect, useRef, useState, useCallback, useLayoutEffect, memo } from 'react'
import { createPortal } from 'react-dom'
import { useArticle } from '../../../hooks/useApi'
import { useTokenSelection } from '../hooks/useTokenSelection'
import { useTokenDrag } from '../hooks/useTokenDrag'
import { useVocabExplanations } from '../hooks/useVocabExplanations'
import { useSentenceInteraction } from '../hooks/useSentenceInteraction'
import { useUser } from '../../../contexts/UserContext'
import { useUIText } from '../../../i18n/useUIText'
import { useSelection } from '../selection/hooks/useSelection'
import { useSpeechSynthesis } from 'react-speech-kit'
import { useLanguage, languageNameToCode, languageCodeToBCP47 } from '../../../contexts/LanguageContext'
import { useTranslationDebug } from '../../../contexts/TranslationDebugContext'
import SentenceContainer from './SentenceContainer'
import { useTokenHighlight } from '../hooks/useTokenHighlight'

/**
 * ArticleViewer - Main component for displaying and interacting with article content
 * 
 * 注意：Grammar 和 Vocab notation 相关的功能现在通过 NotationContext 提供，
 * 不再需要通过 props 传递
 */
function ArticleViewer({ 
  articleId, 
  onTokenSelect, 
  isTokenAsked, 
  markAsAsked,
  getNotationContent,
  setNotationContent,
  onSentenceSelect,
  targetSentenceId = null,  // 🔧 目标句子ID（用于自动滚动和高亮）
  onTargetSentenceScrolled = null,  // 🔧 滚动完成后的回调
  onAskAI = null,  // 🔧 AI详细解释回调
  isTokenInsufficient = false,  // 🔧 Token是否不足（用于禁用AI详细解释按钮）
  autoTranslationEnabled = false  // 🔧 自动翻译开关状态
}) {
  // Debug logging removed to improve performance
  const { userId } = useUser()
  const t = useUIText()
  const { selectedLanguage } = useLanguage() // 🔧 获取全局语言状态
  const { addLog: addDebugLog } = useTranslationDebug() // 🔧 仅用于 useTokenDrag 的日志
  
  // 🔧 调试：检查 userId 和 articleId 的稳定性
  const userIdRef = useRef(userId)
  const articleIdRef = useRef(articleId)
  useEffect(() => {
    if (userIdRef.current !== userId) {
      console.log('🔄 [ArticleViewer] userId 变化:', { old: userIdRef.current, new: userId })
      userIdRef.current = userId
    }
    if (articleIdRef.current !== articleId) {
      console.log('🔄 [ArticleViewer] articleId 变化:', { old: articleIdRef.current, new: articleId })
      articleIdRef.current = articleId
    }
  }, [userId, articleId])
  
  // 🔧 使用稳定的 userId（避免因 userId 变化导致查询循环）
  const stableUserId = useMemo(() => userId, [userId])
  const { data, isLoading, isError, error } = useArticle(articleId, stableUserId)
  
  // 🔧 调试：检查 useArticle 的状态
  useEffect(() => {
    console.log('🔍 [ArticleViewer] useArticle 状态:', {
      isLoading,
      isError,
      hasData: !!data,
      error: error?.message || error,
      articleId,
      userId: stableUserId
    })
  }, [isLoading, isError, data, error, articleId, stableUserId])

  const normalizeLanguageCode = (language) => {
    if (!language) return null
    const lower = String(language).trim().toLowerCase()
    if (['zh', 'zh-cn', 'zh_cn', 'zh-hans', '中文', 'chinese'].includes(lower)) return 'zh'
    if (['zh-tw', 'zh_tw', '繁体中文'].includes(lower)) return 'zh'
    if (['en', 'english', '英文'].includes(lower)) return 'en'
    if (['de', 'german', '德文', '德语'].includes(lower)) return 'de'
    if (lower.length === 2) return lower
    return null
  }

  const rawSentences = data?.data?.sentences
  const articleLanguage = data?.data?.language || null
  const articleLanguageCode = normalizeLanguageCode(articleLanguage)
  const articleIsNonWhitespace = articleLanguageCode
    ? ['zh', 'ja', 'ko'].includes(articleLanguageCode)
    : undefined

  const sentences = useMemo(() => {
    // 🔧 调试：检查数据格式
    console.log('🔍 [ArticleViewer] Processing data:', {
      hasData: !!data,
      dataKeys: data ? Object.keys(data) : [],
      hasDataData: !!data?.data,
      dataDataKeys: data?.data ? Object.keys(data.data) : [],
      rawSentences,
      isArray: Array.isArray(rawSentences),
      sentencesLength: Array.isArray(rawSentences) ? rawSentences.length : 'N/A',
      articleLanguage
    })
    if (!Array.isArray(rawSentences)) {
      console.warn('⚠️ [ArticleViewer] rawSentences 不是数组:', {
        rawSentences,
        type: typeof rawSentences,
        data: data?.data
      })
      return []
    }
    try {
      const processed = rawSentences.map((sentence) => ({
        ...sentence,
        language: sentence.language ?? articleLanguage,
        language_code: sentence.language_code ?? articleLanguageCode,
        is_non_whitespace: sentence.is_non_whitespace ?? articleIsNonWhitespace,
      }))
      console.log('✅ [ArticleViewer] 成功处理句子数据:', {
        inputLength: rawSentences.length,
        outputLength: processed.length,
        firstSentence: processed[0] ? {
          sentence_id: processed[0].sentence_id,
          hasTokens: !!processed[0].tokens,
          tokensLength: Array.isArray(processed[0].tokens) ? processed[0].tokens.length : 'N/A'
        } : null
      })
      return processed
    } catch (err) {
      console.error('❌ [ArticleViewer] 处理句子数据时出错:', err)
      console.error('❌ [ArticleViewer] 错误详情:', {
        rawSentencesType: typeof rawSentences,
        rawSentencesIsArray: Array.isArray(rawSentences),
        rawSentencesLength: Array.isArray(rawSentences) ? rawSentences.length : 'N/A',
        firstSentence: rawSentences?.[0]
      })
      return []
    }
  }, [data, rawSentences, articleLanguage, articleLanguageCode, articleIsNonWhitespace])

  // Vocab explanations management
  const {
    hoveredTokenId,
    setHoveredTokenId,
    handleGetExplanation,
    hasExplanation,
    getExplanation
  } = useVocabExplanations()

  // Sentence interaction management
  const {
    hoveredSentenceIndex,
    clickedSentenceIndex,
    selectedSentenceIndex,
    sentenceRefs,
    handleSentenceMouseEnter,
    handleSentenceMouseLeave,
    handleSentenceClick: originalHandleSentenceClick,
    clearSentenceInteraction,
    clearSentenceSelection,
    getSentenceBackgroundStyle,
    isSentenceInteracting,
    isSentenceSelected
  } = useSentenceInteraction()
  
  // 🔧 包装 handleSentenceClick，添加调试日志
  const handleSentenceClick = useCallback((sentenceIndex) => {
    console.log('🔧 [ArticleViewer] 包装的 handleSentenceClick 被调用', { 
      sentenceIndex, 
      originalHandleSentenceClick: typeof originalHandleSentenceClick,
      selectedSentenceIndex 
    })
    if (typeof originalHandleSentenceClick === 'function') {
      console.log('🔧 [ArticleViewer] 调用 originalHandleSentenceClick')
      originalHandleSentenceClick(sentenceIndex)
      console.log('🔧 [ArticleViewer] originalHandleSentenceClick 调用完成')
    } else {
      console.error('❌ [ArticleViewer] originalHandleSentenceClick 不是函数!', originalHandleSentenceClick)
    }
  }, [originalHandleSentenceClick, selectedSentenceIndex])

  // Selection context (new system) - need to sync with old token selection system
  const { clearSelection: clearSelectionContext, selectTokens: selectTokensInContext } = useSelection()

  // 🔧 稳定 useTokenSelection 的参数，避免因为参数引用变化导致 hook 重新执行
  const tokenSelectionParams = useMemo(() => ({
    sentences,
    onTokenSelect,
    articleId,
    clearSentenceSelection,
    selectTokensInContext,
    addDebugLog
  }), [
    sentences, // sentences 已经用 useMemo 稳定了
    onTokenSelect, // 来自 props，应该稳定
    articleId, // 来自 props，应该稳定
    clearSentenceSelection, // 来自 useSentenceInteraction，可能不稳定
    selectTokensInContext, // 来自 useSelection，可能不稳定
    addDebugLog // 来自 useTranslationDebug，可能不稳定
  ])

  // Token selection management
  const {
    selectedTokenIds,
    activeSentenceIndex,
    activeSentenceRef,
    selectedTokenIdsRef, // 🔧 获取 ref，传递给 useTokenDrag
    clearSelection,
    addSingle,
    selectRange, // 🔧 获取 selectRange 函数
    emitSelection
  } = useTokenSelection(tokenSelectionParams)

  // 🔧 稳定 selectRange 函数引用，避免 useTokenDrag 的 useEffect 频繁重新执行
  const selectRangeRef = useRef(selectRange)
  useEffect(() => {
    selectRangeRef.current = selectRange
  }, [selectRange])

  // Token click selection management
  const {
    handleBackgroundClick
  } = useTokenDrag({
    selectedTokenIdsRef,
    activeSentenceRef,
    clearSelection,
    clearSentenceSelection,
    addDebugLog,
    sentences,
    selectRange: selectRangeRef.current // 🔧 使用稳定的引用
  })

  // 🔧 Token highlight management (独立于 useTokenDrag)
  const {
    highlightedRange
  } = useTokenHighlight({
    addDebugLog,
    sentences
  })

  // Grammar notations management - 现在从props接收，不再创建新的hook实例
  // const {
  //   grammarNotations,
  //   isLoading: grammarNotationsLoading,
  //   error: grammarNotationsError,
  //   hasGrammarNotation,
  //   getGrammarNotation,
  //   getGrammarNotationsForSentence,
  //   reload: reloadGrammarNotations
  // } = useGrammarNotations(articleId)

  // Token notations management - 现在从props接收，不再创建新的hook实例
  // const { getNotationContent, setNotationContent } = useTokenNotations()

  // 🔧 滚动容器 ref（用于自动滚动到目标句子）
  const scrollContainerRef = useRef(null)
  const scrollPositionRef = useRef(0)
  const scrollRestoredRef = useRef(false)
  // 🔧 保持文章滚动位置，避免点击/重渲染时跳到顶部
  useEffect(() => {
    const sc = scrollContainerRef.current
    if (!sc) return
    const onScroll = () => {
      scrollPositionRef.current = sc.scrollTop
      if (articleId) {
        sessionStorage.setItem(`article_scroll_${articleId}`, String(sc.scrollTop))
      }
    }
    sc.addEventListener('scroll', onScroll, { passive: true })
    return () => sc.removeEventListener('scroll', onScroll)
  }, [articleId])

  useLayoutEffect(() => {
    if (scrollRestoredRef.current) return
    const sc = scrollContainerRef.current
    if (!sc) return
    const saved = articleId ? sessionStorage.getItem(`article_scroll_${articleId}`) : null
    const savedPos = saved ? parseInt(saved, 10) : 0
    sc.scrollTop = isNaN(savedPos) ? 0 : savedPos
    scrollPositionRef.current = sc.scrollTop
    scrollRestoredRef.current = true
  }, [articleId])
  
  // 🔧 目标句子闪烁状态
  const [flashingSentenceId, setFlashingSentenceId] = useState(null)
  
  // 🔧 朗读功能 - 必须在早期返回之前调用所有 hooks
  const { speak, speaking, cancel, voices, supported } = useSpeechSynthesis()
  const [isReading, setIsReading] = useState(false)
  const currentReadingIndexRef = useRef(0)
  const readingTimeoutRef = useRef(null)
  const isReadingRef = useRef(false) // 使用 ref 来跟踪朗读状态，避免闭包问题
  const isUserStoppedRef = useRef(false) // 跟踪是否是用户主动停止
  const [currentReadingToken, setCurrentReadingToken] = useState(null) // 跟踪当前正在朗读的 token {sentenceIndex, tokenIndex}
  const [currentReadingSentenceIndex, setCurrentReadingSentenceIndex] = useState(null) // 跟踪当前正在朗读的句子索引
  
  // 🔧 使用 ref 存储最新的 sentences，避免在 useCallback 依赖中导致频繁重新创建
  const sentencesRef = useRef(sentences)
  useEffect(() => {
    sentencesRef.current = sentences
  }, [sentences])
  
  // 🔧 朗读按钮容器 state - 必须在早期返回之前调用
  const [readAloudButtonContainer, setReadAloudButtonContainer] = useState(null)
  const containerRef = useRef(null) // 使用 ref 来保持容器引用，避免重新查找
  
  // 🔧 清理朗读状态 - 必须在早期返回之前调用
  useEffect(() => {
    return () => {
      if (readingTimeoutRef.current) {
        clearTimeout(readingTimeoutRef.current)
        readingTimeoutRef.current = null
      }
      // 🔧 只在组件卸载时清理，不要因为状态变化就取消朗读
      // 使用原生 API 的 cancel，而不是 react-speech-kit 的 cancel
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel()
      }
    }
  }, []) // 只在组件卸载时执行

  // 🔧 不再监听 speaking 状态变化，因为我们现在使用原生 API
  // react-speech-kit 的 speaking 状态可能与原生 API 不同步
  // 我们完全依赖 utterance.onend 事件来处理句子完成

  // 🔧 查找朗读按钮容器 - 使用 ref 来避免重复查找
  useEffect(() => {
    // 如果 ref 中已经有容器且容器还在 DOM 中，直接使用，不需要重新查找
    if (containerRef.current && document.body.contains(containerRef.current)) {
      if (containerRef.current !== readAloudButtonContainer) {
        setReadAloudButtonContainer(containerRef.current)
      }
      return
    }
    
    const findContainer = () => {
      // 如果 ref 中已经有容器且容器还在 DOM 中，直接使用
      if (containerRef.current && document.body.contains(containerRef.current)) {
        if (containerRef.current !== readAloudButtonContainer) {
          setReadAloudButtonContainer(containerRef.current)
        }
        return true
      }
      
      // 否则查找容器
      const container = document.getElementById('read-aloud-button-container')
      if (container) {
        containerRef.current = container
        setReadAloudButtonContainer(container)
        return true
      }
      return false
    }
    
    // 立即尝试查找
    if (!findContainer()) {
      // 如果容器还不存在，定期重试
      const intervalId = setInterval(() => {
        if (findContainer()) {
          clearInterval(intervalId)
        }
      }, 100)
      
      // 最多尝试 50 次（5秒）
      const maxAttempts = 50
      let attempts = 0
      const checkAttempts = setInterval(() => {
        attempts++
        if (attempts >= maxAttempts) {
          clearInterval(intervalId)
          clearInterval(checkAttempts)
        }
      }, 100)
      
      return () => {
        clearInterval(intervalId)
        clearInterval(checkAttempts)
      }
    }
  }, []) // 只在组件挂载时执行一次
  
  // 🔧 监听容器变化，确保在容器重新创建时能重新找到（仅在容器丢失时检查）
  useEffect(() => {
    // 只在容器确实丢失时才重新查找
    if (!readAloudButtonContainer || (readAloudButtonContainer && !document.body.contains(readAloudButtonContainer))) {
      const container = document.getElementById('read-aloud-button-container')
      if (container && container !== readAloudButtonContainer) {
        containerRef.current = container
        setReadAloudButtonContainer(container)
      }
    }
  }, [readAloudButtonContainer])
  
  // 🔧 自动滚动到目标句子并添加闪烁效果
  useEffect(() => {
    if (!targetSentenceId || sentences.length === 0 || !scrollContainerRef.current) {
      return
    }

    // 找到对应的句子索引（通过 sentence_id 匹配）
    const targetIndex = sentences.findIndex(s => {
      const sentenceId = s.sentence_id || (typeof s === 'object' && s.id)
      return sentenceId === targetSentenceId
    })

    if (targetIndex === -1) {
      console.warn(`⚠️ [ArticleViewer] 未找到 sentence_id=${targetSentenceId} 的句子`)
      return
    }

    // 等待 DOM 更新后滚动
    setTimeout(() => {
      // 🔧 通过 data-sentence-id 属性查找句子元素
      const container = scrollContainerRef.current
      if (!container) return
      
      const sentenceElement = container.querySelector(`[data-sentence-id="${targetSentenceId}"]`)
      
      if (sentenceElement && container) {
        // 计算滚动位置（使句子居中）
        const containerRect = container.getBoundingClientRect()
        const sentenceRect = sentenceElement.getBoundingClientRect()
        const scrollTop = container.scrollTop
        const sentenceTop = sentenceRect.top - containerRect.top + scrollTop
        const sentenceHeight = sentenceRect.height
        const containerHeight = containerRect.height

        // 滚动到句子中心位置
        const targetScrollTop = sentenceTop - (containerHeight / 2) + (sentenceHeight / 2)
        container.scrollTo({
          top: Math.max(0, targetScrollTop),
          behavior: 'smooth'
        })

        // 添加闪烁效果
        setFlashingSentenceId(targetSentenceId)
        
        // 5 秒后移除闪烁效果
        setTimeout(() => {
          setFlashingSentenceId(null)
          if (onTargetSentenceScrolled) {
            onTargetSentenceScrolled()
          }
        }, 5000)
      }
    }, 100) // 等待 DOM 渲染
  }, [targetSentenceId, sentences, onTargetSentenceScrolled])

  // Handle sentence selection changes（防重复触发：仅在索引变化时上报）
  const lastEmittedSentenceIndexRef = useRef(null)
  useEffect(() => {
    console.log('🔍 [ArticleViewer] useEffect triggered for sentence selection', {
      selectedSentenceIndex,
      lastEmitted: lastEmittedSentenceIndexRef.current,
      hasOnSentenceSelect: !!onSentenceSelect,
      sentencesLength: sentences?.length,
      hasSentence: !!sentences?.[selectedSentenceIndex],
      sentence: sentences?.[selectedSentenceIndex]
    })
    
    // 只有当 selectedSentenceIndex 发生变化且有对应的句子数据时才处理
    if (
      onSentenceSelect &&
      selectedSentenceIndex !== null &&
      selectedSentenceIndex !== lastEmittedSentenceIndexRef.current &&
      sentences[selectedSentenceIndex]
    ) {
      const selectedSentence = sentences[selectedSentenceIndex]
      const sentenceText = selectedSentence.tokens?.map(token => 
        typeof token === 'string' ? token : token.token_body
      ).join(' ') || ''

      console.log('✅ [ArticleViewer] Calling onSentenceSelect', {
        selectedSentenceIndex,
        sentenceText,
        selectedSentence
      })
      
      lastEmittedSentenceIndexRef.current = selectedSentenceIndex
      onSentenceSelect(selectedSentenceIndex, sentenceText, selectedSentence)
    } else {
      console.log('⚠️ [ArticleViewer] onSentenceSelect not called', {
        hasOnSentenceSelect: !!onSentenceSelect,
        selectedSentenceIndex,
        lastEmitted: lastEmittedSentenceIndexRef.current,
        hasSentence: !!sentences?.[selectedSentenceIndex]
      })
    }
    // 当 selectedSentenceIndex 变为 null 时，重置记录，避免下次选同一句子不触发
    if (selectedSentenceIndex === null) {
      lastEmittedSentenceIndexRef.current = null
    }
  }, [selectedSentenceIndex, sentences, onSentenceSelect])

  // ============================================================================
  // 🔧 Helper 函数（放在 hooks 之后、early return 之前）
  // ============================================================================
  
  // 🔧 获取句子的文本内容
  const getSentenceText = (sentence) => {
    if (!sentence) return ''
    
    // 如果有 sentence_body，直接使用
    if (sentence.sentence_body) {
      return sentence.sentence_body.trim()
    }
    
    // 否则从 tokens 构建
    if (sentence.tokens && Array.isArray(sentence.tokens)) {
      return sentence.tokens
        .map(token => {
          if (typeof token === 'string') {
            return token
          }
          // 处理 token 对象
          if (token.token_body) {
            return token.token_body
          }
          return ''
        })
        .filter(t => t.trim().length > 0) // 过滤空字符串
        .join('')
        .trim()
    }
    
    return ''
  }

  // 🔧 检测当前窗口内可见的第一行句子索引
  // 注意：这个函数在 handleReadAloud 内部被调用，所以需要使用 sentencesRef.current
  const getFirstVisibleSentenceIndex = () => {
    const currentSentences = sentencesRef.current
    if (!scrollContainerRef.current || currentSentences.length === 0) return 0
    
    const container = scrollContainerRef.current
    const containerRect = container.getBoundingClientRect()
    const containerTop = containerRect.top
    const containerBottom = containerRect.bottom
    
    // 首先检查第一个句子是否在可见区域内（即使只是部分可见）
    const firstSentenceElement = container.querySelector(`[data-sentence-index="0"]`)
    if (firstSentenceElement) {
      const firstSentenceRect = firstSentenceElement.getBoundingClientRect()
      const firstSentenceTop = firstSentenceRect.top
      const firstSentenceBottom = firstSentenceRect.bottom
      
      // 如果第一个句子的任何部分在可见区域内，返回第一个句子
      if (firstSentenceBottom > containerTop && firstSentenceTop < containerBottom) {
        console.log('🔊 [ArticleViewer] 第一个句子在可见区域内，返回索引 0')
        return 0
      }
    }
    
    // 如果第一个句子不在可见区域内，查找第一个可见的句子
    for (let i = 0; i < currentSentences.length; i++) {
      const sentenceElement = container.querySelector(`[data-sentence-index="${i}"]`)
      if (sentenceElement) {
        const sentenceRect = sentenceElement.getBoundingClientRect()
        const sentenceTop = sentenceRect.top
        const sentenceBottom = sentenceRect.bottom
        
        // 检查句子是否在容器的可见区域内
        // 如果句子的任何部分在可见区域内，就认为它是可见的
        if (sentenceBottom > containerTop && sentenceTop < containerBottom) {
          console.log('🔊 [ArticleViewer] 找到第一个可见句子索引:', i)
          return i
        }
      }
    }
    
    // 如果没找到可见的句子，返回第一个句子
    console.log('🔊 [ArticleViewer] 未找到可见句子，返回索引 0')
    return 0
  }

  // 🔧 等待语音列表加载完成
  const ensureVoicesLoaded = async () => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      return false
    }
    
    let voices = window.speechSynthesis.getVoices()
    
    // 如果语音列表已加载，直接返回
    if (voices.length > 0) {
      console.log('🔊 [ArticleViewer] 语音列表已加载，共', voices.length, '个语音')
      return true
    }
    
    console.log('🔊 [ArticleViewer] 等待语音列表加载...')
    
    // 如果语音列表为空，等待加载
    return new Promise((resolve) => {
      // 先尝试触发 getVoices（某些浏览器需要这个）
      window.speechSynthesis.getVoices()
      
      let resolved = false
      
      // 设置超时保护
      const timeout = setTimeout(() => {
        if (!resolved) {
          resolved = true
          voices = window.speechSynthesis.getVoices()
          const success = voices.length > 0
          console.log('🔊 [ArticleViewer] 语音列表加载超时，结果:', success, '语音数量:', voices.length)
          resolve(success)
        }
      }, 2000)
      
      // 监听语音列表变化事件
      const onVoicesChanged = () => {
        if (!resolved) {
          voices = window.speechSynthesis.getVoices()
          if (voices.length > 0) {
            resolved = true
            clearTimeout(timeout)
            // 恢复原来的监听器（如果有）
            const originalHandler = window.speechSynthesis._originalOnVoicesChanged
            if (originalHandler) {
              window.speechSynthesis.onvoiceschanged = originalHandler
              delete window.speechSynthesis._originalOnVoicesChanged
            } else {
              window.speechSynthesis.onvoiceschanged = null
            }
            console.log('🔊 [ArticleViewer] 语音列表加载完成，共', voices.length, '个语音')
            resolve(true)
          }
        }
      }
      
      // 检查是否支持 onvoiceschanged 事件
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        // 保存原来的监听器（如果有）
        if (window.speechSynthesis.onvoiceschanged) {
          window.speechSynthesis._originalOnVoicesChanged = window.speechSynthesis.onvoiceschanged
        }
        window.speechSynthesis.onvoiceschanged = onVoicesChanged
      } else {
        // 如果不支持事件，等待一段时间后重试
        setTimeout(() => {
          if (!resolved) {
            resolved = true
            voices = window.speechSynthesis.getVoices()
            clearTimeout(timeout)
            const success = voices.length > 0
            console.log('🔊 [ArticleViewer] 语音列表加载完成（无事件支持），结果:', success, '语音数量:', voices.length)
            resolve(success)
          }
        }, 500)
      }
    })
  }

  // 🔧 根据语言代码获取对应的语音（确保从当前可用的语音列表中获取）
  const getVoiceForLanguage = (langCode) => {
    // 确保从最新的语音列表中获取
    const availableVoices = typeof window !== 'undefined' && window.speechSynthesis 
      ? window.speechSynthesis.getVoices() 
      : (voices || [])
    
    if (!availableVoices || availableVoices.length === 0) {
      console.warn('⚠️ [ArticleViewer] 没有可用的语音')
      return null
    }
    
    // 语言代码映射
    const langMap = {
      'de': 'de-DE',
      'en': 'en-US',
      'zh': 'zh-CN',
      'fr': 'fr-FR',
      'es': 'es-ES',
      'it': 'it-IT',
      'ja': 'ja-JP',
      'ko': 'ko-KR',
    }
    
    const targetLang = langMap[langCode] || langCode
    
    // 优先查找完全匹配的语音
    let voice = availableVoices.find(v => v.lang === targetLang)
    
    // 如果找不到，查找语言代码前缀匹配的
    if (!voice) {
      const langPrefix = targetLang.split('-')[0]
      voice = availableVoices.find(v => v.lang && v.lang.startsWith(langPrefix))
    }
    
    // 如果还是找不到，使用默认语音（通常是第一个）
    if (!voice && availableVoices.length > 0) {
      voice = availableVoices[0]
      console.warn(`⚠️ [ArticleViewer] 未找到 ${targetLang} 语音，使用默认语音: ${voice.name}`)
    }
    
    return voice || null
  }

  // ============================================================================
  // 🔧 所有 Hooks（必须在 early return 之前）
  // ============================================================================
  
  // 🔧 朗读当前可见区域的所有句子
  // ⚠️ 注意：这个函数使用了多个状态和 ref，需要用 useCallback 包装以避免频繁重新创建
  const handleReadAloud = useCallback(async () => {
    console.log('🔍 [ArticleViewer] handleReadAloud useCallback 执行')
    // 🔧 使用 ref 获取最新的 sentences，避免闭包问题
    const currentSentences = sentencesRef.current
    console.log('🔊 [ArticleViewer] handleReadAloud 被调用', {
      isReading,
      supported,
      sentencesCount: currentSentences.length,
      voicesCount: voices?.length || 0
    })

    if (isReadingRef.current) {
      // 停止朗读
      console.log('🔊 [ArticleViewer] 用户主动停止朗读')
      // 标记为用户主动停止
      isUserStoppedRef.current = true
      // 同时使用 react-speech-kit 的 cancel 和原生 API 的 cancel
      cancel()
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel()
      }
      setIsReading(false)
      isReadingRef.current = false
      // 🔧 不重置 currentReadingIndexRef.current，保留当前朗读位置，以便下次继续
      setCurrentReadingToken(null) // 清除当前朗读的 token 高亮
      setCurrentReadingSentenceIndex(null) // 清除当前朗读的句子高亮
      if (readingTimeoutRef.current) {
        clearTimeout(readingTimeoutRef.current)
        readingTimeoutRef.current = null
      }
      // 重置标志（延迟足够时间，确保错误处理能检测到）
      // 错误回调可能是异步的，需要给足够的时间
      setTimeout(() => {
        isUserStoppedRef.current = false
      }, 500)
      return
    }

    if (!supported) {
      console.warn('⚠️ [ArticleViewer] 浏览器不支持语音合成')
      alert('您的浏览器不支持语音合成功能')
      return
    }

    if (currentSentences.length === 0) {
      console.warn('⚠️ [ArticleViewer] 没有可朗读的内容')
      alert(t('没有可朗读的内容'))
      return
    }

    // 确保语音列表已加载
    const voicesLoaded = await ensureVoicesLoaded()
    if (!voicesLoaded) {
      console.warn('⚠️ [ArticleViewer] 语音列表加载失败或超时')
      // 继续尝试，可能某些浏览器不需要等待
    }

    // 🔧 确定起始索引：
    // 1. 如果有选中的句子，从选中句子开始
    // 2. 如果没有选中句子，检查是否有上次朗读位置，如果有则继续，否则从可见第一句开始
    let startIndex
    if (selectedSentenceIndex !== null && selectedSentenceIndex !== undefined) {
      // 从选中的句子开始
      startIndex = selectedSentenceIndex
      console.log('🔊 [ArticleViewer] 从选中的句子开始朗读，起始索引:', startIndex)
    } else if (currentReadingIndexRef.current > 0 && currentReadingIndexRef.current < currentSentences.length) {
      // 从上次朗读位置继续
      startIndex = currentReadingIndexRef.current
      console.log('🔊 [ArticleViewer] 从上次朗读位置继续，起始索引:', startIndex)
    } else {
      // 从当前可见的第一行开始
      startIndex = getFirstVisibleSentenceIndex()
      console.log('🔊 [ArticleViewer] 从可见第一句开始朗读，起始索引:', startIndex)
    }
    currentReadingIndexRef.current = startIndex
    setIsReading(true)
    isReadingRef.current = true
    isUserStoppedRef.current = false // 重置用户停止标志

    // 开始朗读
    const readNextSentence = async () => {
      // 🔧 使用 ref 获取最新的 sentences
      const latestSentences = sentencesRef.current
      console.log('🔊 [ArticleViewer] readNextSentence 被调用', {
        currentIndex: currentReadingIndexRef.current,
        totalSentences: latestSentences.length,
        isReadingState: isReading
      })

      // 检查是否还在朗读状态（用户可能已经停止）
      if (!isReadingRef.current) {
        console.log('🔊 [ArticleViewer] 朗读已停止，退出')
        return
      }

      if (currentReadingIndexRef.current >= latestSentences.length) {
        // 朗读完成
        console.log('🔊 [ArticleViewer] 朗读完成')
        setIsReading(false)
        isReadingRef.current = false
        isUserStoppedRef.current = false // 重置用户停止标志
        currentReadingIndexRef.current = 0
              setCurrentReadingToken(null) // 清除当前朗读的 token 高亮
              setCurrentReadingSentenceIndex(null) // 清除当前朗读的句子高亮
        if (readingTimeoutRef.current) {
          clearTimeout(readingTimeoutRef.current)
          readingTimeoutRef.current = null
        }
        return
      }

      const sentence = latestSentences[currentReadingIndexRef.current]
      const sentenceText = getSentenceText(sentence)
      
      console.log('🔊 [ArticleViewer] 准备朗读句子', {
        index: currentReadingIndexRef.current,
        sentenceText: sentenceText?.substring(0, 100),
        textLength: sentenceText?.length,
        tokensCount: sentence?.tokens?.length || 0
      })
      
      if (!sentenceText || sentenceText.trim().length === 0) {
        // 如果句子为空，跳过
        console.log('🔊 [ArticleViewer] 句子为空，跳过')
        currentReadingIndexRef.current++
        // 使用 setTimeout 避免递归过深
        readingTimeoutRef.current = setTimeout(() => {
          readNextSentence()
        }, 100)
        return
      }

      // 🔧 使用全局语言状态，而不是从数据中推断
      const globalLangCode = languageNameToCode(selectedLanguage)
      const langCode = globalLangCode || 'de' // 默认使用 'de'
      const voice = getVoiceForLanguage(langCode)
      
      console.log('🔊 [ArticleViewer] 准备调用 speak', {
        langCode,
        voice: voice ? voice.name : 'null',
        textLength: sentenceText.length
      })

      // 🔧 检查当前句子是否在可见范围内，如果不在则自动滚动
      const checkAndScrollToSentence = () => {
        if (!scrollContainerRef.current) return
        
        const container = scrollContainerRef.current
        const containerRect = container.getBoundingClientRect()
        const containerTop = containerRect.top
        const containerBottom = containerRect.bottom
        
        const sentenceElement = container.querySelector(
          `[data-sentence-index="${currentReadingIndexRef.current}"]`
        )
        
        if (sentenceElement) {
          const sentenceRect = sentenceElement.getBoundingClientRect()
          const sentenceTop = sentenceRect.top
          const sentenceBottom = sentenceRect.bottom
          
          // 检查句子是否在可见区域内
          const isVisible = sentenceBottom > containerTop && sentenceTop < containerBottom
          
          if (!isVisible) {
            // 如果不在可见区域内，滚动到该句子
            console.log('🔊 [ArticleViewer] 句子不在可见范围内，自动滚动到句子:', currentReadingIndexRef.current)
            sentenceElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
          }
        }
      }
      
      // 延迟一点执行滚动，确保 DOM 已更新
      setTimeout(checkAndScrollToSentence, 100)

      // 朗读当前句子 - 直接使用 Web Speech API
      try {
        console.log('🔊 [ArticleViewer] 调用 speak API', {
          text: sentenceText.substring(0, 50),
          voiceName: voice?.name,
          voiceLang: voice?.lang,
          rate: 0.9,
          pitch: 1.0,
          volume: 1.0
        })
        
        // 检查浏览器是否支持 Web Speech API
        if (typeof window === 'undefined' || !window.speechSynthesis) {
          console.error('❌ [ArticleViewer] 浏览器不支持 Web Speech API')
          alert('您的浏览器不支持语音合成功能')
          setIsReading(false)
          isReadingRef.current = false
          isUserStoppedRef.current = false // 重置用户停止标志
              setCurrentReadingToken(null) // 清除当前朗读的 token 高亮
              setCurrentReadingSentenceIndex(null) // 清除当前朗读的句子高亮
          return
        }

        // 等待一小段时间，确保之前的操作完成
        await new Promise(resolve => setTimeout(resolve, 100))

        // 🔧 检查是否有正在进行的朗读，只在有正在进行的朗读时才取消
        // 避免取消当前正要开始的朗读
        if (window.speechSynthesis.speaking) {
          console.log('🔊 [ArticleViewer] 检测到正在进行的朗读，取消它')
          window.speechSynthesis.cancel()
          // 再等待一小段时间，确保 cancel 完成
          await new Promise(resolve => setTimeout(resolve, 100))
        }

        // 确保语音列表已加载（某些浏览器需要触发 getVoices 才能加载）
        let availableVoices = window.speechSynthesis.getVoices()
        if (availableVoices.length === 0) {
          // 如果语音列表为空，等待一下再试
          await new Promise(resolve => setTimeout(resolve, 100))
          availableVoices = window.speechSynthesis.getVoices()
        }

        // 重新验证并获取语音对象（确保使用最新的语音列表）
        let validVoice = null
        if (voice) {
          // 从当前可用的语音列表中查找匹配的语音
          validVoice = availableVoices.find(v => 
            v.name === voice.name && v.lang === voice.lang
          ) || availableVoices.find(v => v.lang === voice.lang)
        }
        
        // 如果找不到匹配的语音，重新获取
        if (!validVoice) {
          validVoice = getVoiceForLanguage(langCode)
        }

        // 🔧 计算字符位置到 token 索引的映射
        const sentenceIndex = currentReadingIndexRef.current
        
        // 直接使用 Web Speech API
        const utterance = new SpeechSynthesisUtterance(sentenceText)
        
        // 🔧 为每个 utterance 创建唯一标识，避免旧的 utterance 事件影响新的朗读
        const utteranceId = `${sentenceIndex}-${Date.now()}-${Math.random()}`
        utterance._utteranceId = utteranceId
        
        // 只有在找到有效语音时才设置
        if (validVoice) {
          utterance.voice = validVoice
          console.log('🔊 [ArticleViewer] 使用语音:', validVoice.name, validVoice.lang)
        } else {
          console.warn('⚠️ [ArticleViewer] 未找到有效语音，使用浏览器默认语音')
        }
        
        utterance.rate = 0.9
        utterance.pitch = 1.0
        utterance.volume = 1.0
        // 🔧 使用全局语言状态转换为 BCP 47 标签
        utterance.lang = languageCodeToBCP47(langCode) || 'de-DE'
        
        let hasStarted = false
        let hasEnded = false
        const currentUtteranceIdRef = { current: utteranceId } // 使用 ref 来跟踪当前 utterance ID
        const tokens = sentence.tokens || []
        let charToTokenMap = []
        let currentCharIndex = 0
        
        // 🔧 使用与 getSentenceText 相同的方式构建文本，确保字符映射准确
        // 构建字符到 token 的映射
        tokens.forEach((token, tokenIndex) => {
          // 使用与 getSentenceText 相同的逻辑获取 token 文本
          let tokenText = ''
          if (typeof token === 'string') {
            tokenText = token
          } else if (token?.token_body) {
            tokenText = token.token_body
          }
          
          // 只处理非空 token
          if (tokenText.trim().length > 0) {
            const tokenLength = tokenText.length
            
            // 为这个 token 的每个字符记录 token 索引
            for (let i = 0; i < tokenLength; i++) {
              charToTokenMap[currentCharIndex + i] = tokenIndex
            }
            currentCharIndex += tokenLength
          }
        })
        
        utterance.onstart = () => {
          // 🔧 只处理当前 utterance 的开始事件
          if (utterance._utteranceId !== currentUtteranceIdRef.current) {
            console.log('🔊 [ArticleViewer] 忽略旧的 utterance 开始事件:', utterance._utteranceId, '当前:', currentUtteranceIdRef.current)
            return
          }
          hasStarted = true
          // 设置当前正在朗读的句子索引
          setCurrentReadingSentenceIndex(sentenceIndex)
          console.log('🔊 [ArticleViewer] onStart 回调被触发，开始朗读', {
            utteranceId: utterance._utteranceId,
            sentenceIndex
          })
        }
        
        // 🔧 监听 boundary 事件，跟踪当前朗读到的字符位置
        utterance.onboundary = (event) => {
          // 🔧 只处理当前 utterance 的 boundary 事件
          if (utterance._utteranceId !== currentUtteranceIdRef.current) {
            return
          }
          
          // 只处理 word 类型的 boundary 事件（单词边界）
          // 注意：不要在这里做任何可能影响朗读流程的操作
          if (event.name === 'word' && isReadingRef.current && !hasEnded) {
            try {
              const charIndex = event.charIndex
              
              // 查找字符索引对应的 token
              // 如果找不到精确匹配，查找最接近的 token
              let tokenIndex = charToTokenMap[charIndex]
              
              // 如果当前字符索引没有映射，向前查找最近的 token
              if (tokenIndex === undefined && charIndex > 0) {
                for (let i = charIndex - 1; i >= 0; i--) {
                  if (charToTokenMap[i] !== undefined) {
                    tokenIndex = charToTokenMap[i]
                    break
                  }
                }
              }
              
              if (tokenIndex !== undefined) {
                // 使用 setTimeout 确保状态更新不会阻塞朗读流程
                setTimeout(() => {
                  if (isReadingRef.current && !hasEnded && utterance._utteranceId === currentUtteranceIdRef.current) {
                    setCurrentReadingToken({
                      sentenceIndex,
                      tokenIndex
                    })
                  }
                }, 0)
              }
            } catch (err) {
              // 静默处理错误，避免影响朗读
              console.warn('⚠️ [ArticleViewer] onboundary 处理错误:', err)
            }
          }
        }
        
        utterance.onend = () => {
          // 🔧 只处理当前 utterance 的结束事件，忽略旧的 utterance 的结束事件
          if (utterance._utteranceId !== currentUtteranceIdRef.current) {
            console.log('🔊 [ArticleViewer] 忽略旧的 utterance 结束事件:', utterance._utteranceId, '当前:', currentUtteranceIdRef.current)
            return
          }
          
          if (hasEnded) {
            console.warn('⚠️ [ArticleViewer] onEnd 被多次调用')
            return
          }
          hasEnded = true
          console.log('🔊 [ArticleViewer] onEnd 回调被触发，句子朗读完成', {
            sentenceIndex,
            sentenceText: sentenceText.substring(0, 50),
            isReading: isReadingRef.current
          })
          // 清除当前朗读的 token 高亮和句子高亮
          setCurrentReadingToken(null)
          setCurrentReadingSentenceIndex(null)
          // 当前句子朗读完成后，继续下一句
          if (isReadingRef.current) {
            currentReadingIndexRef.current++
            readingTimeoutRef.current = setTimeout(() => {
              readNextSentence()
            }, 500) // 句子之间间隔 500ms，给用户时间理解
          }
        }
        
        utterance.onerror = (event) => {
          // 🔧 只处理当前 utterance 的错误，忽略旧的 utterance 的错误
          if (utterance._utteranceId !== currentUtteranceIdRef.current) {
            console.log('🔊 [ArticleViewer] 忽略旧的 utterance 错误:', utterance._utteranceId, '当前:', currentUtteranceIdRef.current)
            return
          }
          
          console.log('🔊 [ArticleViewer] onError 被触发:', {
            error: event.error,
            utteranceId: utterance._utteranceId,
            hasStarted,
            isReading: isReadingRef.current,
            isUserStopped: isUserStoppedRef.current
          })
          
          // 处理 'interrupted' 错误 - 这通常不是严重错误
          if (event.error === 'interrupted') {
            // 如果是用户主动停止，不记录错误
            if (isUserStoppedRef.current || !isReadingRef.current) {
              console.log('🔊 [ArticleViewer] 用户主动停止，忽略 interrupted 错误')
              return
            }
            
            // 🔧 interrupted 错误通常是因为调用了 cancel()，这是正常的操作
            // 但是，如果当前 utterance 刚刚开始就被中断，可能是被新的 utterance 取消了
            // 在这种情况下，我们应该等待新的 utterance 开始，而不是继续下一句
            if (hasStarted) {
              console.log('🔊 [ArticleViewer] 朗读被中断（已开始），可能是被新的朗读取消，不继续下一句')
            } else {
              console.log('🔊 [ArticleViewer] 朗读被中断（未开始），可能是被新的朗读取消，不继续下一句')
            }
          // 清除当前朗读的 token 高亮和句子高亮
          setCurrentReadingToken(null)
          setCurrentReadingSentenceIndex(null)
            return
          }
          
          // 记录其他类型的错误
          console.error('❌ [ArticleViewer] onError 回调被触发，朗读错误:', {
            error: event.error,
            type: event.type,
            charIndex: event.charIndex,
            charLength: event.charLength
          })
          
          // 如果是 'synthesis-failed' 错误，尝试继续下一句（可能是语音不可用）
          if (event.error === 'synthesis-failed') {
            console.warn('⚠️ [ArticleViewer] 语音合成失败，跳过当前句子，继续下一句')
            if (isReadingRef.current) {
              currentReadingIndexRef.current++
              readingTimeoutRef.current = setTimeout(() => {
                readNextSentence()
              }, 500)
            }
            return
          }
          
          // 其他错误才停止朗读
          console.error('❌ [ArticleViewer] 严重错误，停止朗读:', event.error)
          setIsReading(false)
          isReadingRef.current = false
          isUserStoppedRef.current = false // 重置用户停止标志
          currentReadingIndexRef.current = 0
              setCurrentReadingToken(null) // 清除当前朗读的 token 高亮
              setCurrentReadingSentenceIndex(null) // 清除当前朗读的句子高亮
          if (readingTimeoutRef.current) {
            clearTimeout(readingTimeoutRef.current)
            readingTimeoutRef.current = null
          }
        }
        
        // 开始朗读
        console.log('🔊 [ArticleViewer] 调用 window.speechSynthesis.speak')
        window.speechSynthesis.speak(utterance)
        console.log('🔊 [ArticleViewer] speak 调用完成')
        
      } catch (err) {
        console.error('❌ [ArticleViewer] 调用 speak 失败:', err)
        setIsReading(false)
        isReadingRef.current = false
        isUserStoppedRef.current = false // 重置用户停止标志
        currentReadingIndexRef.current = 0
              setCurrentReadingToken(null) // 清除当前朗读的 token 高亮
              setCurrentReadingSentenceIndex(null) // 清除当前朗读的句子高亮
        if (readingTimeoutRef.current) {
          clearTimeout(readingTimeoutRef.current)
          readingTimeoutRef.current = null
        }
      }
    }

    // 使用 setTimeout 确保状态更新后再开始朗读
    setTimeout(() => {
      readNextSentence()
    }, 100)
  }, [
    supported,
    voices?.length || 0,
    selectedLanguage,
    selectedSentenceIndex,
    setIsReading,
    setCurrentReadingToken,
    setCurrentReadingSentenceIndex
  ])
  // 注意：ref 不需要放在依赖数组中，因为它们不会变化
  // 注意：sentences 通过 sentencesRef 访问，不需要放在依赖数组中
  
  // 🔧 使用 useCallback 包装 handleReadAloud，避免在 useMemo 中频繁变化
  const handleReadAloudClick = useCallback((e) => {
    e.stopPropagation() // 阻止事件冒泡，避免触发背景点击
    console.log('🔊 [ArticleViewer] 朗读按钮被点击')
    handleReadAloud()
  }, [handleReadAloud])
  
  // 🔧 构建朗读按钮 - 使用 useMemo 缓存，避免不必要的重新创建
  const readAloudButton = useMemo(() => {
    console.log('🔍 [ArticleViewer] readAloudButton useMemo 执行')
    if (!readAloudButtonContainer) return null
    
    return (
      <button
        onClick={handleReadAloudClick}
        className="flex items-center gap-2 px-4 py-2 text-white rounded-lg shadow-md transition-colors"
        style={{ 
          backgroundColor: isReading ? '#14b8a6' : '#2dd4bf', // teal-500 when reading, teal-400 otherwise
        }}
        onMouseEnter={(e) => {
          if (!isReading) {
            e.currentTarget.style.backgroundColor = '#14b8a6' // teal-500 on hover
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = isReading ? '#14b8a6' : '#2dd4bf'
        }}
        title={isReading ? t('停止朗读') : t('朗读')}
      >
        {/* 播放/停止图标 - 白色轮廓 */}
        {isReading ? (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
            <rect x="9" y="9" width="6" height="6" rx="1" />
            <circle cx="12" cy="12" r="10" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
        <span className="text-sm font-medium">{isReading ? t('停止朗读') : t('朗读')}</span>
      </button>
    )
  }, [readAloudButtonContainer, isReading, handleReadAloudClick, t])

  // 🔧 使用 useMemo 缓存 Portal，避免不必要的重新创建
  const readAloudButtonPortal = useMemo(() => {
    console.log('🔍 [ArticleViewer] readAloudButtonPortal useMemo 执行:', {
      hasReadAloudButtonContainer: !!readAloudButtonContainer,
      hasReadAloudButton: !!readAloudButton
    })
    if (!readAloudButtonContainer || !readAloudButton) return null
    try {
      const portal = createPortal(readAloudButton, readAloudButtonContainer)
      console.log('✅ [ArticleViewer] Portal 创建成功')
      return portal
    } catch (err) {
      console.error('❌ [ArticleViewer] Portal 创建失败:', err)
      return null
    }
  }, [readAloudButtonContainer, readAloudButton])

  // ============================================================================
  // 🔧 Early Return（必须在所有 hooks 之后）
  // ============================================================================
  
  // 🔧 调试：检查所有可能的提前返回条件
  console.log('🔍 [ArticleViewer] 检查渲染条件:', {
    isLoading,
    isError,
    hasData: !!data,
    error: error?.message || error,
    sentencesLength: sentences.length
  })

  if (isLoading) {
    console.log('⏸️ [ArticleViewer] 提前返回：isLoading = true')
    return (
      <div className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto min-h-0 relative overflow-visible">
        <div className="text-gray-500">Loading article...</div>
      </div>
    )
  }

  if (isError) {
    console.log('❌ [ArticleViewer] 提前返回：isError = true', error)
    return (
      <div className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto min-h-0 relative overflow-visible">
        <div className="text-red-500">Failed to load: {String(error?.message || error)}</div>
      </div>
    )
  }

  // 🔧 如果没有数据且不在加载中，返回空状态（避免渲染错误）
  if (!data && !isLoading) {
    console.log('⚠️ [ArticleViewer] 提前返回：没有数据')
    return (
      <div className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto min-h-0 relative overflow-visible">
        <div className="text-gray-500">No article data available</div>
      </div>
    )
  }

  // 🔧 调试：在返回前检查状态
  console.log('🔍 [ArticleViewer] 准备渲染，当前状态:', {
    isLoading,
    isError,
    hasData: !!data,
    sentencesLength: sentences.length,
    sentencesIsArray: Array.isArray(sentences),
    willRenderSentences: sentences.length > 0
  })
  
  // 🔧 错误边界：捕获渲染错误
  try {
    return (
    <div className="flex-1 bg-white rounded-lg border border-gray-200 relative min-h-0 overflow-visible">
      {/* 🔧 使用 Portal 将朗读按钮渲染到父组件的容器中 */}
      {readAloudButtonPortal}
      
      {/* 🔧 滚动容器 */}
      <div
        ref={scrollContainerRef}
        className="flex-1 p-4 overflow-auto min-h-0 h-full article-scrollbar"
        onClick={handleBackgroundClick}
      >
      <style>{`
        @keyframes sentenceFlash {
          0%, 100% { background: linear-gradient(90deg, rgba(229, 231, 235, 0.3), rgba(209, 213, 219, 0.3)); }
          50% { background: linear-gradient(90deg, rgba(229, 231, 235, 0.6), rgba(209, 213, 219, 0.6)); }
        }
        .sentence-flashing {
          animation: sentenceFlash 1s ease-in-out infinite;
        }
        .article-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .article-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .article-scrollbar::-webkit-scrollbar-thumb {
          background: #d1d5db;
          border-radius: 4px;
        }
        .article-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #9ca3af;
        }
      `}</style>
      <div className="space-y-[0.66rem] leading-[1.33] text-gray-900">
        {(() => {
          console.log('🔍 [ArticleViewer] 渲染时检查 sentences:', {
            sentencesLength: sentences.length,
            sentencesIsArray: Array.isArray(sentences),
            firstSentence: sentences[0] ? {
              sentence_id: sentences[0].sentence_id,
              hasTokens: !!sentences[0].tokens,
              tokensType: typeof sentences[0].tokens,
              tokensIsArray: Array.isArray(sentences[0].tokens)
            } : null
          })
          return null
        })()}
        {sentences.length === 0 && (
          <div className="text-gray-500 p-4">
            ⚠️ 没有句子数据。调试信息：
            <pre className="text-xs mt-2 bg-gray-100 p-2 rounded">
              {JSON.stringify({
                hasData: !!data,
                dataKeys: data ? Object.keys(data) : [],
                hasDataData: !!data?.data,
                dataDataKeys: data?.data ? Object.keys(data.data) : [],
                rawSentencesType: typeof rawSentences,
                rawSentencesIsArray: Array.isArray(rawSentences),
                rawSentencesLength: Array.isArray(rawSentences) ? rawSentences.length : 'N/A',
                sentencesLength: sentences.length,
                sentencesIsArray: Array.isArray(sentences),
                isLoading,
                isError,
                error: error?.message || error
              }, null, 2)}
            </pre>
          </div>
        )}
        {sentences.length > 0 && (
          <div className="text-xs text-gray-400 mb-2">
            ✅ 已加载 {sentences.length} 个句子
          </div>
        )}
        {sentences.map((sentence, sIdx) => {
          const sentenceId = sentence.sentence_id || (typeof sentence === 'object' && sentence.id)
          const isFlashing = flashingSentenceId === sentenceId
          
          return (
            <React.Fragment key={`s-${sIdx}`}>
              <SentenceContainer
                key={`s-${sIdx}`}
                sentence={sentence}
                sentenceIndex={sIdx}
              articleId={articleId}
              selectedTokenIds={selectedTokenIds}
              activeSentenceIndex={activeSentenceIndex}
              hasExplanation={hasExplanation}
              getExplanation={getExplanation}
              hoveredTokenId={hoveredTokenId}
              setHoveredTokenId={setHoveredTokenId}
              highlightedRange={highlightedRange}
              handleGetExplanation={handleGetExplanation}
              addSingle={addSingle}
              isTokenAsked={isTokenAsked}
              markAsAsked={markAsAsked}
              getNotationContent={getNotationContent}
              setNotationContent={setNotationContent}
              onSentenceMouseEnter={handleSentenceMouseEnter}
              onSentenceMouseLeave={handleSentenceMouseLeave}
              onSentenceClick={(idx) => {
                console.log('🔘 [ArticleViewer] onSentenceClick 被调用', { idx })
                // 句子选择与 token 选择互斥：清空 token 选择，但保留句子选择
                clearSelection({ skipSentence: true })

                // 🔧 直接调用 handleSentenceClick（用于交互状态）
                if (typeof handleSentenceClick === 'function') {
                  handleSentenceClick(idx)
                }

                // 🔧 关键修复：直接触发 onSentenceSelect，避免依赖 selectedSentenceIndex 更新
                if (onSentenceSelect && sentences && sentences[idx]) {
                  const s = sentences[idx]
                  const sentenceText = s.tokens?.map(token =>
                    typeof token === 'string' ? token : token.token_body
                  ).join(' ') || ''
                  console.log('✅ [ArticleViewer] 直接调用 onSentenceSelect', { idx, sentenceText, sentence: s })
                  onSentenceSelect(idx, sentenceText, s)
                } else {
                  console.warn('⚠️ [ArticleViewer] 无法调用 onSentenceSelect', {
                    hasOnSentenceSelect: !!onSentenceSelect,
                    hasSentences: !!sentences,
                    idx,
                    sentenceExists: !!(sentences && sentences[idx])
                  })
                }
              }}
              getSentenceBackgroundStyle={(idx) => {
                const baseStyle = getSentenceBackgroundStyle(idx)
                // 🔧 如果当前句子正在被朗读，添加 success-50 背景色
                const isCurrentlyReading = currentReadingSentenceIndex === idx
                const readingStyle = isCurrentlyReading ? 'bg-green-50' : ''
                const flashingStyle = isFlashing ? 'sentence-flashing' : ''
                return `${baseStyle} ${readingStyle} ${flashingStyle}`.trim()
              }}
              isSentenceInteracting={isSentenceInteracting}
              currentReadingToken={currentReadingToken}
              onAskAI={onAskAI}
              isTokenInsufficient={isTokenInsufficient}
              autoTranslationEnabled={autoTranslationEnabled}
            />
            </React.Fragment>
          )
        })}
      </div>
      </div>
    </div>
    )
  } catch (err) {
    console.error('❌ [ArticleViewer] 渲染错误:', err)
    console.error('❌ [ArticleViewer] 错误堆栈:', err.stack)
    return (
      <div className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto min-h-0 relative overflow-visible">
        <div className="text-red-500">
          <div className="font-semibold mb-2">渲染出错</div>
          <div className="text-sm">{String(err.message || err)}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            刷新页面
          </button>
        </div>
      </div>
    )
  }
}

// 🔧 临时移除 React.memo，调试渲染问题
// TODO: 修复后重新启用 memo 优化
export default ArticleViewer
// export default memo(ArticleViewer, (prevProps, nextProps) => {
//   // 自定义比较函数：只在相关 props 变化时重新渲染
//   // 🔧 如果 articleId 变化，必须重新渲染
//   if (prevProps.articleId !== nextProps.articleId) {
//     console.log('🔄 [ArticleViewer] memo: articleId 变化，需要重新渲染', { prev: prevProps.articleId, next: nextProps.articleId })
//     return false
//   }
//   
//   // 🔧 其他 props 比较
//   const propsEqual = (
//     prevProps.autoTranslationEnabled === nextProps.autoTranslationEnabled &&
//     prevProps.isTokenInsufficient === nextProps.isTokenInsufficient &&
//     prevProps.targetSentenceId === nextProps.targetSentenceId &&
//     prevProps.onTokenSelect === nextProps.onTokenSelect &&
//     prevProps.isTokenAsked === nextProps.isTokenAsked &&
//     prevProps.markAsAsked === nextProps.markAsAsked &&
//     prevProps.getNotationContent === nextProps.getNotationContent &&
//     prevProps.setNotationContent === nextProps.setNotationContent &&
//     prevProps.onSentenceSelect === nextProps.onSentenceSelect &&
//     prevProps.onTargetSentenceScrolled === nextProps.onTargetSentenceScrolled &&
//     prevProps.onAskAI === nextProps.onAskAI
//   )
//   
//   if (!propsEqual) {
//     console.log('🔄 [ArticleViewer] memo: props 变化，需要重新渲染')
//     return false
//   }
//   
//   // 🔧 props 相同，不重新渲染（但内部状态变化仍会触发重新渲染）
//   return true
// })

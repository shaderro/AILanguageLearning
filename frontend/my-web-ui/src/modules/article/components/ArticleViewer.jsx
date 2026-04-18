/* @refresh reset */
import React, { useMemo, useEffect, useRef, useState, useCallback, useLayoutEffect } from 'react'
import { createPortal } from 'react-dom'
import { useQuery } from '@tanstack/react-query'
import { useTokenSelection } from '../hooks/useTokenSelection'
import { useTokenDrag } from '../hooks/useTokenDrag'
import { useVocabExplanations } from '../hooks/useVocabExplanations'
import { useSentenceInteraction } from '../hooks/useSentenceInteraction'
import { useUser } from '../../../contexts/UserContext'
import { useUIText } from '../../../i18n/useUIText'
import { useSelection } from '../selection/hooks/useSelection'
import { useLanguage, languageNameToCode, languageCodeToBCP47 } from '../../../contexts/LanguageContext'
import { useArticleTts } from '../hooks/useArticleTts'
import { useTranslationDebug } from '../../../contexts/TranslationDebugContext'
import { apiService } from '../../../services/api'
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
  autoTranslationEnabled = false,  // 🔧 自动翻译开关状态
  pageIndex = 1,
  onPageChange = null,
  autoHintTarget = null,
  autoHintPreviewing = false,
  autoHintTooltipVisible = false,
  autoHintFading = false,
  autoHintMessage = '',
  onAutoHintInteraction = null,
}) {
  // 🔧 Debug: detect unexpected remounts (selection state loss)
  useEffect(() => {
    console.log('🧩 [ArticleViewer] mounted', { articleId })
    return () => {
      console.log('🧩 [ArticleViewer] unmounted', { articleId })
    }
  }, [articleId])

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
  const fallbackTotalPages = useMemo(() => {
    if (!articleId || articleId === 'upload') return 1
    try {
      const raw =
        localStorage.getItem(`article_segment_job_${articleId}`) ||
        sessionStorage.getItem(`article_segment_job_${articleId}`)
      if (!raw) return 1
      const job = JSON.parse(raw)
      const total = Number(job?.totalPages || 1)
      return Number.isFinite(total) && total > 0 ? total : 1
    } catch {
      return 1
    }
  }, [articleId])
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['article-page', articleId, pageIndex, stableUserId],
    queryFn: async () => {
      try {
        return await apiService.getArticlePage(articleId, pageIndex)
      } catch (e) {
        // 分页任务未就绪时，兜底为 processing 页面，避免“无按钮可翻页”
        if (pageIndex > 1) {
          return {
            success: true,
            data: {
              text_id: articleId,
              page_index: pageIndex,
              total_pages: fallbackTotalPages,
              page_status: 'processing',
              sentences: [],
            },
          }
        }
        throw e
      }
    },
    enabled: !!articleId && articleId !== 'upload',
    staleTime: 10 * 1000,
  })
  
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
    if (['ja', 'japanese', '日语', '日本語', '日文'].includes(lower)) return 'ja'
    if (lower.length === 2) return lower
    return null
  }

  const rawSentences = data?.data?.sentences
  const pageStatus = data?.data?.page_status || 'completed'
  const totalPages = Math.max(data?.data?.total_pages || 1, fallbackTotalPages)
  const isPageProcessing = pageStatus !== 'completed'
  const segmentProgress = useMemo(() => {
    if (!articleId || articleId === 'upload') return null
    const defaultProgress = {
      completed: Math.min(Math.max(Number(pageIndex) || 1, 1), Math.max(totalPages, 1)),
      total: Math.max(totalPages, 1),
      running: false,
    }
    try {
      const raw = localStorage.getItem(`article_segment_job_${articleId}`)
      const running = localStorage.getItem(`article_segment_running_${articleId}`) === '1'
      if (!raw) return { ...defaultProgress, running }
      const job = JSON.parse(raw)
      const total = Math.max(Number(job?.totalPages || defaultProgress.total), 1)
      const completed = Math.min(Math.max(Number(job?.completedPages || 1), 1), total)
      return { completed, total, running }
    } catch {
      return defaultProgress
    }
  }, [articleId, pageIndex, totalPages])
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
    hoveredSentenceIndex: _hoveredSentenceIndex,
    clickedSentenceIndex: _clickedSentenceIndex,
    selectedSentenceIndex,
    sentenceRefs: _sentenceRefs,
    handleSentenceMouseEnter,
    handleSentenceMouseLeave,
    handleSentenceClick: originalHandleSentenceClick,
    clearSentenceInteraction: _clearSentenceInteraction,
    clearSentenceSelection,
    getSentenceBackgroundStyle,
    isSentenceInteracting,
    isSentenceSelected: _isSentenceSelected
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
  const {
    currentSelection,
    clearSelection: _clearSelectionContext,
    selectTokens: selectTokensInContext,
  } = useSelection()

  const selectedSentenceIndexFromSelectionContext = useMemo(() => {
    if (!currentSelection || currentSelection.type !== 'sentence') return null
    const sid = currentSelection.sentenceId
    if (sid === null || sid === undefined) return null
    const idx = sentences.findIndex(s => (s?.sentence_id ?? s?.id) === sid)
    return idx >= 0 ? idx : null
  }, [currentSelection, sentences])

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
    emitSelection: _emitSelection
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
  
  // 🔧 使用 ref 存储最新的 sentences，避免在 useCallback 依赖中导致频繁重新创建
  const sentencesRef = useRef(sentences)
  useEffect(() => {
    sentencesRef.current = sentences
  }, [sentences])
  
  // 🔧 朗读按钮容器 state - 必须在早期返回之前调用
  const [readAloudButtonContainer, setReadAloudButtonContainer] = useState(null)
  const containerRef = useRef(null) // 使用 ref 来保持容器引用，避免重新查找
  
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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount-only discovery; container sync is in the next effect
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
  // 注意：朗读重构完成后会由 useArticleTts 使用；当前使用 sentencesRef.current 避免闭包陈旧
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

  const {
    ttsPhase,
    ttsUiReading,
    speechSupported,
    handleReadAloud,
    currentReadingToken,
    currentReadingSentenceIndex,
  } = useArticleTts({
    sentences,
    sentencesRef,
    selectedLanguage,
    languageNameToCode,
    languageCodeToBCP47,
    getSentenceText,
    scrollContainerRef,
    getFirstVisibleSentenceIndex,
    selectedSentenceIndex,
    selectedSentenceIndexFromSelectionContext,
    currentSelection,
    activeSentenceIndex,
    selectedTokenIds,
    t,
  })

  
  // 🔧 使用 useCallback 包装 handleReadAloud，避免在 useMemo 中频繁变化
  const handleReadAloudClick = useCallback((e) => {
    e.stopPropagation() // 阻止事件冒泡，避免触发背景点击
    const latestSentences = sentencesRef.current || []
    const idx =
      selectedSentenceIndexFromSelectionContext !== null && selectedSentenceIndexFromSelectionContext !== undefined
        ? selectedSentenceIndexFromSelectionContext
        : selectedSentenceIndex
    const selected = typeof idx === 'number' && idx >= 0 && idx < latestSentences.length ? latestSentences[idx] : null
    const selectedText = selected ? getSentenceText(selected) : null
    console.log('[TTS] read_button_clicked', {
      selectedSentenceIndex,
      selectedSentenceIndexFromSelectionContext,
      currentSelection,
      selectedSentenceId: selected?.sentence_id ?? selected?.id ?? null,
      selectedSentencePreview: selectedText ? String(selectedText).slice(0, 120) : null,
      fallbackFirstSentencePreview: latestSentences[0] ? String(getSentenceText(latestSentences[0]) || '').slice(0, 120) : null,
      ttsUiReading,
      ttsPhase,
    })
    handleReadAloud()
  }, [handleReadAloud, currentSelection, selectedSentenceIndex, selectedSentenceIndexFromSelectionContext, ttsUiReading, ttsPhase])

  const hasTtsSelection =
    Boolean(currentSelection?.sentenceId !== null && currentSelection?.sentenceId !== undefined) ||
    (typeof selectedSentenceIndexFromSelectionContext === 'number' && selectedSentenceIndexFromSelectionContext >= 0) ||
    (typeof selectedSentenceIndex === 'number' && selectedSentenceIndex >= 0) ||
    (Array.isArray(selectedTokenIds) && selectedTokenIds.length > 0 && typeof activeSentenceIndex === 'number' && activeSentenceIndex >= 0)
  const canClickReadAloud = ttsUiReading || hasTtsSelection
  
  // 🔧 构建朗读按钮（避免在该区域继续增加 hook，降低 hooks 顺序问题风险）
  const readAloudButton = !readAloudButtonContainer
    ? null
    : (
      <button
        type="button"
        disabled={!speechSupported || !canClickReadAloud}
        onClick={handleReadAloudClick}
        className="flex items-center gap-2 px-4 py-2 text-white rounded-lg shadow-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        style={{
          backgroundColor: ttsUiReading ? '#14b8a6' : '#2dd4bf', // teal-500 when reading, teal-400 otherwise
        }}
        onMouseEnter={(e) => {
          if (!ttsUiReading && speechSupported && canClickReadAloud) {
            e.currentTarget.style.backgroundColor = '#14b8a6' // teal-500 on hover
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = ttsUiReading ? '#14b8a6' : '#2dd4bf'
        }}
        title={
          !speechSupported
            ? t('浏览器不支持朗读')
            : !canClickReadAloud
              ? t('请先选择要朗读的句子')
            : ttsUiReading
              ? t('停止朗读')
              : t('朗读')
        }
      >
        {ttsUiReading ? (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
            <rect x="9" y="9" width="6" height="6" rx="1" />
            <circle cx="12" cy="12" r="10" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
        <span className="text-sm font-medium">{ttsUiReading ? t('停止朗读') : t('朗读')}</span>
      </button>
    )

  let readAloudButtonPortal = null
  if (readAloudButtonContainer && readAloudButton) {
    try {
      readAloudButtonPortal = createPortal(readAloudButton, readAloudButtonContainer)
    } catch (err) {
      console.error('❌ [ArticleViewer] Portal 创建失败:', err)
    }
  }

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

  const showLoadingState = isLoading && !data
  const showErrorState = isError
  const showEmptyState = !data && !isLoading && !isError
  const showPagination = totalPages > 1 || pageIndex > 1 || fallbackTotalPages > 1

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
        {showLoadingState ? (
          <div className="text-gray-500 text-base text-center py-12">
            {t('Loading article...')}
          </div>
        ) : showErrorState ? (
          <div className="text-red-500 text-base text-center py-12">
            {t('加载失败')}: {String(error?.message || error)}
          </div>
        ) : showEmptyState ? (
          <div className="text-gray-500 text-base text-center py-12">
            {t('No article data available')}
          </div>
        ) : isPageProcessing ? (
          <div className="text-gray-400 text-base text-center py-12">
            {t('articleSegmentPreprocessing')}
          </div>
        ) : sentences.length === 0 && (
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
        {!isPageProcessing && sentences.map((sentence, sIdx) => {
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
                const readingStyle = isCurrentlyReading ? '!bg-green-100 ring-1 ring-green-300' : ''
                const flashingStyle = isFlashing ? 'sentence-flashing' : ''
                return `${baseStyle} ${readingStyle} ${flashingStyle}`.trim()
              }}
              isSentenceInteracting={isSentenceInteracting}
              currentReadingToken={currentReadingToken}
              onAskAI={onAskAI}
              isTokenInsufficient={isTokenInsufficient}
              autoTranslationEnabled={autoTranslationEnabled}
              autoHintTarget={autoHintTarget}
              autoHintPreviewing={autoHintPreviewing}
              autoHintTooltipVisible={autoHintTooltipVisible}
              autoHintFading={autoHintFading}
              autoHintMessage={autoHintMessage}
              onAutoHintInteraction={onAutoHintInteraction}
            />
            </React.Fragment>
          )
        })}

        {showPagination && (
          <div className="mt-6 space-y-3">
            <div className="flex items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => onPageChange && onPageChange(Math.max(1, pageIndex - 1))}
              disabled={pageIndex <= 1 || !onPageChange}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {t('articlePrevPage')}
            </button>
            <span className="text-sm text-gray-500">
              {t('articlePageLabel').replace('{page}', String(pageIndex)).replace('{total}', String(totalPages))}
            </span>
            <button
              type="button"
              onClick={() => onPageChange && onPageChange(Math.min(totalPages, pageIndex + 1))}
              disabled={pageIndex >= totalPages || !onPageChange}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {t('articleNextPage')}
            </button>
            </div>
          </div>
        )}

        {/* 🔧 Bottom spacer: allow scrolling past last sentence for comfort */}
        <div aria-hidden="true" style={{ height: '35vh' }} />
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
          <div className="font-semibold mb-2">{t('页面渲染出错')}</div>
          <div className="text-sm">{String(err.message || err)}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {t('刷新页面')}
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

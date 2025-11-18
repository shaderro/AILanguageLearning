import { useMemo, useEffect, useRef, useState } from 'react'
import { useArticle } from '../../../hooks/useApi'
import { useTokenSelection } from '../hooks/useTokenSelection'
import { useTokenDrag } from '../hooks/useTokenDrag'
import { useVocabExplanations } from '../hooks/useVocabExplanations'
import { useSentenceInteraction } from '../hooks/useSentenceInteraction'
import { useUser } from '../../../contexts/UserContext'
import { useSelection } from '../selection/hooks/useSelection'
import SentenceContainer from './SentenceContainer'

/**
 * ArticleViewer - Main component for displaying and interacting with article content
 * 
 * 注意：Grammar 和 Vocab notation 相关的功能现在通过 NotationContext 提供，
 * 不再需要通过 props 传递
 */
export default function ArticleViewer({ 
  articleId, 
  onTokenSelect, 
  isTokenAsked, 
  markAsAsked,
  getNotationContent,
  setNotationContent,
  onSentenceSelect,
  targetSentenceId = null,  // 🔧 目标句子ID（用于自动滚动和高亮）
  onTargetSentenceScrolled = null  // 🔧 滚动完成后的回调
}) {
  // Debug logging removed to improve performance
  const { userId } = useUser()
  const { data, isLoading, isError, error } = useArticle(articleId, userId)

  // Asked tokens management - 现在从props接收，不再创建新的hook实例
  // const { askedTokenKeys, isTokenAsked, markAsAsked } = useAskedTokens(articleId)

  const sentences = useMemo(() => {
    console.log('🔍 [ArticleViewer] Processing data:', data)
    console.log('🔍 [ArticleViewer] data.data:', data?.data)
    const raw = data?.data?.sentences
    console.log('🔍 [ArticleViewer] sentences:', raw, 'isArray:', Array.isArray(raw))
    if (Array.isArray(raw) && raw.length > 0) {
      console.log('🔍 [ArticleViewer] First sentence:', raw[0])
      console.log('🔍 [ArticleViewer] First sentence has tokens?', raw[0]?.tokens, 'length:', raw[0]?.tokens?.length)
    }
    return Array.isArray(raw) ? raw : []
  }, [data])

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
    handleSentenceClick,
    clearSentenceInteraction,
    clearSentenceSelection,
    getSentenceBackgroundStyle,
    isSentenceInteracting,
    isSentenceSelected
  } = useSentenceInteraction()

  // Selection context (new system) - need to sync with old token selection system
  const { clearSelection: clearSelectionContext, selectTokens: selectTokensInContext } = useSelection()

  // Token selection management
  const {
    selectedTokenIds,
    activeSentenceIndex,
    activeSentenceRef,
    clearSelection,
    addSingle,
    emitSelection
  } = useTokenSelection({ sentences, onTokenSelect, articleId, clearSentenceSelection, selectTokensInContext })

  // Token drag selection management
  const {
    isDraggingRef,
    wasDraggingRef,
    tokenRefsRef,
    handleMouseDownToken,
    handleMouseEnterToken,
    handleMouseMove,
    handleMouseUp,
    handleBackgroundClick
  } = useTokenDrag({
    sentences,
    selectedTokenIds,
    activeSentenceRef,
    emitSelection,
    clearSelection,
    clearSentenceSelection,
    clearSelectionContext
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
  
  // 🔧 目标句子闪烁状态
  const [flashingSentenceId, setFlashingSentenceId] = useState(null)

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
        
        // 10秒后移除闪烁效果
        setTimeout(() => {
          setFlashingSentenceId(null)
          if (onTargetSentenceScrolled) {
            onTargetSentenceScrolled()
          }
        }, 10000)
      }
    }, 100) // 等待 DOM 渲染
  }, [targetSentenceId, sentences, onTargetSentenceScrolled])

  // Handle sentence selection changes（防重复触发：仅在索引变化时上报）
  const lastEmittedSentenceIndexRef = useRef(null)
  useEffect(() => {
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

      lastEmittedSentenceIndexRef.current = selectedSentenceIndex
      onSentenceSelect(selectedSentenceIndex, sentenceText, selectedSentence)
    }
    // 当 selectedSentenceIndex 变为 null 时，重置记录，避免下次选同一句子不触发
    if (selectedSentenceIndex === null) {
      lastEmittedSentenceIndexRef.current = null
    }
  }, [selectedSentenceIndex, sentences, onSentenceSelect])

  if (isLoading) {
    return (
      <div className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto h-full max-h-[calc(100vh-200px)]">
        <div className="text-gray-500">Loading article...</div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto h-full max-h-[calc(100vh-200px)]">
        <div className="text-red-500">Failed to load: {String(error?.message || error)}</div>
      </div>
    )
  }

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto h-full max-h-[calc(100vh-200px)]"
      onClick={handleBackgroundClick}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <style>{`
        @keyframes sentenceFlash {
          0%, 100% { background: linear-gradient(90deg, rgba(229, 231, 235, 0.3), rgba(209, 213, 219, 0.3)); }
          50% { background: linear-gradient(90deg, rgba(229, 231, 235, 0.6), rgba(209, 213, 219, 0.6)); }
        }
        .sentence-flashing {
          animation: sentenceFlash 1s ease-in-out infinite;
        }
      `}</style>
      <div className="space-y-[0.66rem] leading-[1.33] text-gray-900">
        {sentences.map((sentence, sIdx) => {
          const sentenceId = sentence.sentence_id || (typeof sentence === 'object' && sentence.id)
          const isFlashing = flashingSentenceId === sentenceId
          
          return (
            <SentenceContainer
              key={`s-${sIdx}`}
              sentence={sentence}
              sentenceIndex={sIdx}
              articleId={articleId}
              selectedTokenIds={selectedTokenIds}
              activeSentenceIndex={activeSentenceIndex}
              isDraggingRef={isDraggingRef}
              wasDraggingRef={wasDraggingRef}
              tokenRefsRef={tokenRefsRef}
              hasExplanation={hasExplanation}
              getExplanation={getExplanation}
              hoveredTokenId={hoveredTokenId}
              setHoveredTokenId={setHoveredTokenId}
              handleGetExplanation={handleGetExplanation}
              handleMouseDownToken={handleMouseDownToken}
              handleMouseEnterToken={handleMouseEnterToken}
              addSingle={addSingle}
              isTokenAsked={isTokenAsked}
              markAsAsked={markAsAsked}
              getNotationContent={getNotationContent}
              setNotationContent={setNotationContent}
              onSentenceMouseEnter={handleSentenceMouseEnter}
              onSentenceMouseLeave={handleSentenceMouseLeave}
              onSentenceClick={(idx) => {
                // 句子选择与 token 选择互斥：先清空 token 选择（触发前端 UI 与后端 token=null 同步）
                clearSelection()
                handleSentenceClick(idx)
              }}
              getSentenceBackgroundStyle={(idx) => {
                const baseStyle = getSentenceBackgroundStyle(idx)
                return isFlashing ? `${baseStyle} sentence-flashing` : baseStyle
              }}
              isSentenceInteracting={isSentenceInteracting}
            />
          )
        })}
      </div>
    </div>
  )
}

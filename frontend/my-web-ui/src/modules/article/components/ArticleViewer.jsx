﻿import { useMemo, useEffect } from 'react'
import { useArticle } from '../../../hooks/useApi'
import { useTokenSelection } from '../hooks/useTokenSelection'
import { useTokenDrag } from '../hooks/useTokenDrag'
import { useVocabExplanations } from '../hooks/useVocabExplanations'
import { useSentenceInteraction } from '../hooks/useSentenceInteraction'
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
  onSentenceSelect
}) {
  // Debug logging removed to improve performance
  const { data, isLoading, isError, error } = useArticle(articleId)

  // Asked tokens management - 现在从props接收，不再创建新的hook实例
  // const { askedTokenKeys, isTokenAsked, markAsAsked } = useAskedTokens(articleId)

  const sentences = useMemo(() => {
    const raw = data?.data?.sentences
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

  // Token selection management
  const {
    selectedTokenIds,
    activeSentenceIndex,
    activeSentenceRef,
    clearSelection,
    addSingle,
    emitSelection
  } = useTokenSelection({ sentences, onTokenSelect, articleId, clearSentenceInteraction })

  // Token drag selection management
  const {
    isDraggingRef,
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
    clearSelection
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

  // Handle sentence selection changes
  useEffect(() => {
    // 移除详细日志（已通过测试，减少不必要的日志输出）
    
    // 只有当selectedSentenceIndex不为null且有对应的句子数据时才处理
    if (onSentenceSelect && selectedSentenceIndex !== null && sentences[selectedSentenceIndex]) {
      const selectedSentence = sentences[selectedSentenceIndex]
      const sentenceText = selectedSentence.tokens?.map(token => 
        typeof token === 'string' ? token : token.token_body
      ).join(' ') || ''
      
      // 移除详细日志（已通过测试）
      onSentenceSelect(selectedSentenceIndex, sentenceText, selectedSentence)
    }
    // 移除自动清除逻辑，让父组件控制清除时机
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
      className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto h-full max-h-[calc(100vh-200px)]"
      onClick={handleBackgroundClick}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div className="space-y-[0.66rem] leading-[1.33] text-gray-900">
        {sentences.map((sentence, sIdx) => (
          <SentenceContainer
            key={`s-${sIdx}`}
            sentence={sentence}
            sentenceIndex={sIdx}
            articleId={articleId}
            selectedTokenIds={selectedTokenIds}
            activeSentenceIndex={activeSentenceIndex}
            isDraggingRef={isDraggingRef}
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
            onSentenceClick={handleSentenceClick}
            getSentenceBackgroundStyle={getSentenceBackgroundStyle}
            isSentenceInteracting={isSentenceInteracting}
          />
        ))}
      </div>
    </div>
  )
}

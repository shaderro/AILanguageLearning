import { useMemo } from 'react'
import { useArticle } from '../../../hooks/useApi'
import { useTokenSelection } from '../hooks/useTokenSelection'
import { useTokenDrag } from '../hooks/useTokenDrag'
import { useVocabExplanations } from '../hooks/useVocabExplanations'
import { useSentenceInteraction } from '../hooks/useSentenceInteraction'
import { useGrammarNotations } from '../hooks/useGrammarNotations'
// import { useAskedTokens } from '../hooks/useAskedTokens' // 不再在这里创建hook实例，从props接收
// import { useTokenNotations } from '../hooks/useTokenNotations' // 不再在这里创建hook实例，从props接收
import SentenceContainer from './SentenceContainer'

/**
 * ArticleViewer - Main component for displaying and interacting with article content
 */
export default function ArticleViewer({ 
  articleId, 
  onTokenSelect, 
  isTokenAsked, 
  markAsAsked,
  getNotationContent,
  setNotationContent 
}) {
  console.log('🔍 [ArticleViewer] Received articleId:', articleId)
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

  // Token selection management
  const {
    selectedTokenIds,
    activeSentenceIndex,
    activeSentenceRef,
    clearSelection,
    addSingle,
    emitSelection
  } = useTokenSelection({ sentences, onTokenSelect, articleId })

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

  // Sentence interaction management
  const {
    hoveredSentenceIndex,
    clickedSentenceIndex,
    sentenceRefs,
    handleSentenceMouseEnter,
    handleSentenceMouseLeave,
    handleSentenceClick,
    clearSentenceInteraction,
    getSentenceBackgroundStyle,
    isSentenceInteracting
  } = useSentenceInteraction()

  // Grammar notations management
  const {
    grammarNotations,
    isLoading: grammarNotationsLoading,
    error: grammarNotationsError,
    hasGrammarNotation,
    getGrammarNotation,
    getGrammarNotationsForSentence,
    reload: reloadGrammarNotations
  } = useGrammarNotations(articleId)

  // Token notations management - 现在从props接收，不再创建新的hook实例
  // const { getNotationContent, setNotationContent } = useTokenNotations()

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
            hasGrammarNotation={hasGrammarNotation}
            getGrammarNotationsForSentence={getGrammarNotationsForSentence}
          />
        ))}
      </div>
    </div>
  )
}

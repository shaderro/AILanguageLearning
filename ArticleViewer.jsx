import { useMemo } from 'react'
import { useArticle } from '../../../hooks/useApi'
import { useTokenSelection } from '../hooks/useTokenSelection'
import { useTokenDrag } from '../hooks/useTokenDrag'
import { useVocabExplanations } from '../hooks/useVocabExplanations'
import { useAskedTokens } from '../hooks/useAskedTokens'
import TokenSpan from './TokenSpan'

/**
 * ArticleViewer - Main component for displaying and interacting with article content
 */
export default function ArticleViewer({ articleId, onTokenSelect }) {
  const { data, isLoading, isError, error } = useArticle(articleId)

  // Asked tokens management
  const { askedTokenKeys, isTokenAsked, markAsAsked } = useAskedTokens(articleId)

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
  } = useTokenSelection({ sentences, onTokenSelect })

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
          <div key={`s-${sIdx}`} className="select-none" data-sentence="1">
            {(sentence?.tokens || []).map((t, tIdx) => (
              <TokenSpan
                key={`${sIdx}-${tIdx}`}
                token={t}
                tokenIdx={tIdx}
                sentenceIdx={sIdx}
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
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

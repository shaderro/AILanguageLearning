import { getTokenKey, getTokenId } from '../utils/tokenUtils'
import VocabExplanationButton from './VocabExplanationButton'
import VocabTooltip from './VocabTooltip'

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
  isDraggingRef,
  tokenRefsRef,
  hasExplanation,
  getExplanation,
  hoveredTokenId,
  setHoveredTokenId,
  handleGetExplanation,
  handleMouseDownToken,
  handleMouseEnterToken,
  addSingle,
  isTokenAsked,
  markAsAsked
}) {
  const displayText = typeof token === 'string' ? token : (token?.token_body ?? token?.token ?? '')
  const selectable = typeof token === 'object' ? !!token?.selectable : false
  const uid = getTokenId(token)
  const selected = uid ? selectedTokenIds.has(uid) : false
  const hasSelection = selectedTokenIds && selectedTokenIds.size > 0
  const hoverAllowed = selectable && (!hasSelection ? (activeSentenceIndex == null || activeSentenceIndex === sentenceIdx) : activeSentenceIndex === sentenceIdx)
  const cursorClass = hoverAllowed ? 'cursor-pointer' : 'cursor-default'
  const isTextToken = typeof token === 'object' && token?.token_type === 'text'
  
  // 检查token是否已被提问
  // sentence_id 从 sentenceIdx 计算得出 (sentenceIdx + 1)
  const tokenSentenceId = sentenceIdx + 1
  const tokenSentenceTokenId = token?.sentence_token_id
  
  const isAsked = isTextToken && tokenSentenceTokenId != null
    ? isTokenAsked(articleId, tokenSentenceId, tokenSentenceTokenId)
    : false

  const bgClass = selected
    ? 'bg-yellow-300'
    : (hoverAllowed ? 'bg-transparent hover:bg-yellow-200' : 'bg-transparent')
  const tokenHasExplanation = isTextToken && hasExplanation(token)
  const tokenExplanation = isTextToken ? getExplanation(token) : null
  const isHovered = hoveredTokenId === uid

  return (
    <span
      key={getTokenKey(sentenceIdx, token, tokenIdx)}
      className="relative inline-block"
    >
      <span
        data-token="1"
        ref={(el) => {
          if (!tokenRefsRef.current[sentenceIdx]) tokenRefsRef.current[sentenceIdx] = {}
          tokenRefsRef.current[sentenceIdx][tokenIdx] = el
        }}
        onMouseDown={(e) => handleMouseDownToken(sentenceIdx, tokenIdx, token, e)}
        onMouseEnter={() => {
          if (isTextToken && tokenHasExplanation) {
            setHoveredTokenId(uid)
          }
          handleMouseEnterToken(sentenceIdx, tokenIdx, token)
        }}
        onMouseLeave={() => {
          if (isTextToken && tokenHasExplanation) {
            setHoveredTokenId(null)
          }
        }}
        onClick={(e) => { if (!isDraggingRef.current && selectable) { e.preventDefault(); addSingle(sentenceIdx, token) } }}
        className={[
          'px-0.5 rounded-sm transition-colors duration-150 select-none',
          cursorClass,
          bgClass,
          isAsked ? 'border-b-2 border-green-500' : ''
        ].join(' ')}
        style={{ color: '#111827' }}
      >
        {displayText}
      </span>
      
      {isTextToken && tokenHasExplanation && (
        <VocabTooltip 
          token={token} 
          explanation={tokenExplanation} 
          isVisible={isHovered} 
        />
      )}
      
      {isTextToken && selected && selectedTokenIds.size === 1 && (
        <VocabExplanationButton 
          token={token} 
          onGetExplanation={handleGetExplanation}
          markAsAsked={markAsAsked}
          articleId={articleId}
          sentenceIdx={sentenceIdx}
        />
      )}
    </span>
  )
}


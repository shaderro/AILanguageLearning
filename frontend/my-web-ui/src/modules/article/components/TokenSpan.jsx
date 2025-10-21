import { useState } from 'react'
import { getTokenKey, getTokenId } from '../utils/tokenUtils'
import VocabExplanationButton from './VocabExplanationButton'
import VocabTooltip from './VocabTooltip'
import TokenNotation from './TokenNotation'

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
  markAsAsked,
  getNotationContent,
  setNotationContent
}) {
  const displayText = typeof token === 'string' ? token : (token?.token_body ?? token?.token ?? '')
  const selectable = typeof token === 'object' ? !!token?.selectable : false
  const uid = getTokenId(token, sentenceIdx)
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
  
  // 管理TokenNotation的显示状态（针对已提问的token）
  const [showNotation, setShowNotation] = useState(false)
  
  // 获取该token的notation内容
  const notationContent = isAsked && getNotationContent 
    ? getNotationContent(articleId, tokenSentenceId, tokenSentenceTokenId)
    : null

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
          console.debug('[TokenSpan.mouseEnter] sentenceIdx=', sentenceIdx, 'uid=', uid, 'text=', displayText)
          // 如果是已提问的token，显示notation
          if (isAsked) {
            setShowNotation(true)
          }
          handleMouseEnterToken(sentenceIdx, tokenIdx, token)
        }}
        onMouseLeave={() => {
          if (isTextToken && tokenHasExplanation) {
            setHoveredTokenId(null)
          }
          // 隐藏notation
          if (isAsked) {
            setShowNotation(false)
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
      
      {/* TokenNotation - 显示在已提问token下方 */}
      {isAsked && showNotation && (
        <TokenNotation 
          isVisible={showNotation}
          note={notationContent || "This is a test note"}
          textId={articleId}
          sentenceId={tokenSentenceId}
          tokenIndex={tokenSentenceTokenId}
        />
      )}
    </span>
  )
}


import { useState, useRef } from 'react'
import { getTokenKey, getTokenId } from '../utils/tokenUtils'
// import VocabExplanationButton from './VocabExplanationButton' // 暂时注释掉 - 以后可能会用到
import VocabTooltip from './VocabTooltip'
import TokenNotation from './TokenNotation'
import GrammarNotation from './GrammarNotation'

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
  setNotationContent,
  // Grammar notation props
  hasGrammarNotation,
  getGrammarNotationsForSentence,
  // Vocab notation props
  getVocabExampleForToken
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
  
  // 调试日志已关闭以提升性能

  // 检查是否有grammar notation
  const sentenceId = sentenceIdx + 1
  const grammarNotations = getGrammarNotationsForSentence ? getGrammarNotationsForSentence(sentenceId) : []
  const hasGrammar = grammarNotations.length > 0
  
  // 检查当前token是否在grammar notation的marked_token_ids中
  // 如果marked_token_ids为空，则整个句子都有grammar notation
  const isInGrammarNotation = hasGrammar && grammarNotations.some(notation => {
    if (!notation.marked_token_ids || notation.marked_token_ids.length === 0) {
      // 如果marked_token_ids为空，整个句子都有grammar notation
      return true
    }
    return notation.marked_token_ids.includes(tokenSentenceTokenId)
  })

  // 检查是否有 vocab notation（来自缓存列表，而不依赖 asked tokens）
  const vocabNotationsForSentence = typeof getVocabNotationsForSentence === 'function'
    ? getVocabNotationsForSentence(sentenceId)
    : []
  const hasVocabNotationForToken = Array.isArray(vocabNotationsForSentence)
    ? vocabNotationsForSentence.some(n => n?.token_index === tokenSentenceTokenId)
    : false

  // 检查是否在 asked tokens 中有 vocab 记录（通过 isAsked 已经包含了这个检查）
  const hasVocabVisual = isAsked || hasVocabNotationForToken

  const bgClass = selected
    ? 'bg-yellow-300'
    : (hoverAllowed ? 'bg-transparent hover:bg-yellow-200' : 'bg-transparent')
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
          // Debug logging removed for performance
          // 如果是已提问的token，显示notation
          if (isAsked) {
            cancelHideNotation()  // 取消任何待处理的隐藏
            setShowNotation(true)
          }
          handleMouseEnterToken(sentenceIdx, tokenIdx, token)
        }}
        onMouseLeave={() => {
          if (isTextToken && tokenHasExplanation) {
            setHoveredTokenId(null)
          }
          // 延迟隐藏notation（而不是立即隐藏）
          if (isAsked) {
            scheduleHideNotation()
          }
        }}
        onClick={(e) => { 
          if (!isDraggingRef.current && selectable) { 
            e.preventDefault(); 
            e.stopPropagation(); 
            addSingle(sentenceIdx, token) 
          } 
        }}
        className={[
          'px-0.5 rounded-sm transition-colors duration-150 select-none',
          cursorClass,
          bgClass,
          // 优先级：vocab 绿色 > 语法 灰色
          hasVocabVisual ? 'border-b-2 border-green-500' : (isInGrammarNotation ? 'border-b-2 border-gray-400' : '')
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
      
      {/* TokenNotation - 对有 vocab 标注（asked 或缓存命中）的 token 显示 */}
      {hasVocabVisual && showNotation && (
        <TokenNotation 
          isVisible={showNotation}
          note={notationContent || "This is a test note"}
          textId={articleId}
          sentenceId={tokenSentenceId}
          tokenIndex={tokenSentenceTokenId}
          onMouseEnter={handleNotationMouseEnter}
          onMouseLeave={handleNotationMouseLeave}
          getVocabExampleForToken={getVocabExampleForToken}
        />
      )}
      
      {/* GrammarNotation is now handled at sentence level in SentenceContainer */}
    </span>
  )
}


import { useState, useRef, useMemo, useContext } from 'react'
import { getTokenKey, getTokenId } from '../utils/tokenUtils'
// import VocabExplanationButton from './VocabExplanationButton' // 暂时注释掉 - 以后可能会用到
import VocabTooltip from './VocabTooltip'
import VocabNotationCard from './notation/VocabNotationCard'
import GrammarNotation from './GrammarNotation'
import { NotationContext } from '../contexts/NotationContext'
import { useTokenSelectable } from '../selection/hooks/useTokenSelectable'

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
  wasDraggingRef,
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
  // 从 NotationContext 获取 notation 相关功能
  const notationContext = useContext(NotationContext)
  const {
    getGrammarNotationsForSentence,
    getVocabNotationsForSentence,
    getVocabExampleForToken,
    isTokenAsked: isTokenAskedFromContext
  } = notationContext || {}
  
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
  const sentenceId = sentenceIdx + 1
  const grammarNotations = getGrammarNotationsForSentence ? getGrammarNotationsForSentence(sentenceId) : []
  const hasGrammar = grammarNotations.length > 0
  
  // 检查当前token是否在grammar notation的marked_token_ids中
  // 如果marked_token_ids为空，则整个句子都有grammar notation
  // 取消 grammar 灰色下划线的渲染，改用句子右下角徽标触发卡片
  const isInGrammarNotation = false

  // 优先检查 vocab notation（从新API加载）
  // vocab notation是数据源，asked tokens只是兼容层
  // 使用useMemo缓存计算结果，避免每次渲染都重新计算
  const vocabNotationsForSentence = useMemo(() => {
    return typeof getVocabNotationsForSentence === 'function'
      ? getVocabNotationsForSentence(sentenceId)
      : []
  }, [getVocabNotationsForSentence, sentenceId])
  
  // 使用useMemo缓存匹配结果，避免每次渲染都重新计算
  const hasVocabNotationForToken = useMemo(() => {
    if (!Array.isArray(vocabNotationsForSentence) || tokenSentenceTokenId == null) {
      return false
    }
    const currentTokenId = Number(tokenSentenceTokenId)
    return vocabNotationsForSentence.some(n => {
      // 确保类型一致（数字比较）
      const notationTokenId = Number(n?.token_id ?? n?.token_index)
      return notationTokenId === currentTokenId
    })
  }, [vocabNotationsForSentence, tokenSentenceTokenId])

  // 优先使用vocab notation，asked tokens作为备用（向后兼容）
  // 如果vocab notation存在，就不需要检查asked tokens了
  const hasVocabVisual = hasVocabNotationForToken || (isAsked && !hasVocabNotationForToken)

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
          selOnEnter()
          if (isTextToken && tokenHasExplanation) {
            setHoveredTokenId(uid)
          }
          // 如果有vocab notation（来自vocab_notations或asked tokens），显示notation卡片
          if (hasVocabVisual) {
            cancelHideNotation()  // 取消任何待处理的隐藏
            setShowNotation(true)
          }
          handleMouseEnterToken(sentenceIdx, tokenIdx, token)
        }}
        onMouseLeave={() => {
          selOnLeave()
          if (isTextToken && tokenHasExplanation) {
            setHoveredTokenId(null)
          }
          // 延迟隐藏notation（而不是立即隐藏）
          if (hasVocabVisual) {
            scheduleHideNotation()
          }
        }}
        onClick={(e) => { 
          // 如果正在拖拽或刚结束拖拽，完全跳过点击处理（避免拖拽结束时误触发切换）
          if (isDraggingRef.current || wasDraggingRef.current) {
            console.log('⏭️ [TokenSpan] onClick blocked - dragging or just finished dragging')
            e.preventDefault()
            e.stopPropagation()
            return
          }
          selOnClick()
          if (selectable) { 
            e.preventDefault(); 
            e.stopPropagation(); 
            addSingle(sentenceIdx, token) 
          } 
        }}
        className={[
          'px-0.5 rounded-sm transition-colors duration-150 select-none',
          cursorClass,
          bgClass,
          selectionTokenClass,
          // 只渲染 vocab 绿色下划线；grammar 改为句子徽标触发
          hasVocabVisual ? 'border-b-2 border-green-500' : ''
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
      
      {/* VocabNotationCard - 对有 vocab 标注（来自vocab_notations或asked tokens）的 token 显示 */}
      {hasVocabVisual && showNotation && (
        <VocabNotationCard 
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


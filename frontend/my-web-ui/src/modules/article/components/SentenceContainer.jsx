import { useState, useRef, useContext } from 'react'
import TokenSpan from './TokenSpan'
import GrammarNotationCard from './notation/GrammarNotationCard'
import GrammarNoteBadge from './notation/GrammarNoteBadge'
import { NotationContext } from '../contexts/NotationContext'
import { useSentenceSelectable } from '../selection/hooks/useSentenceSelectable'

/**
 * SentenceContainer - Handles sentence-level interactions and renders tokens
 */
export default function SentenceContainer({
  sentence,
  sentenceIndex,
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
  setNotationContent,
  // Sentence interaction handlers
  onSentenceMouseEnter,
  onSentenceMouseLeave,
  onSentenceClick,
  getSentenceBackgroundStyle,
  isSentenceInteracting
}) {
  // 从 NotationContext 获取 notation 相关功能
  const notationContext = useContext(NotationContext)
  const {
    hasGrammarNotation,
    getGrammarNotationsForSentence,
    getGrammarRuleById
  } = notationContext || {}
  
  // Grammar notation hover state
  const [showGrammarCard, setShowGrammarCard] = useState(false)
  const [grammarCardPosition, setGrammarCardPosition] = useState({ top: 0, left: 0, right: 'auto' })
  const sentenceRef = useRef(null)
  const hideCardTimerRef = useRef(null)
  const handleSentenceMouseEnter = (e) => {
    // Trigger when entering the sentence container
    onSentenceMouseEnter(sentenceIndex)
  }

  const handleSentenceMouseLeave = (e) => {
    // Trigger when leaving the sentence container
    onSentenceMouseLeave()
    // 不在句子离开时自动隐藏，改由徽标/卡片的 mouseleave 控制
  }
  
  // Handle card mouse enter - cancel hiding
  const handleCardMouseEnter = () => {
    if (hideCardTimerRef.current) {
      clearTimeout(hideCardTimerRef.current)
      hideCardTimerRef.current = null
    }
  }
  
  // Handle card mouse leave - hide card
  const handleCardMouseLeave = () => {
    setShowGrammarCard(false)
  }

  const handleSentenceClick = async (e) => {
    // 如果正在拖拽或刚结束拖拽，跳过句子点击（避免清空 token 选择）
    if (isDraggingRef.current || wasDraggingRef.current) {
      console.log(`⏭️ [SentenceContainer] Sentence click blocked - dragging or just finished dragging`)
      e.stopPropagation()
      return
    }
    
    // Always trigger sentence click for now - we'll let the token components handle their own clicks
    e.stopPropagation()
    
    // 移除多余的API调用 - 语法例句数据已通过GrammarNotationCard在hover时获取
    console.log(`🔍 [SentenceContainer] Clicking sentence ${sentenceId} - no API call needed`)
    
    onSentenceClick(sentenceIndex)
  }

  const backgroundStyle = getSentenceBackgroundStyle(sentenceIndex)
  const isInteracting = isSentenceInteracting(sentenceIndex)
  
  // Check if this sentence has grammar notations
  const sentenceId = sentenceIndex + 1 // Convert 0-based index to 1-based sentence ID
  const hasGrammar = hasGrammarNotation ? hasGrammarNotation(sentenceId) : false
  const grammarNotations = getGrammarNotationsForSentence ? getGrammarNotationsForSentence(sentenceId) : []
  
  // Debug logging removed to improve performance

  // Selection hook（句子级选择）
  const { className: selectionSentenceClass, onMouseEnter: selOnEnter, onMouseLeave: selOnLeave, onClick: selOnClick } = useSentenceSelectable({
    textId: articleId,
    sentenceId
  })

  return (
    <div 
      ref={sentenceRef}
      key={`s-${sentenceIndex}`} 
      className={`select-none relative transition-all duration-200 hover:bg-gray-100 ${selectionSentenceClass}`}
      data-sentence="1"
      onMouseEnter={(e) => { selOnEnter(); /* 不再用整句 hover 触发卡片 */ handleSentenceMouseEnter(e) }}
      onMouseLeave={(e) => { selOnLeave(); /* 不再用整句 hover 触发卡片 */ handleSentenceMouseLeave(e) }}
      onClick={(e) => { selOnClick(e); handleSentenceClick(e) }}
      style={{}}
    >
      {/* 移除旧的背景/边框层，避免与 Selection 模块产生双重边框/叠加样式 */}
      
      {(sentence?.tokens || []).map((token, tokenIndex) => (
        <TokenSpan
          key={`${sentenceIndex}-${tokenIndex}`}
          token={token}
          tokenIdx={tokenIndex}
          sentenceIdx={sentenceIndex}
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
        />
      ))}
      
      {/* Grammar notation card - shown when hovering over the entire sentence */}
      {hasGrammar && grammarNotations.length > 0 && (
        <>
          {/* 右下角小徽标作为触发器 */}
          <div className="mt-1 flex justify-end">
            <GrammarNoteBadge
              className=""
              style={{ fontSize: '0.60em' }}
              label="grammar note"
              onMouseEnter={() => {
                const rect = sentenceRef.current?.getBoundingClientRect()
                if (rect) {
                  setGrammarCardPosition({ top: rect.bottom + 8, left: rect.left, right: 'auto' })
                }
                setShowGrammarCard(true)
              }}
              onMouseLeave={() => {
                hideCardTimerRef.current = setTimeout(() => setShowGrammarCard(false), 120)
              }}
            />
          </div>

          {/* 语法注释卡片 */}
          <GrammarNotationCard
            isVisible={showGrammarCard}
            textId={articleId}
            sentenceId={sentenceId}
            position={grammarCardPosition}
            onClose={() => setShowGrammarCard(false)}
            onMouseEnter={handleCardMouseEnter}
            onMouseLeave={handleCardMouseLeave}
            cachedGrammarRules={grammarNotations}
            getGrammarRuleById={getGrammarRuleById}
          />
        </>
      )}
    </div>
  )
}

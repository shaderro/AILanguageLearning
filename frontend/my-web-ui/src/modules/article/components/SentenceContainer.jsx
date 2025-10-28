import { useState, useRef } from 'react'
import TokenSpan from './TokenSpan'
import GrammarNotationCard from './GrammarNotationCard'

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
  isSentenceInteracting,
  // Grammar notation props
  hasGrammarNotation,
  getGrammarNotationsForSentence,
  getGrammarRuleById,
  // Vocab notation props
  getVocabExampleForToken
}) {
  // Grammar notation hover state
  const [showGrammarCard, setShowGrammarCard] = useState(false)
  const [grammarCardPosition, setGrammarCardPosition] = useState({ top: 0, left: 0, right: 'auto' })
  const sentenceRef = useRef(null)
  const hideCardTimerRef = useRef(null)
  const handleSentenceMouseEnter = (e) => {
    // Trigger when entering the sentence container
    onSentenceMouseEnter(sentenceIndex)
    
    // Show grammar card if this sentence has grammar notations
    
    if (hasGrammar && grammarNotations.length > 0) {
      const rect = sentenceRef.current?.getBoundingClientRect()
      if (rect) {
        // Showing grammar card for sentence
        setGrammarCardPosition({
          top: rect.bottom + 8,
          left: rect.left,
          right: 'auto'
        })
        setShowGrammarCard(true)
      }
    }
  }

  const handleSentenceMouseLeave = (e) => {
    // Trigger when leaving the sentence container
    onSentenceMouseLeave()
    
    // Hide grammar card with delay
    hideCardTimerRef.current = setTimeout(() => {
      setShowGrammarCard(false)
    }, 100)
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

  return (
    <div 
      ref={sentenceRef}
      key={`s-${sentenceIndex}`} 
      className={`select-none relative transition-all duration-200`}
      data-sentence="1"
      onMouseEnter={handleSentenceMouseEnter}
      onMouseLeave={handleSentenceMouseLeave}
      onClick={handleSentenceClick}
    >
      {/* Legacy active sentence background - keep for compatibility with token selection */}
      {activeSentenceIndex === sentenceIndex && (
        <div className="absolute inset-0 bg-gray-100 border border-gray-300 rounded-md z-0" />
      )}
      
      {/* New sentence interaction background */}
      {isInteracting && (
        <div className={`absolute inset-0 z-0 ${backgroundStyle}`} />
      )}
      
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
          hasGrammarNotation={hasGrammarNotation}
          getGrammarNotationsForSentence={getGrammarNotationsForSentence}
          getVocabExampleForToken={getVocabExampleForToken}
        />
      ))}
      
      {/* Grammar notation card - shown when hovering over the entire sentence */}
      {hasGrammar && grammarNotations.length > 0 && (
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
      )}
    </div>
  )
}

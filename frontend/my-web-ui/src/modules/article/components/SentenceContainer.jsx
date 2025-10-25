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
  getGrammarNotationsForSentence
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
    console.log(`🔍 [SentenceContainer] Mouse enter sentence ${sentenceId}:`, {
      hasGrammar,
      grammarNotations: grammarNotations.length,
      sentenceIndex
    })
    
    if (hasGrammar && grammarNotations.length > 0) {
      const rect = sentenceRef.current?.getBoundingClientRect()
      if (rect) {
        console.log(`📍 [SentenceContainer] Showing grammar card for sentence ${sentenceId}`)
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
    
    // 调用grammar rule manager获取grammar examples
    try {
      console.log(`🔍 [SentenceContainer] Clicking sentence ${sentenceId}, calling grammar rule manager...`)
      
      // 这里需要调用后端的API来获取grammar examples
      const apiUrl = `http://localhost:8000/api/grammar_examples/${articleId}/${sentenceId}`
      console.log(`🔍 [SentenceContainer] Calling API: ${apiUrl}`)
      
      const response = await fetch(apiUrl)
      console.log(`🔍 [SentenceContainer] API response status: ${response.status}`)
      console.log(`🔍 [SentenceContainer] API response headers:`, response.headers)
      
      if (response.ok) {
        const data = await response.json()
        console.log(`📚 [SentenceContainer] Grammar examples for sentence ${sentenceId}:`, data)
        
        // 打印每个grammar example的详细信息
        if (data.success && data.data && data.data.length > 0) {
          console.log(`\n🔍 [SentenceContainer] Detailed Grammar Examples for Sentence ${sentenceId}:`)
          data.data.forEach((example, index) => {
            console.log(`\n--- Grammar Example ${index + 1} ---`)
            console.log(`Rule ID: ${example.rule_id}`)
            console.log(`Rule Name: ${example.rule_name}`)
            console.log(`Rule Summary: ${example.rule_summary}`)
            console.log(`Rule Explanation: ${example.rule_summary}`) // 使用rule_summary作为explanation
            console.log(`Context Explanation: ${example.example.explanation_context}`)
            console.log(`Text ID: ${example.example.text_id}`)
            console.log(`Sentence ID: ${example.example.sentence_id}`)
          })
        } else {
          console.log(`📝 [SentenceContainer] No grammar examples found for sentence ${sentenceId}`)
        }
      } else {
        const text = await response.text()
        console.log(`❌ [SentenceContainer] Failed to fetch grammar examples: ${response.status}`)
        console.log(`❌ [SentenceContainer] Response text:`, text.substring(0, 200)) // 只显示前200个字符
      }
    } catch (error) {
      console.error(`❌ [SentenceContainer] Error fetching grammar examples:`, error)
    }
    
    onSentenceClick(sentenceIndex)
  }

  const backgroundStyle = getSentenceBackgroundStyle(sentenceIndex)
  const isInteracting = isSentenceInteracting(sentenceIndex)
  
  // Check if this sentence has grammar notations
  const sentenceId = sentenceIndex + 1 // Convert 0-based index to 1-based sentence ID
  const hasGrammar = hasGrammarNotation ? hasGrammarNotation(sentenceId) : false
  const grammarNotations = getGrammarNotationsForSentence ? getGrammarNotationsForSentence(sentenceId) : []
  
  // Debug logging
  if (sentenceId === 4 || sentenceId === 7) {
    console.log(`🔍 [SentenceContainer] Sentence ${sentenceId}:`, {
      hasGrammar,
      grammarNotations,
      sentenceIndex
    })
  }

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
        />
      )}
    </div>
  )
}

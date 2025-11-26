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
  
  // 🔧 获取 sentence_id 用于标识（优先使用数据中的 sentence_id，否则使用索引+1）
  const sentenceId = sentence?.sentence_id || (typeof sentence === 'object' && sentence?.id) || (sentenceIndex + 1)
  
  // Check if this sentence has grammar notations
  const hasGrammar = hasGrammarNotation ? hasGrammarNotation(sentenceId) : false
  const grammarNotations = getGrammarNotationsForSentence ? getGrammarNotationsForSentence(sentenceId) : []
  
  // Debug logging
  if (grammarNotations.length > 0) {
    console.log('🔍 [SentenceContainer] Grammar notations for sentence', sentenceId, ':', grammarNotations)
  }

  // Selection hook（句子级选择）
  const { className: selectionSentenceClass, onMouseEnter: selOnEnter, onMouseLeave: selOnLeave, onClick: selOnClick } = useSentenceSelectable({
    textId: articleId,
    sentenceId
  })
  
  // 🔧 分词下划线功能：检测是否为中文（无空格语言）且有 word_tokens
  const isNonWhitespace = sentence?.is_non_whitespace || sentence?.language_code === 'zh'
  const wordTokens = sentence?.word_tokens || []
  const hasWordTokens = Array.isArray(wordTokens) && wordTokens.length > 0
  const shouldShowSegmentationUnderline = isNonWhitespace && hasWordTokens
  
  // 🔧 跟踪 hover 状态（句子或 token）
  const [isHovered, setIsHovered] = useState(false)
  
  // 🔧 检查句子是否被选中或交互中
  const isSentenceSelected = isSentenceInteracting && isSentenceInteracting(sentenceIndex)
  
  // 🔧 检查是否有 token 被选中（在当前句子中）
  // selectedTokenIds 中的 uid 格式是 `${sentenceIdx}-${sentence_token_id}`
  const hasSelectedTokens = selectedTokenIds && selectedTokenIds.size > 0 && 
    Array.from(selectedTokenIds).some(uid => {
      const uidStr = String(uid)
      // 检查 uid 是否以当前句子索引开头
      return uidStr.startsWith(`${sentenceIndex}-`)
    })
  
  // 🔧 判断是否应该显示分词 UI：hover 或选中时都显示
  const shouldShowSegmentationUI = shouldShowSegmentationUnderline && (isHovered || isSentenceSelected || hasSelectedTokens)
  
  // 🔧 辅助函数：检查某个 token 是否属于某个 word_token（用于显示下划线）
  const getTokenWordTokenInfo = (token, tokenIndex) => {
    if (!shouldShowSegmentationUnderline || !token) return null
    
    const tokenId = token?.sentence_token_id || token?.token_id
    if (tokenId == null) return null
    
    // 查找包含该 token 的 word_token
    for (const wordToken of wordTokens) {
      const tokenIds = wordToken?.token_ids || []
      if (Array.isArray(tokenIds) && tokenIds.includes(Number(tokenId))) {
        // 🔧 计算该 token 在 word_token 中的位置
        const sortedTokenIds = [...tokenIds].sort((a, b) => a - b)
        const tokenIndexInWord = sortedTokenIds.indexOf(Number(tokenId))
        const isFirstInWord = tokenIndexInWord === 0
        const isLastInWord = tokenIndexInWord === sortedTokenIds.length - 1
        const isSingleCharWord = sortedTokenIds.length === 1
        
        return {
          wordTokenId: wordToken?.word_token_id,
          tokenIds: sortedTokenIds,
          wordBody: wordToken?.word_body,
          tokenIndexInWord,
          isFirstInWord,
          isLastInWord,
          isSingleCharWord
        }
      }
    }
    return null
  }
  
  // 🔧 处理句子 hover
  const handleSentenceHover = (e) => {
    if (shouldShowSegmentationUnderline) {
      setIsHovered(true)
    }
    selOnEnter()
    handleSentenceMouseEnter(e)
  }
  
  const handleSentenceHoverLeave = (e) => {
    if (shouldShowSegmentationUnderline) {
      setIsHovered(false)
    }
    selOnLeave()
    handleSentenceMouseLeave(e)
  }
  
  return (
    <div 
      ref={sentenceRef}
      key={`s-${sentenceIndex}`} 
      className={`select-none relative transition-all duration-200 ${backgroundStyle} ${selectionSentenceClass}`}
      data-sentence="1"
      data-sentence-id={sentenceId}
      onMouseEnter={handleSentenceHover}
      onMouseLeave={handleSentenceHoverLeave}
      onClick={(e) => { selOnClick(e); handleSentenceClick(e) }}
      style={{}}
    >
      {/* 移除旧的背景/边框层，避免与 Selection 模块产生双重边框/叠加样式 */}
      
      {(sentence?.tokens || []).map((token, tokenIndex) => {
        // 🔧 获取该 token 的 word_token 信息（用于显示分词下划线）
        const wordTokenInfo = getTokenWordTokenInfo(token, tokenIndex)
        const shouldShowUnderline = shouldShowSegmentationUI && wordTokenInfo != null
        
        // 🔧 检查当前 token 和下一个 token 是否属于不同的 word token（用于添加空格）
        let shouldAddSpaceAfter = false
        if (shouldShowSegmentationUI && tokenIndex < (sentence?.tokens || []).length - 1) {
          const nextToken = sentence.tokens[tokenIndex + 1]
          // 🔧 只对文本类型的 token 添加空格（不包括标点符号和空格）
          const isCurrentTextToken = token?.token_type === 'text' || (typeof token === 'object' && !token?.token_type)
          const isNextTextToken = nextToken?.token_type === 'text' || (typeof nextToken === 'object' && !nextToken?.token_type)
          
          if (isCurrentTextToken && isNextTextToken) {
            const nextTokenWordTokenInfo = getTokenWordTokenInfo(nextToken, tokenIndex + 1)
            
            // 如果当前 token 和下一个 token 都属于 word token，但属于不同的 word token，则添加空格
            if (wordTokenInfo && nextTokenWordTokenInfo) {
              const currentWordTokenId = wordTokenInfo.wordTokenId
              const nextWordTokenId = nextTokenWordTokenInfo.wordTokenId
              if (currentWordTokenId !== nextWordTokenId) {
                shouldAddSpaceAfter = true
              }
            } else if (wordTokenInfo && !nextTokenWordTokenInfo) {
              // 当前 token 属于 word token，下一个不属于，添加空格
              shouldAddSpaceAfter = true
            } else if (!wordTokenInfo && nextTokenWordTokenInfo) {
              // 当前 token 不属于 word token，下一个属于，添加空格
              shouldAddSpaceAfter = true
            }
          }
        }
        
        return (
          <>
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
              handleMouseEnterToken={(sIdx, tIdx, t) => {
                // 🔧 当 hover token 时，也显示分词下划线
                if (shouldShowSegmentationUnderline) {
                  setIsHovered(true)
                }
                handleMouseEnterToken(sIdx, tIdx, t)
              }}
              addSingle={addSingle}
              isTokenAsked={isTokenAsked}
              markAsAsked={markAsAsked}
              getNotationContent={getNotationContent}
              setNotationContent={setNotationContent}
              // 🔧 新增：分词下划线相关 props
              showSegmentationUnderline={shouldShowUnderline}
              wordTokenInfo={wordTokenInfo}
            />
            {/* 🔧 在不同 word token 之间添加空格（只在 hover 时显示） */}
            {shouldAddSpaceAfter && (
              <span key={`space-${sentenceIndex}-${tokenIndex}`} className="inline-block w-2" aria-hidden="true" />
            )}
          </>
        )
      })}
      
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

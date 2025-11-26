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
  setNotationContent,
  // 🔧 新增：分词下划线相关 props
  showSegmentationUnderline = false,
  wordTokenInfo = null
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
  const anchorRef = useRef(null)
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
  // 🔧 移除 useMemo，直接调用函数，确保每次渲染都能获取最新数据
  const vocabNotationsForSentence = typeof getVocabNotationsForSentence === 'function'
    ? getVocabNotationsForSentence(sentenceId)
    : []
  
  // 🔧 获取当前 token 的 word_token_id（如果存在）
  const currentTokenWordTokenId = token?.word_token_id ? Number(token.word_token_id) : null
  
  // 使用useMemo缓存匹配结果，避免每次渲染都重新计算
  // 🔧 修复：不仅检查是否有匹配，还要找到最匹配的 notation（用于后续显示正确的 vocab example）
  const { hasVocabNotationForToken, matchedNotation } = useMemo(() => {
    if (!Array.isArray(vocabNotationsForSentence) || tokenSentenceTokenId == null) {
      return { hasVocabNotationForToken: false, matchedNotation: null }
    }
    const currentTokenId = Number(tokenSentenceTokenId)
    
    // 🔧 优先匹配：如果当前 token 有 word_token_id，优先匹配相同 word_token_id 的 notation
    if (currentTokenWordTokenId != null) {
      const exactMatch = vocabNotationsForSentence.find(n => {
        const notationWordTokenId = n?.word_token_id ? Number(n.word_token_id) : null
        return notationWordTokenId === currentTokenWordTokenId
      })
      
      if (exactMatch) {
        return { hasVocabNotationForToken: true, matchedNotation: exactMatch }
      }
    }
    
    // 🔧 次优匹配：检查 word_token_token_ids 是否包含当前 token
    const wordTokenMatch = vocabNotationsForSentence.find(n => {
      if (n?.word_token_token_ids && Array.isArray(n.word_token_token_ids) && n.word_token_token_ids.length > 0) {
        const tokenIdsArray = n.word_token_token_ids.map(id => Number(id))
        return tokenIdsArray.includes(currentTokenId)
      }
      return false
    })
    
    if (wordTokenMatch) {
      return { hasVocabNotationForToken: true, matchedNotation: wordTokenMatch }
    }
    
    // 🔧 回退匹配：使用 token_id 精确匹配（用于空格语言或没有 word_token_token_ids 的情况）
    const tokenIdMatch = vocabNotationsForSentence.find(n => {
      const notationTokenId = Number(n?.token_id ?? n?.token_index)
      return notationTokenId === currentTokenId
    })
    
    if (tokenIdMatch) {
      return { hasVocabNotationForToken: true, matchedNotation: tokenIdMatch }
    }
    
    return { hasVocabNotationForToken: false, matchedNotation: null }
  }, [vocabNotationsForSentence, tokenSentenceTokenId, currentTokenWordTokenId])

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
      ref={anchorRef}
    >
      <span
        data-token="1"
        ref={(el) => {
          if (!tokenRefsRef.current[sentenceIdx]) tokenRefsRef.current[sentenceIdx] = {}
          tokenRefsRef.current[sentenceIdx][tokenIdx] = el
        }}
        onMouseDown={(e) => handleMouseDownToken(sentenceIdx, tokenIdx, token, e)}
        onMouseEnter={() => {
          // 只有可选择的token才触发hover效果
          if (selectable) {
            selOnEnter()
          }
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
          // 只有可选择的token才清除hover效果
          if (selectable) {
            selOnLeave()
          }
          if (isTextToken && tokenHasExplanation) {
            setHoveredTokenId(null)
          }
          // 延迟隐藏notation（而不是立即隐藏）
          if (hasVocabVisual) {
            scheduleHideNotation()
          }
          // 🔧 注意：分词下划线的显示/隐藏由 SentenceContainer 的 hover 状态控制
          // 这里不需要额外处理，因为当鼠标离开整个句子时，SentenceContainer 会处理
        }}
        onClick={(e) => { 
          // 如果正在拖拽或刚结束拖拽，完全跳过点击处理（避免拖拽结束时误触发切换）
          if (isDraggingRef.current || wasDraggingRef.current) {
            console.log('⏭️ [TokenSpan] onClick blocked - dragging or just finished dragging')
            e.preventDefault()
            e.stopPropagation()
            return
          }
          // 只有可选择的token才响应点击
          if (selectable) { 
            selOnClick()
            e.preventDefault(); 
            e.stopPropagation(); 
            addSingle(sentenceIdx, token) 
          } 
        }}
        className={[
          'px-0.5 rounded-sm transition-colors duration-150 select-none relative',
          cursorClass,
          bgClass,
          selectionTokenClass,
          // 只渲染 vocab 绿色下划线；grammar 改为句子徽标触发
          hasVocabVisual ? 'border-b-2 border-green-500' : ''
        ].join(' ')}
        style={{ color: '#111827' }}
      >
        {displayText}
        {/* 🔧 分词下划线：在 token 下方显示灰色下划线（表示 word token 的分词边界） */}
        {/* 🔧 只对文本类型的 token 显示下划线，不包括标点符号和空格 */}
        {showSegmentationUnderline && wordTokenInfo && isTextToken && token?.token_type !== 'punctuation' && token?.token_type !== 'space' && (() => {
          // 🔧 根据 token 在 word_token 中的位置，调整下划线的样式
          // 目标：同一个 word_token 内的字符下划线连续，不同 word_token 之间有间隙
          // 注意：token span 有 px-0.5 (左右各 2px padding)，下划线是绝对定位的
          // 下划线的 left 是相对于 token span 的内容区域（不包括 padding）的
          const { isFirstInWord, isLastInWord, isSingleCharWord } = wordTokenInfo
          
          let finalLeft = '0%'
          let finalWidth = '100%'
          
          // 🔧 统一基准：所有字符的下划线都从 padding 的左边缘开始（-2px），确保对齐
          // 然后通过宽度调整来实现连接或留空隙
          if (isSingleCharWord) {
            // 单独字符：从 padding 左边缘开始，但左右都有空隙（缩短到 75%，居中）
            // 调整 left 使下划线居中：从 padding 左边缘(-2px) + 内容区域12.5%开始
            finalLeft = 'calc(-2px + 12.5%)' // 从 padding 左边缘 + 内容区域12.5%开始（居中）
            finalWidth = '75%' // 宽度 75%
          } else if (isFirstInWord) {
            // 第一个字符：从 padding 左边缘开始，延伸到右侧（覆盖右侧 padding，与下一个字符连接）
            finalLeft = '-2px' // 从 padding 左边缘开始，统一基准
            finalWidth = 'calc(100% + 4px)' // 总宽度：内容(100%) + 左侧padding(2px) + 右侧padding(2px)
          } else if (isLastInWord) {
            // 最后一个字符：从 padding 左边缘开始（与前一个字符对齐），右侧留空隙
            finalLeft = '-2px' // 从 padding 左边缘开始，统一基准
            finalWidth = 'calc(100% + 4px - 10px)' // 总宽度减去右侧空隙（10px）
          } else {
            // 中间字符：从 padding 左边缘开始（与前一个字符对齐），延伸到右侧（与下一个字符连接）
            finalLeft = '-2px' // 从 padding 左边缘开始，统一基准
            finalWidth = 'calc(100% + 4px)' // 总宽度：内容(100%) + 左侧padding(2px) + 右侧padding(2px)
          }
          
          return (
            <span 
              className="absolute bottom-[-2px] h-[1.5px] bg-gray-400 pointer-events-none opacity-60"
              style={{ 
                // 确保下划线在 vocab 绿色下划线下方（如果有的话）
                zIndex: hasVocabVisual ? 0 : 1,
                left: finalLeft,
                width: finalWidth
              }}
            />
          )
        })()}
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
          // 🔧 修复：如果匹配到了 notation，使用该 notation 的 token_id（确保显示正确的 vocab example）
          tokenIndex={matchedNotation?.token_id ?? tokenSentenceTokenId}
          onMouseEnter={handleNotationMouseEnter}
          onMouseLeave={handleNotationMouseLeave}
          getVocabExampleForToken={getVocabExampleForToken}
          anchorRef={anchorRef}
        />
      )}
      
      {/* GrammarNotation is now handled at sentence level in SentenceContainer */}
    </span>
  )
}


import React, { useState, useRef, useContext, useCallback, useEffect, useMemo } from 'react'
import TokenSpan from './TokenSpan'
import { getTokenKey } from '../utils/tokenUtils'
import GrammarNotationCard from './notation/GrammarNotationCard'
import GrammarNoteBadge from './notation/GrammarNoteBadge'
import { NotationContext } from '../contexts/NotationContext'
import { useSentenceSelectable } from '../selection/hooks/useSentenceSelectable'
import QuickTranslationTooltip from '../../../components/QuickTranslationTooltip'
import { getQuickTranslation, getSystemLanguage } from '../../../services/translationService'
import { useLanguage, languageNameToCode } from '../../../contexts/LanguageContext'
import { useUiLanguage } from '../../../contexts/UiLanguageContext'
import { useTranslationDebug } from '../../../contexts/TranslationDebugContext'

/**
 * SentenceContainer - Handles sentence-level interactions and renders tokens
 */
export default function SentenceContainer({
  sentence,
  sentenceIndex,
  articleId,
  selectedTokenIds,
  activeSentenceIndex,
  hasExplanation,
  getExplanation,
  hoveredTokenId,
  setHoveredTokenId,
  handleGetExplanation,
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
  currentReadingToken = null, // 当前正在朗读的 token {sentenceIndex, tokenIndex}
  // 🔧 新增：AI详细解释回调
  onAskAI = null,
  // 🔧 新增：高亮范围
  highlightedRange = null,
  // 🔧 新增：Token是否不足（用于禁用AI详细解释按钮）
  isTokenInsufficient = false,
  // 🔧 新增：自动翻译开关状态
  autoTranslationEnabled = false
}) {
  // 从 NotationContext 获取 notation 相关功能
  const notationContext = useContext(NotationContext)
  const {
    hasGrammarNotation,
    getGrammarNotationsForSentence,
    getGrammarRuleById,
    grammarNotations: contextGrammarNotations  // 🔧 获取 grammarNotations 状态，用于触发重新计算
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
  
  // Handle card mouse leave - hide card
  const handleCardMouseLeave = () => {
    setShowGrammarCard(false)
    // 🔧 当 grammar card 隐藏后，如果还在句子内，可以显示整句翻译
    // 注意：这里不立即显示，而是等待句子 hover 状态自然触发
  }

  const handleSentenceClick = async (e) => {
    e.stopPropagation()
    onSentenceClick(sentenceIndex)
  }

  const backgroundStyle = getSentenceBackgroundStyle(sentenceIndex)
  const isInteracting = isSentenceInteracting(sentenceIndex)
  
  // 🔧 获取 sentence_id 用于标识（优先使用数据中的 sentence_id，否则使用索引+1）
  const sentenceId = sentence?.sentence_id || (typeof sentence === 'object' && sentence?.id) || (sentenceIndex + 1)
  
  // Check if this sentence has grammar notations
  // 🔧 使用 useMemo 缓存结果，避免每次渲染都调用函数（可能导致无限循环）
  const hasGrammar = useMemo(() => {
    return hasGrammarNotation ? hasGrammarNotation(sentenceId) : false
  }, [hasGrammarNotation, sentenceId, contextGrammarNotations])  // 🔧 添加 contextGrammarNotations 依赖，确保缓存更新时重新计算
  
  // 🔧 使用 ref 缓存上次的结果，只在结果变化时输出日志
  const lastGrammarNotationsRef = useRef(null)
  
  const grammarNotations = useMemo(() => {
    const result = getGrammarNotationsForSentence ? getGrammarNotationsForSentence(sentenceId) : []
    
    // 🔍 诊断日志：只在结果变化时输出（避免刷屏）
    const lastResult = lastGrammarNotationsRef.current
    const currentNotationIds = result.map(n => n.notation_id || n.grammar_id).sort().join(',')
    const lastNotationIds = lastResult?.notationIds || ''
    
    if (result.length > 0 && (result.length !== lastResult?.count || currentNotationIds !== lastNotationIds)) {
      console.log('🔍 [SentenceContainer] grammarNotations for sentence (结果变化):', {
        sentenceId,
        count: result.length,
        previousCount: lastResult?.count || 0,
        notations: result.map(n => ({
          notation_id: n.notation_id,
          grammar_id: n.grammar_id,
          text_id: n.text_id,
          sentence_id: n.sentence_id
        }))
      })
      
      // 更新缓存
      lastGrammarNotationsRef.current = {
        count: result.length,
        notationIds: currentNotationIds
      }
    }
    
    return result
  }, [getGrammarNotationsForSentence, sentenceId, contextGrammarNotations])  // 🔧 添加 contextGrammarNotations 依赖，确保缓存更新时重新计算
  
  // 🔧 移除调试日志，避免刷屏（如果需要调试，可以使用条件判断）
  // if (grammarNotations.length > 0) {
  //   console.log('🔍 [SentenceContainer] Grammar notations for sentence', sentenceId, ':', grammarNotations)
  // }

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
  
  // 🔧 整句翻译相关状态
  const { selectedLanguage } = useLanguage()
  const { uiLanguage } = useUiLanguage() // 🔧 获取 UI 语言设置
  // 清除调试日志
  const [sentenceTranslation, setSentenceTranslation] = useState(null)
  const [showSentenceTranslation, setShowSentenceTranslation] = useState(false)
  const [isLoadingSentenceTranslation, setIsLoadingSentenceTranslation] = useState(false)
  const sentenceTranslationTimerRef = useRef(null)
  const sentenceTranslationQueryRef = useRef(null)
  const [isHoveringToken, setIsHoveringToken] = useState(false)
  const isHoveringTokenRef = useRef(false) // 使用 ref 来跟踪，避免闭包问题
  
  // 获取源语言和目标语言
  const sourceLang = useMemo(() => {
    return sentence?.language_code || 'de' // 默认德语
  }, [sentence])
  
  const targetLang = useMemo(() => {
    // 🔧 优先使用 UI 语言设置（用户设置的界面语言）
    // 如果 UI 语言为英语，自动翻译的目标语言也应该是英语
    if (uiLanguage === 'en') {
      // 如果源语言也是英语，则翻译成中文
      return sourceLang === 'en' ? 'zh' : 'en'
    }
    
    // 如果 UI 语言为中文，使用原来的逻辑（基于学习语言或系统语言）
    const globalLang = languageNameToCode(selectedLanguage)
    const preferredLang = globalLang || getSystemLanguage()
    
    if (preferredLang === sourceLang) {
      const systemLang = getSystemLanguage()
      if (systemLang !== sourceLang) {
        return systemLang
      } else {
        return sourceLang === 'en' ? 'zh' : 'en'
      }
    }
    return preferredLang
  }, [uiLanguage, selectedLanguage, sourceLang])
  
  // 获取句子完整文本
  const sentenceText = useMemo(() => {
    if (sentence?.sentence_body) {
      return sentence.sentence_body
    }
    if (Array.isArray(sentence?.tokens)) {
      return sentence.tokens
        .map(token => typeof token === 'string' ? token : (token?.token_body || token?.token || ''))
        .join('')
    }
    return ''
  }, [sentence])
  
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
  
  // 🔧 查询整句翻译
  const querySentenceTranslation = useCallback(async (text) => {
    if (!text || text.trim().length === 0) {
      return
    }
    
    // 取消之前的查询
    if (sentenceTranslationQueryRef.current) {
      sentenceTranslationQueryRef.current = null
    }
    
    const currentQuery = {}
    sentenceTranslationQueryRef.current = currentQuery
    
    // 设置加载状态
    setIsLoadingSentenceTranslation(true)
    setShowSentenceTranslation(true)
    
    // 🔧 关闭翻译调试日志
    // const debugLogger = (level, message, data) => {
    //   addDebugLog(level, `[SentenceContainer] ${message}`, data)
    // }
    
    try {
      const finalTargetLang = targetLang || 'en'
      // 🔧 关闭翻译调试日志
      // const logData = { text, sourceLang, targetLang: finalTargetLang }
      // debugLogger('info', `开始查询整句翻译: "${text.substring(0, 50)}..."`, logData)
      
      // 🔧 句子查询：直接使用翻译API（跳过词典查询）
      const translation = await getQuickTranslation(text, sourceLang, finalTargetLang, {
        // debugLogger, // 🔧 关闭调试日志
        isWord: false, // 明确指定为句子查询
        useDictionary: false // 句子不使用词典API
      })
      
      // 🔧 关闭翻译调试日志
      // const resultData = { text: text.substring(0, 50) + '...', translation }
      // debugLogger(translation ? 'success' : 'warning', `整句翻译查询完成`, resultData)
      
      // 检查查询是否已被取消
      if (sentenceTranslationQueryRef.current === currentQuery) {
        setSentenceTranslation(translation)
        setIsLoadingSentenceTranslation(false)
        // 即使没有翻译结果，也保持显示状态（显示加载失败或空状态）
        setShowSentenceTranslation(true)
        sentenceTranslationQueryRef.current = null
      }
    } catch (error) {
      // 🔧 关闭翻译调试日志
      // const errorData = { text: text.substring(0, 50) + '...', error: error.message }
      // debugLogger('error', `整句翻译查询失败`, errorData)
      
      if (sentenceTranslationQueryRef.current === currentQuery) {
        setSentenceTranslation(null)
        setIsLoadingSentenceTranslation(false)
        setShowSentenceTranslation(false)
        sentenceTranslationQueryRef.current = null
      }
    }
  }, [sourceLang, targetLang])
  
  // 🔧 清理整句翻译定时器
  const clearSentenceTranslationTimer = useCallback(() => {
    if (sentenceTranslationTimerRef.current) {
      clearTimeout(sentenceTranslationTimerRef.current)
      sentenceTranslationTimerRef.current = null
    }
  }, [])
  
  // 🔧 清理整句翻译状态
  const clearSentenceTranslation = useCallback(() => {
    clearSentenceTranslationTimer()
    setShowSentenceTranslation(false)
    setSentenceTranslation(null)
    setIsLoadingSentenceTranslation(false)
    sentenceTranslationQueryRef.current = null
  }, [clearSentenceTranslationTimer])
  
  // 🔧 处理句子 hover
  const handleSentenceHover = (e) => {
    if (shouldShowSegmentationUnderline) {
      setIsHovered(true)
    }
    selOnEnter()
    handleSentenceMouseEnter(e)
    
    // 🔧 重置 token hover 状态（因为鼠标现在在 sentence container 上，不在 token 上）
    // 这样可以确保从 token 移动到 sentence container 其他区域时能显示整句翻译
    setIsHoveringToken(false)
    isHoveringTokenRef.current = false
    
    // 🔧 延迟显示整句翻译（如果 grammar card 没有显示且自动翻译已开启）
    if (sentenceText.trim().length > 0 && !showGrammarCard && autoTranslationEnabled) {
      clearSentenceTranslationTimer()
      sentenceTranslationTimerRef.current = setTimeout(() => {
        // 再次检查，确保没有新的 token hover 且 grammar card 没有显示且自动翻译已开启
        if (!isHoveringTokenRef.current && !showGrammarCard && autoTranslationEnabled) {
          querySentenceTranslation(sentenceText)
        }
      }, 250)
    }
  }
  
  const handleSentenceHoverLeave = (e) => {
    if (shouldShowSegmentationUnderline) {
      setIsHovered(false)
    }
    selOnLeave()
    handleSentenceMouseLeave(e)
    
    // 🔧 清理整句翻译
    clearSentenceTranslation()
    setIsHoveringToken(false)
    isHoveringTokenRef.current = false
  }
  
  // 🔧 处理 token hover 进入
  const handleTokenHoverEnter = useCallback(() => {
    setIsHoveringToken(true)
    isHoveringTokenRef.current = true
    clearSentenceTranslation() // 当 hover token 时，隐藏整句翻译
  }, [clearSentenceTranslation])
  
  // 🔧 处理 token hover 离开
  const handleTokenHoverLeave = useCallback(() => {
    setIsHoveringToken(false)
    isHoveringTokenRef.current = false
    // 如果还在句子内且 grammar card 没有显示且自动翻译已开启，延迟显示整句翻译
    if (isHovered && sentenceText.trim().length > 0 && !showGrammarCard && autoTranslationEnabled) {
      clearSentenceTranslationTimer()
      sentenceTranslationTimerRef.current = setTimeout(() => {
        if (!isHoveringTokenRef.current && !showGrammarCard && autoTranslationEnabled) {
          querySentenceTranslation(sentenceText)
        }
      }, 250)
    }
  }, [isHovered, sentenceText, clearSentenceTranslationTimer, querySentenceTranslation, showGrammarCard, autoTranslationEnabled])
  
  // 🔧 重新定义 handleCardMouseEnter，确保可以访问 clearSentenceTranslation
  const handleCardMouseEnterWithTranslation = useCallback(() => {
    if (hideCardTimerRef.current) {
      clearTimeout(hideCardTimerRef.current)
      hideCardTimerRef.current = null
    }
    // 🔧 当 grammar card 显示时，确保整句翻译被隐藏
    clearSentenceTranslation()
  }, [clearSentenceTranslation])
  
  // 🔧 当自动翻译关闭时，清除整句翻译
  useEffect(() => {
    if (!autoTranslationEnabled) {
      clearSentenceTranslation()
    }
  }, [autoTranslationEnabled, clearSentenceTranslation])
  
  // 组件卸载时清理
  useEffect(() => {
    return () => {
      clearSentenceTranslationTimer()
      sentenceTranslationQueryRef.current = null
    }
  }, [clearSentenceTranslationTimer])
  
  return (
    <div 
      ref={sentenceRef}
      key={`s-${sentenceIndex}`} 
      className={`select-none relative transition-all duration-200 ${backgroundStyle} ${selectionSentenceClass}`}
      data-sentence="1"
      data-sentence-id={sentenceId}
      data-sentence-index={sentenceIndex}
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
        
        // 🔧 检查当前 token 是否是正在朗读的 token
        const isCurrentlyReading = currentReadingToken && 
          currentReadingToken.sentenceIndex === sentenceIndex && 
          currentReadingToken.tokenIndex === tokenIndex
        
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
        
        const tokenKey = getTokenKey(sentenceIndex, token, tokenIndex)

        return (
          <React.Fragment key={tokenKey}>
            <TokenSpan
              token={token}
              tokenIdx={tokenIndex}
              sentenceIdx={sentenceIndex}
              articleId={articleId}
              selectedTokenIds={selectedTokenIds}
              activeSentenceIndex={activeSentenceIndex}
              hasExplanation={hasExplanation}
              getExplanation={getExplanation}
              hoveredTokenId={hoveredTokenId}
              setHoveredTokenId={setHoveredTokenId}
              isTokenInsufficient={isTokenInsufficient}
              handleGetExplanation={handleGetExplanation}
              onTokenMouseLeave={handleTokenHoverLeave}
              addSingle={addSingle}
              isTokenAsked={isTokenAsked}
              markAsAsked={markAsAsked}
              highlightedRange={highlightedRange}
              getNotationContent={getNotationContent}
              setNotationContent={setNotationContent}
              // 🔧 新增：分词下划线相关 props
              showSegmentationUnderline={shouldShowUnderline}
              wordTokenInfo={wordTokenInfo}
              // 🔧 新增：朗读高亮相关 props
              isCurrentlyReading={isCurrentlyReading}
              // 🔧 新增：AI详细解释回调
              onAskAI={onAskAI}
            />
            {/* 🔧 在不同 word token 之间添加空格（只在 hover 时显示） */}
            {shouldAddSpaceAfter && (
              <span key={`space-${sentenceIndex}-${tokenIndex}`} className="inline-block w-2" aria-hidden="true" />
            )}
          </React.Fragment>
        )
      })}
      
      {/* 🔧 整句翻译 tooltip - 只在自动翻译开启、没有 hover token 且没有显示 grammar notation 时显示 */}
      {autoTranslationEnabled && showSentenceTranslation && !isHoveringToken && !showGrammarCard && (
        <QuickTranslationTooltip
          word={sentenceText}
          translation={sentenceTranslation}
          isVisible={showSentenceTranslation}
          anchorRef={sentenceRef}
          position="bottom"
          showWord={false}
          isLoading={isLoadingSentenceTranslation}
          fullWidth={true}
        />
      )}
      
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
                  // 🔧 传递句子的位置信息，让 GrammarNotationCard 自己决定显示位置
                  setGrammarCardPosition({ 
                    top: rect.bottom + 8, // 默认显示在下方
                    left: rect.left, 
                    right: 'auto',
                    sentenceTop: rect.top, // 🔧 传递句子顶部位置
                    sentenceBottom: rect.bottom // 🔧 传递句子底部位置
                  })
                }
                setShowGrammarCard(true)
                // 🔧 当显示 grammar notation 时，隐藏整句翻译
                clearSentenceTranslation()
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
            onMouseEnter={handleCardMouseEnterWithTranslation}
            onMouseLeave={handleCardMouseLeave}
            cachedGrammarRules={grammarNotations}
            getGrammarRuleById={getGrammarRuleById}
          />
        </>
      )}
    </div>
  )
}

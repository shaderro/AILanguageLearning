import { useState, useEffect, useLayoutEffect, useCallback, useRef } from 'react'
import { apiService } from '../../../../services/api'
import { colors } from '../../../../design-tokens'
import { useUIText } from '../../../../i18n/useUIText'

// 解析和格式化解释文本
const parseExplanation = (text) => {
  if (!text) return ''
  
  let cleanText = text
  
  // 1. 处理字典格式的字符串（如 "{'explanation': '...'}" 或 '{"explanation": "..."}'）
  if (text.includes("'explanation'") || text.includes('"explanation"')) {
    try {
      // 尝试解析 JSON 格式
      const jsonMatch = text.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        const jsonStr = jsonMatch[0]
        // 先尝试标准 JSON 解析
        try {
          const parsed = JSON.parse(jsonStr)
          cleanText = parsed.explanation || parsed.definition || text
        } catch (e) {
          // 如果不是标准 JSON，尝试处理 Python 字典格式（单引号）
          // 使用更智能的方法：只替换键和字符串分隔符的单引号
          // 先尝试直接提取 explanation 字段的值（支持多行和转义字符）
          // 🔧 修复：处理被截断的 JSON（缺少结束引号或右大括号）
          // 先尝试完整匹配（有结束引号）
          let explanationMatch = text.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*?)['"]\s*[,}]/s)
          if (!explanationMatch) {
            // 如果完整匹配失败，尝试匹配到字符串末尾（处理被截断的 JSON）
            explanationMatch = text.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*?)(?:['"]\s*[,}]|$)/s)
          }
          if (explanationMatch) {
            cleanText = explanationMatch[1]
              .replace(/\\n/g, '\n')  // 处理转义的换行符
              .replace(/\\'/g, "'")   // 处理转义的单引号
              .replace(/\\"/g, '"')   // 处理转义的双引号
          } else {
            // 如果正则匹配失败，尝试将单引号替换为双引号（简单处理）
            const normalized = jsonStr.replace(/'/g, '"')
            try {
              const parsed = JSON.parse(normalized)
              cleanText = parsed.explanation || parsed.definition || text
            } catch (e2) {
              // 如果还是失败，尝试从截断的 JSON 中提取 explanation 值
              // 查找 "explanation": " 之后的所有内容（直到字符串结束或找到引号）
              const truncatedMatch = text.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*)/)
              if (truncatedMatch) {
                cleanText = truncatedMatch[1]
                  .replace(/\\n/g, '\n')
                  .replace(/\\'/g, "'")
                  .replace(/\\"/g, '"')
              } else {
                // 如果还是失败，使用原始文本
                cleanText = text
              }
            }
          }
        }
      } else {
        // 🔧 修复：如果没有找到完整的 JSON 对象（可能被截断），尝试直接提取 explanation 字段
        const truncatedMatch = text.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*)/)
        if (truncatedMatch) {
          cleanText = truncatedMatch[1]
            .replace(/\\n/g, '\n')
            .replace(/\\'/g, "'")
            .replace(/\\"/g, '"')
        }
      }
    } catch (e) {
      // 解析失败，使用原始文本
    }
  }
  
  // 2. 处理代码块格式（```json ... ```）
  if (cleanText.includes('```json') && cleanText.includes('```')) {
    try {
      const jsonMatch = cleanText.match(/```json\n(.*?)\n```/s)
      if (jsonMatch) {
        const jsonStr = jsonMatch[1]
        const parsed = JSON.parse(jsonStr)
        cleanText = parsed.explanation || parsed.definition || cleanText
      }
    } catch (e) {
      // 解析失败，继续使用 cleanText
    }
  }
  
  // 3. 清理多余的转义字符和格式化
  // 将 \n 转换为实际的换行
  cleanText = cleanText.replace(/\\n/g, '\n')
  // 移除多余的空白行（连续两个以上的换行符）
  cleanText = cleanText.replace(/\n{3,}/g, '\n\n')
  // 去除首尾空白
  cleanText = cleanText.trim()
  
  return cleanText
}

/**
 * GrammarNotationCard - 语法注释卡片组件（从 components/ 迁移至 notation/）
 */
export default function GrammarNotationCard({ 
  isVisible = false, 
  textId = null,
  sentenceId = null,
  position = { top: 0, left: 0, right: 'auto' },
  onClose = null,
  onMouseEnter = null,
  onMouseLeave = null,
  cachedGrammarRules = null,
  getGrammarRuleById = null
}) {
  const t = useUIText()
  const [grammarRules, setGrammarRules] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [articleRect, setArticleRect] = useState(null)
  const cardRef = useRef(null)
  const [cardHeight, setCardHeight] = useState(null)

  useEffect(() => {
    if (isVisible && textId && sentenceId) {
      if (cachedGrammarRules && getGrammarRuleById) {
        // 🔍 诊断日志：检查传入的 cachedGrammarRules
        console.log('🔍 [GrammarNotationCard] 处理 cachedGrammarRules:', {
          textId,
          sentenceId,
          cachedGrammarRulesCount: cachedGrammarRules?.length || 0,
          cachedGrammarRules: cachedGrammarRules?.map(n => ({
            notation_id: n.notation_id,
            grammar_id: n.grammar_id,
            text_id: n.text_id,
            sentence_id: n.sentence_id
          }))
        })
        
        const rules = cachedGrammarRules.map(notation => {
          const rule = getGrammarRuleById(notation.grammar_id)
          if (!rule) {
            console.warn(`⚠️ [GrammarNotationCard] Grammar rule not found in cache for grammar_id=${notation.grammar_id}`)
            return null
          }
          let contextExplanation = notation.context_explanation || notation.explanation_context || ''
          if (rule.examples && Array.isArray(rule.examples)) {
            const matchingExample = rule.examples.find(ex => 
              Number(ex.text_id) === Number(notation.text_id) && 
              Number(ex.sentence_id) === Number(notation.sentence_id)
            )
            if (matchingExample) {
              contextExplanation = matchingExample.explanation_context || ''
            }
          }
          const result = {
            ...rule,
            context_explanation: contextExplanation,
            notation_id: notation.notation_id || `${notation.text_id}:${notation.sentence_id}`,
            marked_token_ids: notation.marked_token_ids || [],
            grammar_id: notation.grammar_id,
            text_id: notation.text_id,
            sentence_id: notation.sentence_id
          }
          return result
        }).filter(Boolean)
        
        console.log('✅ [GrammarNotationCard] 处理后的 rules:', {
          rulesCount: rules.length,
          rules: rules.map(r => ({
            rule_id: r.rule_id,
            grammar_id: r.grammar_id,
            rule_name: r.rule_name,
            notation_id: r.notation_id
          }))
        })
        
        setGrammarRules(rules)
        setIsLoading(false)
        setError(null)
      } else {
        setIsLoading(true)
        setError(null)
        fetchSentenceGrammarRules(textId, sentenceId)
          .then(rules => {
            setGrammarRules(rules)
            setIsLoading(false)
          })
          .catch(error => {
            console.error('❌ [GrammarNotationCard] Error fetching sentence grammar rules:', error)
            setError(error.message || 'Failed to load grammar rules')
            setIsLoading(false)
          })
      }
    } else {
      setGrammarRules([])
      setError(null)
    }
  }, [isVisible, textId, sentenceId, cachedGrammarRules, getGrammarRuleById])

  const measureArticleRect = useCallback(() => {
    if (typeof document === 'undefined') return
    // ArticleViewer 的滚动容器：`className="... article-scrollbar"`
    const el = document.querySelector('.article-scrollbar')
    if (!el) return
    const rect = el.getBoundingClientRect()
    if (!rect || !rect.width) return
    setArticleRect({
      left: rect.left,
      width: rect.width,
    })
  }, [])

  // 打开 tooltip 时测量 article view 宽度，并在 resize / scroll 时更新
  useLayoutEffect(() => {
    if (!isVisible) {
      setArticleRect(null)
      return
    }
    measureArticleRect()
    window.addEventListener('resize', measureArticleRect)
    window.addEventListener('scroll', measureArticleRect, true)
    return () => {
      window.removeEventListener('resize', measureArticleRect)
      window.removeEventListener('scroll', measureArticleRect, true)
    }
  }, [isVisible, measureArticleRect])

  const fetchSentenceGrammarRules = async (textId, sentenceId) => {
    try {
      const response = await apiService.getSentenceGrammarRules(textId, sentenceId)
      if (response && response.data) {
        if (Array.isArray(response.data)) return response.data
        if (response.data.grammar_rules) return response.data.grammar_rules
        if (response.data.rule_id) return [response.data]
        if (response.data.grammar_id) {
          try {
            const ruleResponse = await apiService.getGrammarById(response.data.grammar_id)
            if (ruleResponse && ruleResponse.data) {
              return [{
                ...ruleResponse.data,
                context_explanation: response.data.context_explanation || '',
                notation_id: response.data.notation_id || `${response.data.text_id}:${response.data.sentence_id}`,
                marked_token_ids: response.data.marked_token_ids || []
              }]
            }
          } catch (ruleError) {
            console.warn(`Failed to fetch grammar rule ${response.data.grammar_id}:`, ruleError)
          }
        }
      }
      return []
    } catch (error) {
      console.error('Error in fetchSentenceGrammarRules:', error)
      try {
        const notationsResponse = await apiService.getGrammarNotations(textId)
        const notations = Array.isArray(notationsResponse) ? notationsResponse : 
                         (notationsResponse?.data && Array.isArray(notationsResponse.data) ? notationsResponse.data : [])
        const sentenceNotations = notations.filter(notation => 
          notation.sentence_id === sentenceId
        )
        const grammarRules = []
        for (const notation of sentenceNotations) {
          try {
            const ruleResponse = await apiService.getGrammarById(notation.grammar_id)
            if (ruleResponse && ruleResponse.data) {
              grammarRules.push({
                ...ruleResponse.data,
                context_explanation: notation.context_explanation || '',
                notation_id: notation.notation_id
              })
            }
          } catch (ruleError) {
            console.warn(`Failed to fetch grammar rule ${notation.grammar_id}:`, ruleError)
          }
        }
        return grammarRules
      } catch (fallbackError) {
        console.error('Fallback method also failed:', fallbackError)
        throw fallbackError
      }
    }
  }

  // 🔧 测量 tooltip 实际高度，用于动态调整位置
  useLayoutEffect(() => {
    if (isVisible && cardRef.current) {
      const h = cardRef.current.getBoundingClientRect().height
      if (h && h !== cardHeight) {
        setCardHeight(h)
      }
    }
  }, [isVisible, cardHeight, grammarRules.length]) // 当 grammarRules 数量变化时重新测量

  // 🔧 动态计算位置：如果 tooltip 会超出视口底部，则显示在句子上方
  const [finalPosition, setFinalPosition] = useState(position)
  
  useEffect(() => {
    if (!isVisible || !position.top) {
      setFinalPosition(position)
      return
    }
    
    const calculatePosition = () => {
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight
      const actualHeight = cardHeight || 300 // 使用实际高度，如果没有则使用估算值
      const spaceBelow = viewportHeight - position.top
      const sentenceTop = position.sentenceTop // 从 position 中获取句子顶部位置
      
      // 🔧 如果下方空间不够（无法完整显示 tooltip），且上方有足够空间，则显示在上方
      if (spaceBelow < actualHeight && sentenceTop && sentenceTop >= actualHeight) {
        // 显示在句子上方（tooltip 底部与句子顶部对齐，留 8px 间距）
        setFinalPosition({
          ...position,
          top: sentenceTop - actualHeight - 8
        })
      } else {
        // 默认显示在句子下方
        setFinalPosition(position)
      }
    }
    
    calculatePosition()
    
    // 🔧 监听滚动和窗口大小变化，重新计算位置
    window.addEventListener('scroll', calculatePosition, true)
    window.addEventListener('resize', calculatePosition)
    
    return () => {
      window.removeEventListener('scroll', calculatePosition, true)
      window.removeEventListener('resize', calculatePosition)
    }
  }, [isVisible, position, cardHeight])

  if (!isVisible) return null

  // 🔧 tooltip 宽度：与 article view 宽度保持一致（直接测量 .article-scrollbar）
  const TOOLTIP_MAX_WIDTH = articleRect?.width ? `${Math.floor(articleRect.width)}px` : '800px'
  const TOOLTIP_MAX_HEIGHT = '200px' // 🔧 改为原来的 1/3 (600px / 3 = 200px)，超出时使用滚动
  const TOOLTIP_INNER_MAX_HEIGHT = 'calc(200px - 32px)' // 🔧 减去上下 padding (16px * 2)

  return (
    <div 
      ref={cardRef}
      className="fixed bg-white border border-gray-300 rounded-lg shadow-lg z-50 notation-card"
      style={{
        top: `${finalPosition.top}px`,
        // 如果测量到了 articleRect，则强制与 article view 左对齐
        left: articleRect?.left != null ? `${Math.floor(articleRect.left)}px` : (finalPosition.left !== 'auto' ? `${finalPosition.left}px` : 'auto'),
        right: finalPosition.right !== 'auto' ? `${finalPosition.right}px` : 'auto',
        // 与 article view 对齐时，不需要 transform
        transform: articleRect?.left != null ? 'none' : (position.left !== 'auto' ? 'none' : 'translateX(-50%)'),
        width: articleRect?.width ? `${Math.floor(articleRect.width)}px` : '100%',
        maxWidth: TOOLTIP_MAX_WIDTH,
        minWidth: '300px',
        maxHeight: TOOLTIP_MAX_HEIGHT,
        minHeight: '80px',
        height: 'auto',
        padding: '16px',
        boxSizing: 'border-box',
        display: 'block'
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={(e) => e.stopPropagation()}
    >
      <div 
        style={{ 
          maxHeight: TOOLTIP_INNER_MAX_HEIGHT,
          height: 'auto',
          overflowY: 'auto',
          overflowX: 'hidden'
        }}
      >
        {isLoading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px 0' }}>
            <div style={{ 
              animation: 'spin 1s linear infinite',
              borderRadius: '50%',
              height: '24px',
              width: '24px',
              borderBottom: `2px solid ${colors.primary[600]}`
            }}></div>
            <span style={{ marginLeft: '8px', color: '#6b7280' }}>加载中...</span>
          </div>
        )}

        {error && (
          <div style={{ color: '#ef4444', fontSize: '14px', padding: '8px 0' }}>
            加载失败: {error}
          </div>
        )}

        {!isLoading && !error && grammarRules.length === 0 && (
          <div style={{ color: '#6b7280', fontSize: '14px', padding: '8px 0' }}>
            该句子暂无语法注释
          </div>
        )}

        {!isLoading && !error && grammarRules.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {grammarRules.map((rule, index) => {
              // 🔧 构建语法规则详情页面的 URL
              const grammarId = rule.rule_id || rule.grammar_id
              const detailUrl = grammarId 
                ? `${window.location.origin}${window.location.pathname}?page=grammarDemo&grammarId=${grammarId}`
                : null
              
              // 🔧 处理点击事件：在新标签页打开详情页面
              const handleTitleClick = (e) => {
                e.preventDefault()
                e.stopPropagation()
                if (detailUrl) {
                  window.open(detailUrl, '_blank', 'noopener,noreferrer')
                }
              }
              
              return (
                <div 
                  key={rule.notation_id || `grammar-${rule.rule_id || rule.grammar_id}-${index}`} 
                  style={{ 
                    borderBottom: index < grammarRules.length - 1 ? '1px solid #e5e7eb' : 'none',
                    paddingBottom: index < grammarRules.length - 1 ? '20px' : '0'
                  }}
                >
                  {/* 🔧 可点击的标题：绿色下划线幽灵按钮 */}
                  <button
                    onClick={handleTitleClick}
                    disabled={!detailUrl}
                    style={{ 
                      background: 'transparent',
                      border: 'none',
                      padding: 0,
                      margin: 0,
                      cursor: detailUrl ? 'pointer' : 'default',
                      textAlign: 'left',
                      fontWeight: '600', 
                      color: colors.primary[600], 
                      marginBottom: '8px',
                      fontSize: '16px',
                      textDecoration: 'underline',
                      textDecorationColor: '#10b981', // 绿色下划线
                      textDecorationThickness: '2px',
                      textUnderlineOffset: '4px',
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      if (detailUrl) {
                        e.target.style.color = colors.primary[700]
                        e.target.style.textDecorationColor = '#059669' // 深绿色
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (detailUrl) {
                        e.target.style.color = colors.primary[600]
                        e.target.style.textDecorationColor = '#10b981' // 恢复绿色
                      }
                    }}
                  >
                    {rule.rule_name || rule.name || t('语法规则')}
                  </button>
                  
                  {/* 🔧 只显示 context_explanation */}
                  {rule.context_explanation ? (
                    <div style={{ 
                      fontSize: '14px', 
                      color: '#374151',
                      marginTop: '8px',
                      paddingLeft: '8px', 
                      borderLeft: '2px solid #dcfce7',
                      padding: '4px 0 4px 8px',
                      whiteSpace: 'pre-wrap',
                      lineHeight: '1.6'
                    }}>
                      {parseExplanation(rule.context_explanation || '')}
                    </div>
                  ) : (
                    <div style={{ 
                      fontSize: '14px', 
                      color: '#9ca3af',
                      fontStyle: 'italic',
                      marginTop: '8px',
                      paddingLeft: '8px', 
                      borderLeft: '2px solid #dcfce7',
                      padding: '4px 0 4px 8px'
                    }}>
                      {t('暂无上下文解释')}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}



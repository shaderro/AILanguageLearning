import { useState, useEffect } from 'react'
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

  useEffect(() => {
    if (isVisible && textId && sentenceId) {
      if (cachedGrammarRules && getGrammarRuleById) {
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

  if (!isVisible) return null

  return (
    <div 
      className="fixed bg-white border border-gray-300 rounded-lg shadow-lg z-50 notation-card"
      style={{
        top: `${position.top}px`,
        left: position.left !== 'auto' ? `${position.left}px` : 'auto',
        right: position.right !== 'auto' ? `${position.right}px` : 'auto',
        transform: position.left !== 'auto' ? 'none' : 'translateX(-50%)',
        width: '100%',
        maxWidth: '1200px',  // ✅ 增加最大宽度：从 800px 增加到 1200px
        minWidth: '300px',
        maxHeight: '600px',  // ✅ 增加最大高度：从 200px 增加到 600px，避免内容截断
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
          maxHeight: 'calc(600px - 16px - 16px)',  // ✅ 同步更新内部容器最大高度
          height: 'auto',
          overflowY: 'auto',
          overflowX: 'hidden',
          wordWrap: 'break-word',  // ✅ 确保长单词可以换行
          wordBreak: 'break-word'  // ✅ 防止文本溢出
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
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {grammarRules.map((rule, index) => (
              <div 
                key={rule.notation_id || index} 
                style={{ 
                  borderBottom: index < grammarRules.length - 1 ? '1px solid #f3f4f6' : 'none',
                  paddingBottom: '12px'
                }}
              >
                <div style={{ 
                  fontWeight: '600', 
                  color: colors.primary[600], 
                  marginBottom: '8px',
                  fontSize: '16px'
                }}>
                  {rule.rule_name || rule.name}
                </div>
                <div style={{ fontSize: '14px', color: '#374151', marginBottom: '8px' }}>
                  <span style={{ fontWeight: '500' }}>{t('规则解释:')}</span>
                  <div style={{ 
                    marginTop: '4px', 
                    paddingLeft: '8px', 
                    borderLeft: `2px solid ${colors.primary[100]}`,
                    padding: '4px 0 4px 8px',
                    whiteSpace: 'pre-wrap',
                    wordWrap: 'break-word',  // ✅ 确保长文本可以换行
                    wordBreak: 'break-word',  // ✅ 防止文本溢出
                    overflowWrap: 'break-word'  // ✅ 额外的换行保护
                  }}>
                    {parseExplanation(rule.rule_summary || rule.explanation || '')}
                  </div>
                </div>
                {rule.context_explanation && (
                  <div style={{ fontSize: '14px', color: '#6b7280' }}>
                    <span style={{ fontWeight: '500' }}>{t('上下文解释:')}</span>
                    <div style={{ 
                      marginTop: '4px', 
                      paddingLeft: '8px', 
                      borderLeft: '2px solid #dcfce7',
                      padding: '4px 0 4px 8px',
                      whiteSpace: 'pre-wrap',
                      wordWrap: 'break-word',  // ✅ 确保长文本可以换行
                      wordBreak: 'break-word',  // ✅ 防止文本溢出
                      overflowWrap: 'break-word'  // ✅ 额外的换行保护
                    }}>
                      {parseExplanation(rule.context_explanation || '')}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}



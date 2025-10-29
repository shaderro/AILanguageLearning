import { useState, useEffect } from 'react'
import { apiService } from '../../../services/api'

/**
 * GrammarNotationCard - 语法注释卡片组件
 * 
 * Props:
 * - isVisible: 是否显示卡片
 * - textId: 文章ID
 * - sentenceId: 句子ID
 * - position: 卡片位置 { top, left, right }
 * - onClose: 关闭回调
 * - cachedGrammarRules: 缓存的语法规则数据（可选）
 * - getGrammarRuleById: 获取语法规则详情的函数（可选）
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
  const [grammarRules, setGrammarRules] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (isVisible && textId && sentenceId) {
      // 优先使用缓存数据
      if (cachedGrammarRules && getGrammarRuleById) {
        // 移除详细日志（已通过测试，缓存功能正常）
        
        const rules = cachedGrammarRules.map(notation => {
          const rule = getGrammarRuleById(notation.grammar_id)
          
          if (!rule) {
            console.warn(`⚠️ [GrammarNotationCard] Grammar rule not found in cache for grammar_id=${notation.grammar_id}`)
            return null
          }
          
          // 从 grammar rule 的 examples 中查找匹配当前 (text_id, sentence_id) 的 example
          let contextExplanation = notation.context_explanation || notation.explanation_context || ''
          
          if (rule.examples && Array.isArray(rule.examples)) {
            const matchingExample = rule.examples.find(ex => 
              Number(ex.text_id) === Number(notation.text_id) && 
              Number(ex.sentence_id) === Number(notation.sentence_id)
            )
            
            if (matchingExample) {
              // 解析 explanation_context（可能是JSON字符串）
              let explanationText = matchingExample.explanation_context || ''
              try {
                const parsed = JSON.parse(explanationText)
                if (parsed && parsed.explanation) {
                  explanationText = parsed.explanation
                }
              } catch (e) {
                // 如果不是JSON，直接使用原字符串
              }
              
              contextExplanation = explanationText
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
        // 回退到API调用（缓存未命中时的fallback）
        console.log(`🔍 [GrammarNotationCard] Using API fallback for sentence ${sentenceId} (cache miss)`)
        setIsLoading(true)
        setError(null)
        
        fetchSentenceGrammarRules(textId, sentenceId)
          .then(rules => {
            console.log(`✅ [GrammarNotationCard] Fetched ${rules.length} grammar rules from API:`, rules)
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

  // 获取句子的语法规则
  const fetchSentenceGrammarRules = async (textId, sentenceId) => {
    try {
      // 使用新的API方法直接获取句子的语法规则
      const response = await apiService.getSentenceGrammarRules(textId, sentenceId)
      
      if (response && response.data) {
        // 如果返回的是语法规则列表
        if (Array.isArray(response.data)) {
          return response.data
        }
        
        // 如果返回的是包含语法规则的对象
        if (response.data.grammar_rules) {
          return response.data.grammar_rules
        }
        
        // 如果返回的是单个语法规则
        if (response.data.rule_id) {
          return [response.data]
        }
        
        // 如果返回的是GrammarNotation对象，需要根据grammar_id获取语法规则详情
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
      // 如果新API失败，回退到旧方法
      try {
        const notationsResponse = await apiService.getGrammarNotations(textId)
        const notations = Array.isArray(notationsResponse) ? notationsResponse : 
                         (notationsResponse?.data && Array.isArray(notationsResponse.data) ? notationsResponse.data : [])
        
        // 过滤出当前句子的语法标注
        const sentenceNotations = notations.filter(notation => 
          notation.sentence_id === sentenceId
        )
        
        // 获取每个语法规则的详细信息
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
      className="fixed bg-white border border-gray-300 rounded-lg shadow-lg z-50"
      style={{
        top: `${position.top}px`,
        left: position.left !== 'auto' ? `${position.left}px` : 'auto',
        right: position.right !== 'auto' ? `${position.right}px` : 'auto',
        transform: position.left !== 'auto' ? 'none' : 'translateX(-50%)',
        width: '100%',
        maxWidth: '800px',
        minWidth: '300px',
        maxHeight: '200px',
        minHeight: '80px',
        height: 'auto',
        padding: '16px',
        boxSizing: 'border-box',
        display: 'block'
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* 标题栏 - 固定高度 */}
      <div 
        style={{ 
          height: '40px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px',
          flexShrink: '0'
        }}
      >
        <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', margin: '0' }}>语法注释</h3>
        <button
          onClick={onClose}
          style={{ 
            background: 'none',
            border: 'none',
            fontSize: '20px',
            color: '#9ca3af',
            cursor: 'pointer',
            padding: '0',
            lineHeight: '1'
          }}
          onMouseEnter={(e) => e.target.style.color = '#4b5563'}
          onMouseLeave={(e) => e.target.style.color = '#9ca3af'}
          aria-label="关闭"
        >
          ×
        </button>
      </div>

      {/* 内容区域 - 可滚动 */}
      <div 
        style={{ 
          maxHeight: 'calc(200px - 16px - 16px - 40px - 12px)',
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
              borderBottom: '2px solid #3b82f6'
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
                {/* 规则名称 */}
                <div style={{ 
                  fontWeight: '600', 
                  color: '#2563eb', 
                  marginBottom: '8px',
                  fontSize: '16px'
                }}>
                  {rule.rule_name || rule.name}
                </div>
                
                {/* 规则解释 */}
                <div style={{ fontSize: '14px', color: '#374151', marginBottom: '8px' }}>
                  <span style={{ fontWeight: '500' }}>规则解释:</span>
                  <div style={{ 
                    marginTop: '4px', 
                    paddingLeft: '8px', 
                    borderLeft: '2px solid #dbeafe',
                    padding: '4px 0 4px 8px'
                  }}>
                    {rule.rule_summary || rule.explanation}
                  </div>
                </div>
                
                {/* 上下文解释 */}
                {rule.context_explanation && (
                  <div style={{ fontSize: '14px', color: '#6b7280' }}>
                    <span style={{ fontWeight: '500' }}>上下文解释:</span>
                    <div style={{ 
                      marginTop: '4px', 
                      paddingLeft: '8px', 
                      borderLeft: '2px solid #dcfce7',
                      padding: '4px 0 4px 8px'
                    }}>
                      {rule.context_explanation}
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

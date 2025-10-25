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
 */
export default function GrammarNotationCard({ 
  isVisible = false, 
  textId = null,
  sentenceId = null,
  position = { top: 0, left: 0, right: 'auto' },
  onClose = null,
  onMouseEnter = null,
  onMouseLeave = null
}) {
  const [grammarRules, setGrammarRules] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (isVisible && textId && sentenceId) {
      setIsLoading(true)
      setError(null)
      
      // 获取句子的所有语法规则
      fetchSentenceGrammarRules(textId, sentenceId)
        .then(rules => {
          setGrammarRules(rules)
          setIsLoading(false)
        })
        .catch(error => {
          console.error('Error fetching sentence grammar rules:', error)
          setError(error.message || 'Failed to load grammar rules')
          setIsLoading(false)
        })
    } else {
      setGrammarRules([])
      setError(null)
    }
  }, [isVisible, textId, sentenceId])

  // 获取句子的语法规则
  const fetchSentenceGrammarRules = async (textId, sentenceId) => {
    try {
      // 使用新的API方法直接获取句子的语法规则
      const response = await apiService.getSentenceGrammarRules(textId, sentenceId)
      
      console.log(`🔍 [GrammarNotationCard] API response for sentence ${sentenceId}:`, response)
      
      if (response && response.data) {
        // 如果返回的是语法规则列表
        if (Array.isArray(response.data)) {
          console.log(`✅ [GrammarNotationCard] Found ${response.data.length} grammar rules`)
          return response.data
        }
        
        // 如果返回的是包含语法规则的对象
        if (response.data.grammar_rules) {
          console.log(`✅ [GrammarNotationCard] Found grammar_rules array with ${response.data.grammar_rules.length} items`)
          return response.data.grammar_rules
        }
        
        // 如果返回的是单个语法规则
        if (response.data.rule_id) {
          console.log(`✅ [GrammarNotationCard] Found single grammar rule`)
          return [response.data]
        }
      }
      
      console.log(`⚠️ [GrammarNotationCard] No grammar rules found in response`)
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

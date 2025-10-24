import { useState, useEffect } from 'react'
import { apiService } from '../../../services/api'

/**
 * GrammarNotation - 显示语法注释的下划线组件
 * 
 * Props:
 * - isVisible: 是否显示
 * - textId: 文章ID
 * - sentenceId: 句子ID
 * - grammarId: 语法规则ID
 * - markedTokenIds: 标记的token ID列表
 * - onMouseEnter: 鼠标进入的回调
 * - onMouseLeave: 鼠标离开的回调
 */
export default function GrammarNotation({ 
  isVisible = false, 
  textId = null,
  sentenceId = null,
  grammarId = null,
  markedTokenIds = [],
  onMouseEnter = null,
  onMouseLeave = null
}) {
  const [grammarRule, setGrammarRule] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (isVisible && grammarId) {
      setIsLoading(true)
      setError(null)
      
      // 获取语法规则信息
      apiService.getGrammarById(grammarId)
        .then(response => {
          if (response && response.data) {
            setGrammarRule(response.data)
          } else {
            setGrammarRule(null)
          }
          setIsLoading(false)
        })
        .catch(error => {
          console.error('Error fetching grammar rule:', error)
          setError(error.message || 'Failed to load grammar rule')
          setIsLoading(false)
        })
    } else {
      setGrammarRule(null)
      setError(null)
    }
  }, [isVisible, grammarId])

  if (!isVisible) return null

  return (
    <div 
      className="absolute left-0 right-0 h-0.5 bg-gray-400"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      title={grammarRule ? grammarRule.rule_summary : '语法注释'}
      style={{ 
        bottom: '-4px', // 确保在asked token绿色下划线之下
        zIndex: 1 // 确保在asked token下划线之上
      }}
    >
      {/* 可选的悬停提示 */}
      {grammarRule && (
        <div className="absolute bottom-full left-0 mb-1 opacity-0 hover:opacity-100 transition-opacity duration-200 pointer-events-none">
          <div className="bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
            {grammarRule.rule_name}: {grammarRule.rule_summary}
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import { apiService } from '../../../../services/api'

/**
 * VocabNotationCard - 显示词汇注释卡片（由原 TokenNotation 重命名）
 * 
 * Props:
 * - isVisible: 是否显示
 * - note: 备用文本
 * - position: 定位信息（可选）
 * - textId, sentenceId, tokenIndex: 定位到具体词汇示例
 * - onMouseEnter, onMouseLeave: 悬停回调
 * - getVocabExampleForToken: 从缓存/后端获取示例
 */
export default function VocabNotationCard({ 
  isVisible = false, 
  note = "This is a test note", 
  position = {},
  textId = null,
  sentenceId = null,
  tokenIndex = null,
  onMouseEnter = null,
  onMouseLeave = null,
  getVocabExampleForToken = null
}) {
  const [show, setShow] = useState(false)
  const [vocabExample, setVocabExample] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => setShow(true), 150)

      // 🔧 只在第一次显示且没有数据时才加载，避免重复请求
      if (!vocabExample && !isLoading && !error) {
        if (getVocabExampleForToken) {
          setIsLoading(true)
          setError(null)
          getVocabExampleForToken(textId, sentenceId, tokenIndex)
            .then(example => {
              setVocabExample(example || null)
              setIsLoading(false)
            })
            .catch(error => {
              console.error('❌ [VocabNotationCard] Error fetching vocab example:', error)
              setError(error.message || 'Failed to load vocab example')
              setVocabExample(null)
              setIsLoading(false)
            })
        } else if (textId && sentenceId && tokenIndex) {
          setIsLoading(true)
          setError(null)
          apiService.getVocabExampleByLocation(textId, sentenceId, tokenIndex)
            .then(response => {
              if (response && response.vocab_id) {
                setVocabExample(response)
              } else {
                setVocabExample(null)
              }
              setIsLoading(false)
            })
            .catch(error => {
              console.error('❌ [VocabNotationCard] Error fetching vocab example:', error)
              setError(error.message || 'Failed to load vocab example')
              setIsLoading(false)
            })
        }
      }

      return () => clearTimeout(timer)
    } else {
      setShow(false)
      // 不再清空 vocabExample，保留缓存
    }
  }, [isVisible, textId, sentenceId, tokenIndex, getVocabExampleForToken, vocabExample, isLoading, error])

  if (!show) return null

  let displayContent = note

  if (isLoading) {
    displayContent = (
      <div className="flex items-center gap-2">
        <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-gray-500">加载中...</span>
      </div>
    )
  } else if (error) {
    displayContent = (
      <div className="text-red-600">
        <div className="font-semibold">加载失败</div>
        <div className="text-xs mt-1">{error}</div>
      </div>
    )
  } else if (vocabExample && vocabExample.context_explanation) {
    displayContent = (
      <div>
        <div className="text-xs text-gray-500 mb-1">词汇解释</div>
        <div className="text-sm text-gray-800 leading-relaxed">
          {vocabExample.context_explanation}
        </div>
        {vocabExample.vocab_id && (
          <div className="text-xs text-gray-400 mt-2">Vocab ID: {vocabExample.vocab_id}</div>
        )}
      </div>
    )
  } else if (vocabExample === null && !isLoading) {
    displayContent = (
      <div className="text-gray-500 text-sm">暂无词汇解释</div>
    )
  }

  return (
    <div 
      className="absolute top-full left-0 z-50 transition-opacity duration-200 notation-card"
      style={{
        minWidth: '200px',
        maxWidth: '400px',
        opacity: show ? 1 : 0,
        marginTop: '-4px',
        paddingTop: '8px',
        ...position
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="absolute top-1 left-4 w-2 h-2 bg-gray-200 transform rotate-45 border-l border-t border-gray-300"></div>
      <div className="bg-gray-100 border border-gray-300 rounded-lg shadow-lg p-3">
        {displayContent}
      </div>
    </div>
  )
}



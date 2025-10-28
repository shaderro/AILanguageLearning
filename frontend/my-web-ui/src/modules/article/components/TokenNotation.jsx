import { useState, useEffect } from 'react'
import { apiService } from '../../../services/api'

/**
 * TokenNotation - 显示已提问token的注释卡片
 * 
 * Props:
 * - isVisible: 是否显示
 * - note: 注释内容（备用，如果 API 没有数据时显示）
 * - position: 定位信息（可选）
 * - onMouseEnter: 鼠标进入卡片的回调
 * - onMouseLeave: 鼠标离开卡片的回调
 * - getVocabExampleForToken: 获取vocab example的函数（可选）
 */
export default function TokenNotation({ 
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
      // 短暂延迟后显示，避免闪烁
      const timer = setTimeout(() => setShow(true), 150)
      
      // 优先使用缓存数据
      if (getVocabExampleForToken) {
        console.log('🔍 [TokenNotation] Using cached vocab example')
        setIsLoading(true)
        setError(null)
        
        getVocabExampleForToken(textId, sentenceId, tokenIndex)
          .then(example => {
            if (example) {
              console.log(`✅ [TokenNotation] Found cached vocab example:`, example)
              setVocabExample(example)
            } else {
              console.log(`❌ [TokenNotation] No cached vocab example found`)
              setVocabExample(null)
            }
            setIsLoading(false)
          })
          .catch(error => {
            console.error('❌ [TokenNotation] Error fetching vocab example:', error)
            setError(error.message || 'Failed to load vocab example')
            setVocabExample(null)
            setIsLoading(false)
          })
      } else if (textId && sentenceId && tokenIndex) {
        // 回退到API调用
        console.log(`🔍 [TokenNotation] Using API fallback for:`, {
          textId,
          sentenceId, 
          tokenIndex
        })
        
        setIsLoading(true)
        setError(null)
        
        apiService.getVocabExampleByLocation(textId, sentenceId, tokenIndex)
          .then(response => {
            console.log(`✅ [TokenNotation] Vocab example result:`, response)
            // response 已经通过拦截器处理，直接是 vocab example 对象（或 null）
            if (response && response.vocab_id) {
              console.log(`📝 [TokenNotation] Found vocab example:`, {
                vocab_id: response.vocab_id,
                text_id: response.text_id,
                sentence_id: response.sentence_id,
                context_explanation: response.context_explanation,
                token_indices: response.token_indices
              })
              setVocabExample(response)
            } else {
              console.log(`❌ [TokenNotation] No vocab example found for text_id=${textId}, sentence_id=${sentenceId}, token_index=${tokenIndex}`)
              setVocabExample(null)
            }
            setIsLoading(false)
          })
          .catch(error => {
            console.error(`❌ [TokenNotation] Error fetching vocab example:`, error)
            setError(error.message || 'Failed to load vocab example')
            setIsLoading(false)
          })
      }
      
      return () => clearTimeout(timer)
    } else {
      setShow(false)
      // 隐藏时清除数据，下次显示时重新加载
      setVocabExample(null)
      setError(null)
    }
  }, [isVisible, textId, sentenceId, tokenIndex, getVocabExampleForToken])

  if (!show) return null

  // 准备显示内容
  let displayContent = note  // 默认使用备用内容
  
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
    // 显示实际的 vocab example 解释
    displayContent = (
      <div>
        <div className="text-xs text-gray-500 mb-1">词汇解释</div>
        <div className="text-sm text-gray-800 leading-relaxed">
          {vocabExample.context_explanation}
        </div>
        {/* 可选：显示 vocab_id */}
        {vocabExample.vocab_id && (
          <div className="text-xs text-gray-400 mt-2">
            Vocab ID: {vocabExample.vocab_id}
          </div>
        )}
      </div>
    )
  } else if (vocabExample === null && !isLoading) {
    // API 返回但没有找到数据
    displayContent = (
      <div className="text-gray-500 text-sm">
        暂无词汇解释
      </div>
    )
  }

  return (
    <div 
      className="absolute top-full left-0 z-50 transition-opacity duration-200"
      style={{
        minWidth: '200px',
        maxWidth: '400px',  // 增加最大宽度以容纳更长的解释
        opacity: show ? 1 : 0,
        // 添加负 margin-top 来扩大可交互区域，覆盖 token 和卡片之间的空隙
        marginTop: '-4px',
        paddingTop: '8px',
        ...position
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* 小箭头 */}
      <div className="absolute top-1 left-4 w-2 h-2 bg-gray-200 transform rotate-45 border-l border-t border-gray-300"></div>
      
      {/* 卡片主体 - 浅灰底、深灰色文字 */}
      <div className="bg-gray-100 border border-gray-300 rounded-lg shadow-lg p-3">
        {displayContent}
      </div>
    </div>
  )
}

